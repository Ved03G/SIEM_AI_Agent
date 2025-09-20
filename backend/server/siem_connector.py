# server/siem_connector.py
"""
SIEM Connector module for handling connections to OpenSearch instances
and mock data. This module provides a unified interface for querying
security event data regardless of the data source.
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from opensearchpy import OpenSearch, ConnectionError, NotFoundError
from models import LogResult, QueryStats, SeverityLevel
from config import Settings
from urllib.parse import urlparse

# Load configuration
settings = Settings()


class SIEMConnector:
    """
    Handles connections to OpenSearch SIEM instances with fallback to mock data.
    Provides a unified interface for querying security events.
    """
    
    def __init__(self, use_mock_data: bool = False):
        self.use_mock_data = use_mock_data
        self.es_client = None
        self.mock_data = []
        self.connection_status = "disconnected"
        
        # Load mock data
        self._load_mock_data()
        
    # Try to connect to OpenSearch if not using mock data
        if not use_mock_data:
            self._connect_to_opensearch()
    
    def _load_mock_data(self):
        """Load rich mock SIEM data from JSON file"""
        try:
            # Try rich mock data first
            rich_data_path = os.path.join(os.path.dirname(__file__), "mock_siem_data_rich.json")
            if os.path.exists(rich_data_path):
                with open(rich_data_path, 'r') as f:
                    self.mock_data = json.load(f)
                print(f"🎯 Loaded {len(self.mock_data)} rich demo events (7 days)")
                return
                
            # Fallback to original mock data
            mock_data_path = os.path.join(os.path.dirname(__file__), "mock_siem_data.json")
            with open(mock_data_path, 'r') as f:
                self.mock_data = json.load(f)
            print(f"📄 Loaded {len(self.mock_data)} basic mock security events")
            
        except FileNotFoundError:
            print("⚠️  No mock data files found, using empty dataset")
            self.mock_data = []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing mock data: {e}")
            self.mock_data = []
    
    def _connect_to_opensearch(self):
        """Attempt to connect to Wazuh OpenSearch server"""
        # Primary + backup hosts from configuration
        all_hosts = []
        try:
            # Prefer using helper if available
            all_hosts = settings.get_opensearch_hosts()
        except Exception:
            # Fallback to single host
            all_hosts = [settings.opensearch_host]

        # Ensure we have at least one host (prefer secure default)
        if not all_hosts:
            all_hosts = ["https://localhost:9200"]

        for host in all_hosts:
            try:
                print(f"🔌 Attempting to connect to Wazuh OpenSearch at {host}")
                
                # Configure OpenSearch client for Wazuh server (simpe-test pattern)
                es_config = {
                    "hosts": [host],
                    "verify_certs": settings.opensearch_verify_certs,
                    "ssl_show_warn": False,
                }
                
                # Add authentication from environment
                if settings.opensearch_username and settings.opensearch_password:
                    es_config["http_auth"] = (
                        settings.opensearch_username,
                        settings.opensearch_password
                    )
                    print(f"🔐 Using authentication: {settings.opensearch_username}")
                
                self.es_client = OpenSearch(**es_config)
                
                # Test the connection
                if self.es_client.ping():
                    self.connection_status = "connected"
                    print(f"✅ Successfully connected to Wazuh OpenSearch at {host}")
                    
                    # Get cluster info
                    cluster_info = self.es_client.info()
                    print(f"📊 OpenSearch version: {cluster_info.get('version', {}).get('number', 'unknown')}")
                    return
                    
            except ConnectionError as e:
                print(f"❌ Connection error for {host}: {type(e).__name__}: {str(e)}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error connecting to {host}: {type(e).__name__}: {str(e)}")
                continue
        
        # If no connection succeeded, fall back to mock data
        print("🔄 No OpenSearch connection available, falling back to mock data")
        self.use_mock_data = True
        self.connection_status = "mock_mode"
    
    # Removed legacy standalone query_siem function in favor of SIEMConnector.query

    
    def _query_opensearch(self, dsl_query: Dict[str, Any], start_time: float) -> Tuple[List[LogResult], QueryStats]:
        """Query real Wazuh OpenSearch instance"""
        try:
            # Use configured index patterns (defaults include common Wazuh patterns)
            wazuh_indices = settings.get_opensearch_index_patterns()
            
            print(f"🔍 Querying Wazuh indices: {wazuh_indices}")
            # Log the DSL (truncate if long)
            try:
                dsl_preview = json.dumps(dsl_query, indent=2)
            except Exception:
                dsl_preview = str(dsl_query)
            print("🧠 DSL body (truncated to 2,000 chars):\n" + dsl_preview[:2000])

            # Ensure track_total_hits for accurate counts
            effective_query = dict(dsl_query) if isinstance(dsl_query, dict) else {}
            if "track_total_hits" not in effective_query:
                effective_query["track_total_hits"] = True
            
            # Try each index pattern until we find data
            response = None
            indices_searched = []
            
            for index_pattern in wazuh_indices:
                try:
                    print(f"📊 Searching index pattern: {index_pattern}")
                    response = self.es_client.search(
                        index=index_pattern,
                        body=effective_query,
                        request_timeout=30
                    )
                    indices_searched.append(index_pattern)
                    
                    # Check if we got any hits
                    total_hits = response["hits"]["total"]
                    hit_count = total_hits["value"] if isinstance(total_hits, dict) else total_hits
                    took_ms = response.get("took")
                    print(f"   ↳ took={took_ms}ms hits={hit_count}")
                    
                    if hit_count > 0:
                        print(f"✅ Found {hit_count} results in {index_pattern}")
                        break
                    else:
                        print(f"📭 No results in {index_pattern}")
                        
                except NotFoundError:
                    continue
                except Exception as e:
                    print(f"⚠️  Error querying index {index_pattern}: {e}")
                    continue
            
            if not response:
                # If no indices found, fall back to mock data
                print("📄 No OpenSearch indices found, using mock data")
                return self._query_mock_data(dsl_query, start_time)
            
            # Process the response
            hits = response["hits"]["hits"]
            total_hits = response["hits"]["total"]
            
            # Handle different OpenSearch versions
            if isinstance(total_hits, dict):
                total_count = total_hits.get("value", 0)
            else:
                total_count = total_hits
            
            # Convert hits to LogResult objects
            results = []
            for hit in hits:
                source = hit["_source"]
                # inject the _id so _convert_opensearch_hit_to_log_result can use it
                if "_id" in hit:
                    source = {**source, "_id": hit["_id"]}
                log_result = self._convert_opensearch_hit_to_log_result(source)
                results.append(log_result)
            
            # Create query stats
            query_time_ms = int((time.time() - start_time) * 1000)
            query_stats = QueryStats(
                total_hits=total_count,
                query_time_ms=query_time_ms,
                indices_searched=indices_searched,
                dsl_query=dsl_query
            )
            
            print(f"📊 OpenSearch query completed: {len(results)} results in {query_time_ms}ms")
            
            # If zero results overall, attempt a small debug sample to guide tuning
            if total_count == 0 and wazuh_indices:
                try:
                    sample_index = wazuh_indices[0]
                    print(f"🧪 Zero-hit sampler: fetching 1 doc from {sample_index} to inspect fields")
                    sample_resp = self.es_client.search(
                        index=sample_index,
                        body={
                            "size": 1,
                            "sort": [{"@timestamp": {"order": "desc"}}],
                            "query": {"match_all": {}}
                        },
                        request_timeout=15
                    )
                    sample_hits = sample_resp.get("hits", {}).get("hits", [])
                    if sample_hits:
                        sample_src = sample_hits[0].get("_source", {})
                        print("🧪 Sample fields:")
                        print("   rule.description:", sample_src.get("rule", {}).get("description"))
                        print("   message:", str(sample_src.get("message", ""))[:300])
                        print("   full_log:", str(sample_src.get("full_log", ""))[:300])
                    else:
                        print("🧪 No sample documents available in index pattern", sample_index)
                except Exception as de:
                    print("🧪 Sampler error:", de)

            # Log a curl to reproduce (without credentials)
            try:
                hosts = settings.get_opensearch_hosts()
                host = hosts[0] if hosts else "https://localhost:9200"
                curl_body = json.dumps(effective_query)
                curl_snip = (
                    f"curl -k -u <user>:<pass> -H 'Content-Type: application/json' "
                    f"-X POST '{host}/{wazuh_indices[0]}/_search?pretty' -d '{curl_body}'"
                )
                print("🧵 Repro curl (edit creds as needed):\n" + curl_snip[:2000])
            except Exception:
                pass

            return results, query_stats
            
        except ConnectionError as e:
            print(f"❌ OpenSearch connection error: {e}")
            return self._query_mock_data(dsl_query, start_time)
        except Exception as e:
            print(f"❌ Error querying OpenSearch: {e}")
            return self._query_mock_data(dsl_query, start_time)
    
    def query(self, dsl_query: Dict[str, Any]) -> Tuple[List[LogResult], QueryStats]:
        """Public method to execute a DSL query against OpenSearch or mock data"""
        start_time = time.time()
        if self.es_client and self.connection_status == "connected" and not self.use_mock_data:
            return self._query_opensearch(dsl_query, start_time)
        else:
            return self._query_mock_data(dsl_query, start_time)

    def _query_mock_data(self, dsl_query: Dict[str, Any], start_time: float) -> Tuple[List[LogResult], QueryStats]:
        """Query mock data using DSL-like filtering"""
        print("📄 Querying mock data...")
        
        # Ensure DSL is a dictionary
        if isinstance(dsl_query, str):
            try:
                dsl_query = json.loads(dsl_query)
            except Exception:
                dsl_query = {}
        elif not isinstance(dsl_query, dict):
            dsl_query = {}

        # Start with all mock data
        filtered_data = self.mock_data.copy()
        
        # Apply DSL query filters to mock data
        filtered_data = self._apply_mock_filters(filtered_data, dsl_query)
        
        # Apply sorting
        sort_config = dsl_query.get("sort", [{"timestamp": {"order": "desc"}}])
        if sort_config:
            sort_field = list(sort_config[0].keys())[0]
            sort_order = sort_config[0][sort_field].get("order", "desc")
            reverse_sort = sort_order == "desc"
            
            if sort_field == "timestamp":
                filtered_data.sort(
                    key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")),
                    reverse=reverse_sort
                )
        
        # Apply size limit
        size = dsl_query.get("size", 20)
        results_data = filtered_data[:size]
        
        # Convert to LogResult objects
        results = []
        for item in results_data:
            log_result = self._convert_mock_data_to_log_result(item)
            results.append(log_result)
        
        # Create query stats
        query_time_ms = int((time.time() - start_time) * 1000)
        query_stats = QueryStats(
            total_hits=len(filtered_data),
            query_time_ms=query_time_ms,
            indices_searched=["mock-data"],
            dsl_query=dsl_query
        )
        
        print(f"📊 Mock query completed: {len(results)} results in {query_time_ms}ms")
        return results, query_stats
    
    def _apply_mock_filters(self, data: List[Dict], dsl_query: Dict[str, Any]) -> List[Dict]:
        """Apply DSL query filters to mock data"""
        filtered_data = data
        
        query = dsl_query.get("query", {})
        bool_query = query.get("bool", {})
        
        # Apply must conditions (AND)
        must_conditions = bool_query.get("must", [])
        for condition in must_conditions:
            filtered_data = self._apply_condition(filtered_data, condition)
        
        # Apply should conditions (OR)
        should_conditions = bool_query.get("should", [])
        if should_conditions:
            should_results = []
            for condition in should_conditions:
                condition_results = self._apply_condition(data, condition)
                should_results.extend(condition_results)
            # Remove duplicates while preserving order
            seen = set()
            filtered_data = [x for x in should_results if x["event_id"] not in seen and not seen.add(x["event_id"])]
        
        # Apply filter conditions
        filter_conditions = bool_query.get("filter", [])
        for condition in filter_conditions:
            filtered_data = self._apply_condition(filtered_data, condition)
        
        return filtered_data
    
    def _apply_condition(self, data: List[Dict], condition: Dict[str, Any]) -> List[Dict]:
        """Apply a single DSL condition to the data"""
        if "match_all" in condition:
            return data
        
        elif "term" in condition:
            field, value = next(iter(condition["term"].items()))
            return [item for item in data if self._get_nested_value(item, field) == value]
        
        elif "terms" in condition:
            field, values = next(iter(condition["terms"].items()))
            return [item for item in data if self._get_nested_value(item, field) in values]
        
        elif "match" in condition:
            field, value = next(iter(condition["match"].items()))
            return [item for item in data if value.lower() in str(self._get_nested_value(item, field)).lower()]
        
        elif "range" in condition:
            field, range_config = next(iter(condition["range"].items()))
            filtered = []
            for item in data:
                item_value = self._get_nested_value(item, field)
                if self._value_in_range(item_value, range_config):
                    filtered.append(item)
            return filtered
        
        else:
            # Unknown condition type, return original data
            return data
    
    def _get_nested_value(self, item: Dict, field_path: str) -> Any:
        """Get a nested value from a dictionary using dot notation"""
        try:
            value = item
            for key in field_path.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and key.isdigit():
                    value = value[int(key)]
                else:
                    return None
            return value
        except (KeyError, IndexError, TypeError):
            return None
    
    def _value_in_range(self, value: Any, range_config: Dict[str, Any]) -> bool:
        """Check if a value falls within a specified range"""
        try:
            if "gte" in range_config and value < range_config["gte"]:
                return False
            if "gt" in range_config and value <= range_config["gt"]:
                return False
            if "lte" in range_config and value > range_config["lte"]:
                return False
            if "lt" in range_config and value >= range_config["lt"]:
                return False
            return True
        except (TypeError, ValueError):
            return False
    
    def _convert_opensearch_hit_to_log_result(self, source: Dict[str, Any]) -> LogResult:
        """Convert OpenSearch hit to LogResult model"""
        # Extract common fields from Wazuh/Elastic SIEM format
        rule_info = source.get("rule", {})
        data_info = source.get("data", {})
        agent_info = source.get("agent", {})
        
        return LogResult(
            timestamp=source.get("timestamp", source.get("@timestamp", "N/A")),
            event_id=source.get("_id", source.get("id", f"evt_{int(time.time())}")),
            source_ip=data_info.get("srcip", data_info.get("src_ip")),
            destination_ip=data_info.get("dstip", data_info.get("dst_ip")),
            user=data_info.get("user", data_info.get("username")),
            rule_id=str(rule_info.get("id", "")),
            rule_description=rule_info.get("description", "No description available"),
            severity=self._map_level_to_severity(rule_info.get("level", 0)),
            source_system=agent_info.get("name", "unknown"),
            raw_data=source,
            details=self._format_event_details(source)
        )
    
    def _convert_mock_data_to_log_result(self, item: Dict[str, Any]) -> LogResult:
        """Convert mock data item to LogResult model"""
        rule_info = item.get("rule", {})
        data_info = item.get("data", {})
        agent_info = item.get("agent", {})
        
        return LogResult(
            timestamp=item.get("timestamp", "N/A"),
            event_id=item.get("event_id", f"mock_{int(time.time())}"),
            source_ip=data_info.get("srcip"),
            destination_ip=data_info.get("dstip"),
            user=data_info.get("user"),
            rule_id=str(rule_info.get("id", "")),
            rule_description=rule_info.get("description", "No description available"),
            severity=self._map_level_to_severity(rule_info.get("level", 0)),
            source_system=agent_info.get("name", "mock-agent"),
            raw_data=item,
            details=self._format_event_details(item)
        )
    
    def _map_level_to_severity(self, level: int) -> Optional[SeverityLevel]:
        """Map numeric level to severity enum"""
        if level >= 10:
            return SeverityLevel.CRITICAL
        elif level >= 8:
            return SeverityLevel.HIGH
        elif level >= 5:
            return SeverityLevel.MEDIUM
        elif level > 0:
            return SeverityLevel.LOW
        else:
            return None
    
    def _format_event_details(self, event: Dict[str, Any]) -> str:
        """Format event details for display"""
        rule_info = event.get("rule", {})
        data_info = event.get("data", {})
        
        details = rule_info.get("description", "Security event detected")
        
        # Add relevant context
        if data_info.get("srcip"):
            details += f" | Source IP: {data_info['srcip']}"
        if data_info.get("user"):
            details += f" | User: {data_info['user']}"
        if data_info.get("protocol"):
            details += f" | Protocol: {data_info['protocol']}"
        
        return details
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and health information"""
        status_info = {
            "status": self.connection_status,
            "using_mock_data": self.use_mock_data,
            "mock_data_count": len(self.mock_data) if self.use_mock_data else 0
        }
        
        if self.es_client and not self.use_mock_data:
            try:
                cluster_health = self.es_client.cluster.health()
                status_info.update({
                    "opensearch_cluster_status": cluster_health.get("status", "unknown"),
                    "opensearch_nodes": cluster_health.get("number_of_nodes", 0),
                    "opensearch_indices": cluster_health.get("active_primary_shards", 0)
                })
            except Exception as e:
                status_info["opensearch_error"] = str(e)
        
        return status_info


# Global SIEM connector instance
# Initialize with mock data by default (will attempt OpenSearch connection)
siem_connector = SIEMConnector(use_mock_data=False)


def query_siem(dsl_query: Dict[str, Any]) -> Tuple[List[LogResult], QueryStats]:
    """
    Main entry point for SIEM queries.
    This function provides the interface that the main application uses.
    """
    return siem_connector.query(dsl_query)


def get_siem_status() -> Dict[str, Any]:
    """Get SIEM connection status"""
    return siem_connector.get_connection_status()


def force_mock_mode(enable: bool = True):
    """Force the connector to use mock data (useful for testing)"""
    global siem_connector
    siem_connector.use_mock_data = enable
    if enable:
        siem_connector.connection_status = "mock_mode"
        print("🔄 Forced mock mode enabled")
    else:
        siem_connector._connect_to_opensearch()
        print("🔌 Attempting to reconnect to OpenSearch")