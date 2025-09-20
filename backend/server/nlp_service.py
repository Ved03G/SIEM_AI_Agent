# server/nlp_service_simple.py
"""
Hackathon-focused NLP service using Gemini AI for maximum demo impact.
Simplified for speed and visual results.
"""

import json
from typing import Dict, Any, List, Optional
from models import QueryType
from nlp_brain import generate_dsl_query as gemini_generate_dsl


def generate_dsl_query(question: str, context: Optional[List[str]] = None, 
                      query_type: QueryType = QueryType.INVESTIGATION) -> Dict[str, Any]:
    """
    Generate Elasticsearch DSL query from natural language using Gemini AI.
    Simplified for hackathon demo with fallback safety.
    """
    print(f"🧠 Gemini AI processing: '{question}'")
    
    try:
        # Use your Gemini-powered NLP brain
        dsl_query = gemini_generate_dsl(question)
        
        if dsl_query and isinstance(dsl_query, dict):
            print(f"✅ Gemini success!")
            
            # Ensure required fields for demo
            if "size" not in dsl_query:
                dsl_query["size"] = 25  # Good demo size
            
            if "sort" not in dsl_query:
                dsl_query["sort"] = [{"@timestamp": {"order": "desc"}}]
            
            return dsl_query
            
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
    
    # Demo-friendly fallback
    return create_demo_fallback_query(question)


def create_demo_fallback_query(question: str) -> Dict[str, Any]:
    """Create visually appealing fallback for demo"""
    # Simple keyword matching for common security terms
    security_keywords = {
        "failed": {"term": {"rule.description": "failure"}},
        "login": {"term": {"rule.groups": "authentication"}},
        "attack": {"range": {"rule.level": {"gte": 8}}},
        "suspicious": {"range": {"rule.level": {"gte": 6}}},
        "malware": {"term": {"rule.groups": "malware"}},
        "critical": {"range": {"rule.level": {"gte": 10}}}
    }
    
    must_clauses = []
    for keyword, clause in security_keywords.items():
        if keyword.lower() in question.lower():
            must_clauses.append(clause)
    
    if not must_clauses:
        must_clauses = [{"match_all": {}}]
    
    return {
        "size": 25,
        "query": {"bool": {"must": must_clauses}},
        "sort": [{"@timestamp": {"order": "desc"}}]
    }


def generate_suggestions(question: str, results: List[Dict]) -> List[str]:
    """Generate demo-worthy follow-up suggestions"""
    suggestions = [
        "Show me the top attacking IPs",
        "Create a security report for the last 24 hours", 
        "Display failed login attempts by country",
        "Find all high severity alerts this week",
        "Show malware detection trends"
    ]
    
    # Contextual suggestions based on question
    if "failed" in question.lower():
        suggestions.insert(0, "Show geographic distribution of failed logins")
    elif "ip" in question.lower():
        suggestions.insert(0, "Analyze all activity from this IP range")
    elif "attack" in question.lower():
        suggestions.insert(0, "Generate attack timeline visualization")
    
    return suggestions[:4]  # Keep it concise for demo


def analyze_query_intent(question: str) -> Dict[str, Any]:
    """Analyze query for demo insights"""
    intent = {
        "type": QueryType.INVESTIGATION,
        "confidence": 0.8,
        "entities": [],
        "time_scope": "recent"
    }
    
    # Simple entity extraction for demo
    if "ip" in question.lower():
        intent["entities"].append("ip_address")
    if "user" in question.lower():
        intent["entities"].append("username")
    if "hour" in question.lower() or "day" in question.lower():
        intent["time_scope"] = "specific"
    
    return intent