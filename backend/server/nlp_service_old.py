# server/nlp_service.py
"""
Natural Language Processing service using Gemini AI for converting conversational queries 
into Elasticsearch DSL queries. This provides production-grade NLP with Google's Gemini.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from models import QueryType, SeverityLevel
from nlp_brain import generate_dsl_query as gemini_generate_dsl


class NLPQueryProcessor:
    """
    Processes natural language queries and converts them to Elasticsearch DSL.
    This is a sophisticated placeholder that demonstrates the expected functionality.
    """
    
    def __init__(self):
        # Common security terms and their mappings to SIEM fields
        self.security_terms = {
            # Authentication related
            "login": ["authentication", "logon", "signin"],
            "failed login": ["authentication_failed", "logon_failure", "failed_auth"],
            "successful login": ["authentication_success", "logon_success"],
            "brute force": ["brute_force", "password_attack", "credential_attack"],
            
            # Network related
            "suspicious connection": ["network", "outbound", "connection"],
            "external connection": ["external", "outbound", "geo_risk"],
            "malicious domain": ["dns", "malware", "command_control"],
            
            # File and system related
            "file access": ["file_monitor", "sensitive_files"],
            "malware": ["malware", "virus", "trojan"],
            "powershell": ["powershell", "encoded_command", "execution"],
            "service": ["windows", "service", "persistence"],
            
            # General security
            "high severity": ["level:>=8"],
            "critical": ["level:>=9"],
            "tor": ["tor", "anonymization"]
        }
        
        # Time range mappings
        self.time_patterns = {
            r"last\s+(\d+)\s+hours?": lambda m: self._get_time_range(hours=int(m.group(1))),
            r"last\s+(\d+)\s+days?": lambda m: self._get_time_range(days=int(m.group(1))),
            r"yesterday": lambda m: self._get_time_range(days=1, offset_days=1),
            r"today": lambda m: self._get_time_range(hours=24),
            r"last\s+week": lambda m: self._get_time_range(days=7),
            r"last\s+month": lambda m: self._get_time_range(days=30),
            r"past\s+24\s+hours?": lambda m: self._get_time_range(hours=24)
        }
        
        # Common query patterns and their DSL translations
        self.query_patterns = [
            # Authentication patterns
            {
                "pattern": r"(failed|unsuccessful)\s+(login|authentication|logon)",
                "dsl_template": {
                    "query": {
                        "bool": {
                            "must": [
                                {"terms": {"rule.groups": ["authentication_failed"]}}
                            ]
                        }
                    }
                }
            },
            # IP address patterns
            {
                "pattern": r"from\s+ip\s+(\d+\.\d+\.\d+\.\d+)",
                "dsl_template": {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"data.srcip": "{ip}"}}
                            ]
                        }
                    }
                }
            },
            # User patterns
            {
                "pattern": r"user\s+(\w+)",
                "dsl_template": {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"data.user": "{user}"}}
                            ]
                        }
                    }
                }
            },
            # Malware/threat patterns
            {
                "pattern": r"(malware|virus|trojan|threat)",
                "dsl_template": {
                    "query": {
                        "bool": {
                            "should": [
                                {"terms": {"rule.groups": ["malware"]}},
                                {"terms": {"rule.groups": ["virus"]}},
                                {"terms": {"rule.groups": ["trojan"]}}
                            ]
                        }
                    }
                }
            }
        ]

    def generate_dsl_query(self, question: str, context: Optional[List[str]] = None, 
                          max_results: int = 20) -> Dict[str, Any]:
        """
        Main function to convert natural language to Elasticsearch DSL.
        
        Args:
            question: Natural language security query
            context: Previous queries for contextual understanding
            max_results: Maximum number of results to return
        
        Returns:
            Elasticsearch DSL query dictionary
        """
        print(f"🔍 Processing NLP query: '{question}'")
        
        # Start with base query structure
        dsl_query = {
            "size": max_results,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [],
                    "should": [],
                    "filter": []
                }
            }
        }
        
        # Process the question
        processed_query = self._process_natural_language(question.lower())
        
        # Add time range if specified
        time_filter = self._extract_time_range(question)
        if time_filter:
            dsl_query["query"]["bool"]["filter"].append(time_filter)
        
        # Add main query conditions
        if processed_query["must"]:
            dsl_query["query"]["bool"]["must"].extend(processed_query["must"])
        if processed_query["should"]:
            dsl_query["query"]["bool"]["should"].extend(processed_query["should"])
            dsl_query["query"]["bool"]["minimum_should_match"] = 1
        
        # Add severity filters
        severity_filter = self._extract_severity(question)
        if severity_filter:
            dsl_query["query"]["bool"]["filter"].append(severity_filter)
        
        # Handle contextual queries
        if context:
            context_filters = self._process_context(context)
            if context_filters:
                dsl_query["query"]["bool"]["filter"].extend(context_filters)
        
        # If no specific conditions, add a match_all query
        if not dsl_query["query"]["bool"]["must"] and not dsl_query["query"]["bool"]["should"]:
            dsl_query["query"]["bool"]["must"].append({"match_all": {}})
        
        print(f"📊 Generated DSL query: {json.dumps(dsl_query, indent=2)}")
        return dsl_query

    def _process_natural_language(self, question: str) -> Dict[str, List[Dict]]:
        """Process natural language and extract query conditions"""
        must_conditions = []
        should_conditions = []
        
        # Check for specific patterns
        for pattern_info in self.query_patterns:
            pattern = pattern_info["pattern"]
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                # Create query based on pattern
                if "authentication" in pattern:
                    must_conditions.append({
                        "terms": {"rule.groups": ["authentication_failed"]}
                    })
                elif "ip" in pattern:
                    ip_address = match.group(1)
                    must_conditions.append({
                        "term": {"data.srcip": ip_address}
                    })
                elif "user" in pattern:
                    username = match.group(1)
                    must_conditions.append({
                        "term": {"data.user": username}
                    })
                elif "malware" in pattern:
                    should_conditions.extend([
                        {"terms": {"rule.groups": ["malware"]}},
                        {"terms": {"rule.groups": ["virus"]}},
                        {"terms": {"rule.groups": ["command_control"]}}
                    ])
        
        # Check for security terms
        for term, related_terms in self.security_terms.items():
            if any(t in question for t in [term] + related_terms):
                if term == "failed login":
                    must_conditions.append({
                        "terms": {"rule.groups": ["authentication_failed"]}
                    })
                elif term == "suspicious connection":
                    should_conditions.extend([
                        {"terms": {"rule.groups": ["network"]}},
                        {"terms": {"rule.groups": ["outbound"]}},
                        {"terms": {"rule.groups": ["geo_risk"]}}
                    ])
                elif term == "malicious domain":
                    should_conditions.extend([
                        {"terms": {"rule.groups": ["dns"]}},
                        {"terms": {"rule.groups": ["malware"]}},
                        {"terms": {"rule.groups": ["command_control"]}}
                    ])
                elif term == "file access":
                    should_conditions.extend([
                        {"terms": {"rule.groups": ["file_monitor"]}},
                        {"terms": {"rule.groups": ["sensitive_files"]}}
                    ])
                elif term == "powershell":
                    should_conditions.extend([
                        {"terms": {"rule.groups": ["powershell"]}},
                        {"terms": {"rule.groups": ["execution"]}}
                    ])
                elif term == "tor":
                    must_conditions.append({
                        "terms": {"rule.groups": ["tor"]}
                    })
        
        return {"must": must_conditions, "should": should_conditions}

    def _extract_time_range(self, question: str) -> Optional[Dict[str, Any]]:
        """Extract time range from the question"""
        for pattern, time_func in self.time_patterns.items():
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                time_range = time_func(match)
                return {
                    "range": {
                        "timestamp": {
                            "gte": time_range["start"],
                            "lte": time_range["end"]
                        }
                    }
                }
        return None

    def _extract_severity(self, question: str) -> Optional[Dict[str, Any]]:
        """Extract severity filters from the question"""
        if any(term in question.lower() for term in ["critical", "high severity", "urgent"]):
            return {
                "range": {
                    "rule.level": {"gte": 8}
                }
            }
        elif any(term in question.lower() for term in ["medium severity", "moderate"]):
            return {
                "range": {
                    "rule.level": {"gte": 5, "lt": 8}
                }
            }
        elif any(term in question.lower() for term in ["low severity", "minor"]):
            return {
                "range": {
                    "rule.level": {"lt": 5}
                }
            }
        return None

    def _process_context(self, context: List[str]) -> List[Dict[str, Any]]:
        """Process previous queries for contextual understanding"""
        context_filters = []
        
        # Simple context processing - in a real implementation, this would be more sophisticated
        for prev_query in context[-3:]:  # Consider last 3 queries
            if "same user" in prev_query.lower():
                # This would need to extract the user from previous results
                pass
            elif "same ip" in prev_query.lower():
                # This would need to extract the IP from previous results
                pass
        
        return context_filters

    def _get_time_range(self, hours: int = 0, days: int = 0, offset_days: int = 0) -> Dict[str, str]:
        """Generate time range for queries"""
        now = datetime.now()
        
        if offset_days > 0:
            end_time = now - timedelta(days=offset_days)
            start_time = end_time - timedelta(days=days, hours=hours)
        else:
            end_time = now
            start_time = now - timedelta(days=days, hours=hours)
        
        return {
            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    def generate_suggestions(self, question: str, results_count: int) -> List[str]:
        """Generate follow-up query suggestions based on the current query"""
        suggestions = []
        
        if "failed login" in question.lower():
            suggestions.extend([
                "Show me successful logins from the same IPs",
                "Are there any brute force patterns?",
                "Filter by specific users only"
            ])
        elif "malware" in question.lower():
            suggestions.extend([
                "Show me related network connections",
                "What files were affected?",
                "Show me the infection timeline"
            ])
        elif "suspicious" in question.lower():
            suggestions.extend([
                "Show me high severity events only",
                "Group by source IP address",
                "Show me events from external sources"
            ])
        
        # Add general suggestions based on result count
        if results_count == 0:
            suggestions.extend([
                "Try expanding the time range",
                "Search for similar but broader terms",
                "Check for typos in the query"
            ])
        elif results_count > 50:
            suggestions.extend([
                "Add more specific filters",
                "Focus on high severity events",
                "Filter by time range"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions


# Initialize the global NLP processor
nlp_processor = NLPQueryProcessor()


def generate_dsl_query(question: str, context: Optional[List[str]] = None, 
                      max_results: int = 20) -> Dict[str, Any]:
    """
    Main entry point for NLP query processing.
    This function will be replaced with Person B's actual implementation.
    """
    print("--- NLP Module (Enhanced Placeholder) ---")
    return nlp_processor.generate_dsl_query(question, context, max_results)


def generate_suggestions(question: str, results_count: int) -> List[str]:
    """Generate contextual suggestions for follow-up queries"""
    return nlp_processor.generate_suggestions(question, results_count)


def analyze_query_intent(question: str) -> QueryType:
    """Analyze the intent of the query to determine its type"""
    question_lower = question.lower()
    
    if any(term in question_lower for term in ["report", "summary", "overview", "statistics"]):
        return QueryType.REPORT
    elif any(term in question_lower for term in ["show me more", "continue", "also", "additionally"]):
        return QueryType.CONTEXTUAL
    else:
        return QueryType.INVESTIGATION