# server/siem_connector.py
"""
SIEM Connector module for handling connections to Elasticsearch instances
and mock data. This module provides a unified interface for querying
security event data regardless of the data source.
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from elasticsearch import Elasticsearch, ConnectionError, NotFoundError
from models import LogResult, QueryStats, SeverityLevel
from config import Settings

# Load configuration
settings = Settings()


class SIEMConnector:
    """
    Handles connections to Elasticsearch SIEM instances with fallback to mock data.
    Provides a unified interface for querying security events.
    """
    
    def __init__(self, use_mock_data: bool = False):
        self.use_mock_data = use_mock_data
        self.es_client = None
        self.mock_data = []
        self.connection_status = "disconnected"
        
        # Load mock data
        self._load_mock_data()
        
        # Try to connect to Elasticsearch if not using mock data
        if not use_mock_data:
            self._connect_to_elasticsearch()
    
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
    
    def _connect_to_elasticsearch(self):
        """Attempt to connect to Wazuh Elasticsearch server"""
        # Primary Wazuh server from environment
        primary_host = settings.elasticsearch_host
        
        # Backup hosts for fallback
        wazuh_es_hosts = [
            primary_host,                      # Configured Wazuh server
            "https://169.254.97.100:9200",     # Direct HTTPS
            "http://169.254.97.100:9200",      # Direct HTTP
            "https://169.254.97.100:9443",     # Alternative port
            "http://localhost:9200",           # Local fallback
        ]
        
        for host in wazuh_es_hosts:
            try:
                print(f"🔌 Attempting to connect to Wazuh Elasticsearch at {host}")
                
                # Configure Elasticsearch client for Wazuh server
                es_config = {
                    "hosts": [host],
                    "request_timeout": settings.elasticsearch_timeout,
                    "max_retries": settings.elasticsearch_max_retries,
                    "retry_on_timeout": True,
                    "verify_certs": settings.elasticsearch_verify_certs,
                }
                
                # Add authentication from environment
                if settings.elasticsearch_username and settings.elasticsearch_password:
                    es_config["basic_auth"] = (
                        settings.elasticsearch_username, 
                        settings.elasticsearch_password
                    )
                    print(f"🔐 Using authentication: {settings.elasticsearch_username}")
                
                self.es_client = Elasticsearch(**es_config)
                
                # Test the connection
                if self.es_client.ping():
                    self.connection_status = "connected"
                    print(f"✅ Successfully connected to Wazuh Elasticsearch at {host}")
                    
                    # Get cluster info
                    cluster_info = self.es_client.info()
                    print(f"📊 Elasticsearch version: {cluster_info.get('version', {}).get('number', 'unknown')}")
                    return
                    
            except ConnectionError as e:
                print(f"❌ Connection error for {host}: {type(e).__name__}: {str(e)}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error connecting to {host}: {type(e).__name__}: {str(e)}")
                continue
        
        # If no connection succeeded, fall back to mock data
        print("🔄 No Elasticsearch connection available, falling back to mock data")
        self.use_mock_data = True
        self.connection_status = "mock_mode"
    
    def query_siem(self, dsl_query: Dict[str, Any]) -> Tuple[List[LogResult], QueryStats]:
        """
        Execute a query against the SIEM and return formatted results.
        
        Args:
            dsl_query: Elasticsearch DSL query dictionary
            
        Returns:
            Tuple of (results, query_stats)
        """
        start_time = time.time()
        
        if self.use_mock_data or not self.es_client:
            return self._query_mock_data(dsl_query, start_time)
        else:
            return self._query_elasticsearch(dsl_query, start_time)
    
    def _query_elasticsearch(self, dsl_query: Dict[str, Any], start_time: float) -> Tuple[List[LogResult], QueryStats]:
        """Query real Wazuh Elasticsearch instance"""
        try:
            # Wazuh specific indices patterns
            wazuh_indices = [
                "wazuh-alerts-4.x-*",    # Current Wazuh 4.x alerts
                "wazuh-alerts-*",        # General Wazuh alerts
                "wazuh-archives-*",      # Wazuh archives
                "filebeat-*",            # Filebeat indices
                ".wazuh-*",              # Wazuh internal indices
                "logstash-*"             # Logstash indices if used
            ]
            
            print(f"🔍 Querying Wazuh indices: {wazuh_indices}")
            
            # Try each index pattern until we find data
            response = None
            indices_searched = []
            
            for index_pattern in wazuh_indices:
                try:
                    print(f"📊 Searching index pattern: {index_pattern}")
                    response = self.es_client.search(
                        index=index_pattern,
                        **dsl_query,
                        timeout="30s"
                    )
                    indices_searched.append(index_pattern)
                    
                    # Check if we got any hits
                    total_hits = response["hits"]["total"]
                    hit_count = total_hits["value"] if isinstance(total_hits, dict) else total_hits
                    
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
                print("📄 No Elasticsearch indices found, using mock data")
                return self._query_mock_data(dsl_query, start_time)
            
            # Process the response
            hits = response["hits"]["hits"]
            total_hits = response["hits"]["total"]
            
            # Handle different Elasticsearch versions
            if isinstance(total_hits, dict):
                total_count = total_hits.get("value", 0)
            else:
                total_count = total_hits
            
            # Convert hits to LogResult objects
            results = []
            for hit in hits:
                source = hit["_source"]
                log_result = self._convert_elasticsearch_hit_to_log_result(source)
                results.append(log_result)
            
            # Create query stats
            query_time_ms = int((time.time() - start_time) * 1000)
            query_stats = QueryStats(
                total_hits=total_count,
                query_time_ms=query_time_ms,
                indices_searched=indices_searched,
                dsl_query=dsl_query
            )
            
            print(f"📊 Elasticsearch query completed: {len(results)} results in {query_time_ms}ms")
            return results, query_stats
            
        except ConnectionError as e:
            print(f"❌ Elasticsearch connection error: {e}")
            return self._query_mock_data(dsl_query, start_time)
        except Exception as e:
            print(f"❌ Error querying Elasticsearch: {e}")
            return self._query_mock_data(dsl_query, start_time)
    
    def _query_mock_data(self, dsl_query: Dict[str, Any], start_time: float) -> Tuple[List[LogResult], QueryStats]:
        """Query mock data using DSL-like filtering"""
        print("📄 Querying mock data...")
        
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
    
    def _convert_elasticsearch_hit_to_log_result(self, source: Dict[str, Any]) -> LogResult:
        """Convert Elasticsearch hit to LogResult model"""
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
                    "elasticsearch_cluster_status": cluster_health.get("status", "unknown"),
                    "elasticsearch_nodes": cluster_health.get("number_of_nodes", 0),
                    "elasticsearch_indices": cluster_health.get("active_primary_shards", 0)
                })
            except Exception as e:
                status_info["elasticsearch_error"] = str(e)
        
        return status_info


# Global SIEM connector instance
# Initialize with mock data by default (will attempt Elasticsearch connection)
siem_connector = SIEMConnector(use_mock_data=False)


def query_siem(dsl_query: Dict[str, Any]) -> Tuple[List[LogResult], QueryStats]:
    """
    Main entry point for SIEM queries.
    This function provides the interface that the main application uses.
    """
    return siem_connector.query_siem(dsl_query)


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
        siem_connector._connect_to_elasticsearch()
        print("🔌 Attempting to reconnect to Elasticsearch")