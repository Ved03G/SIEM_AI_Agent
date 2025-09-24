# server/context_manager.py
"""
Context Manager for handling conversation state and multi-turn queries.
Tracks user sessions, query history, and maintains context for follow-up questions.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from threading import Lock
from models import ConversationContext, ContextEntry


class ContextManager:
    """
    Manages conversation context for multi-turn SIEM queries.
    Provides session management, context persistence, and smart context retrieval.
    """
    
    def __init__(self, max_sessions: int = 1000, session_timeout_hours: int = 24):
        self.sessions: Dict[str, ConversationContext] = {}
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self._lock = Lock()
        
        print(f"💭 Context Manager initialized (max_sessions: {max_sessions}, timeout: {session_timeout_hours}h)")
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation context for a session.
        Returns None if session doesn't exist or has expired.
        """
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            context = self.sessions[session_id]
            
            # Check if session has expired
            if datetime.now() - context.last_updated > self.session_timeout:
                print(f"🕒 Session {session_id[:8]}... expired, removing")
                del self.sessions[session_id]
                return None
            
            return context
    
    def add_to_context(self, session_id: str, query: str, dsl_query: Dict[str, Any], 
                      result_count: int, summary: str) -> ConversationContext:
        """
        Add a new query and its results to the conversation context.
        Creates a new session if it doesn't exist.
        """
        with self._lock:
            # Clean up expired sessions periodically
            self._cleanup_expired_sessions()
            
            # Get or create session context
            if session_id in self.sessions:
                context = self.sessions[session_id]
            else:
                context = ConversationContext(
                    session_id=session_id,
                    history=[],
                    active_filters={},
                    last_updated=datetime.now()
                )
                
                # Enforce max sessions limit
                if len(self.sessions) >= self.max_sessions:
                    self._remove_oldest_session()
            
            # Create new context entry
            entry = ContextEntry(
                timestamp=datetime.now(),
                query=query,
                dsl_query=dsl_query,
                result_count=result_count,
                summary=summary
            )
            
            # Add to history (keep last 10 queries per session)
            context.history.append(entry)
            if len(context.history) > 10:
                context.history = context.history[-10:]
            
            # Update active filters based on the query
            self._update_active_filters(context, dsl_query)
            
            # Update timestamp
            context.last_updated = datetime.now()
            
            # Store the updated context
            self.sessions[session_id] = context
            
            print(f"💾 Added query to context for session {session_id[:8]}... (history size: {len(context.history)})")
            return context
    
    def clear_context(self, session_id: str) -> bool:
        """
        Clear conversation context for a specific session.
        Returns True if session was found and cleared, False otherwise.
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"🗑️  Cleared context for session {session_id[:8]}...")
                return True
            return False
    
    def get_relevant_context(self, session_id: str, current_query: str) -> List[ContextEntry]:
        """
        Get relevant context entries for the current query.
        Returns context entries that might be relevant to the current question.
        """
        context = self.get_context(session_id)
        if not context or not context.history:
            return []
        
        # Simple relevance scoring based on query similarity
        relevant_entries = []
        current_query_lower = current_query.lower()
        
        for entry in context.history[-5:]:  # Consider last 5 queries
            relevance_score = self._calculate_relevance(current_query_lower, entry.query.lower())
            if relevance_score > 0.3:  # Threshold for relevance
                relevant_entries.append(entry)
        
        # Sort by timestamp (most recent first) and relevance
        relevant_entries.sort(key=lambda x: (x.timestamp, self._calculate_relevance(current_query_lower, x.query.lower())), reverse=True)
        
        return relevant_entries[:3]  # Return top 3 most relevant
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the session including statistics and recent activity"""
        context = self.get_context(session_id)
        if not context:
            return {"error": "Session not found"}
        
        # Calculate session statistics
        total_queries = len(context.history)
        total_results = sum(entry.result_count for entry in context.history)
        session_duration = (datetime.now() - context.history[0].timestamp).total_seconds() if context.history else 0
        
        # Get common query themes
        query_themes = self._extract_query_themes(context.history)
        
        return {
            "session_id": session_id,
            "total_queries": total_queries,
            "total_results_found": total_results,
            "session_duration_minutes": int(session_duration / 60),
            "active_filters": context.active_filters,
            "common_themes": query_themes,
            "last_activity": context.last_updated.isoformat(),
            "recent_queries": [entry.query for entry in context.history[-3:]]
        }
    
    def get_active_session_count(self) -> int:
        """Get the number of currently active sessions"""
        with self._lock:
            self._cleanup_expired_sessions()
            return len(self.sessions)
    
    def get_total_session_count(self) -> int:
        """Get total number of sessions (including expired ones that haven't been cleaned up)"""
        return len(self.sessions)
    
    def get_all_sessions_summary(self) -> Dict[str, Any]:
        """Get a summary of all active sessions"""
        with self._lock:
            self._cleanup_expired_sessions()
            
            summaries = {}
            for session_id, context in self.sessions.items():
                summaries[session_id] = {
                    "query_count": len(context.history),
                    "last_updated": context.last_updated.isoformat(),
                    "last_query": context.history[-1].query if context.history else None
                }
            
            return {
                "total_active_sessions": len(self.sessions),
                "sessions": summaries
            }
    
    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session data for analysis or backup"""
        context = self.get_context(session_id)
        if not context:
            return None
        
        return {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "session_data": {
                "history": [
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "query": entry.query,
                        "dsl_query": entry.dsl_query,
                        "result_count": entry.result_count,
                        "summary": entry.summary
                    }
                    for entry in context.history
                ],
                "active_filters": context.active_filters,
                "last_updated": context.last_updated.isoformat()
            }
        }
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions (called with lock already held)"""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, context in self.sessions.items()
            if current_time - context.last_updated > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def _remove_oldest_session(self):
        """Remove the oldest session to make room for new ones (called with lock already held)"""
        if not self.sessions:
            return
        
        oldest_session_id = min(
            self.sessions.keys(),
            key=lambda sid: self.sessions[sid].last_updated
        )
        
        del self.sessions[oldest_session_id]
        print(f"🗑️  Removed oldest session {oldest_session_id[:8]}... to make room")
    
    def _update_active_filters(self, context: ConversationContext, dsl_query: Dict[str, Any]):
        """Update active filters based on the current DSL query"""
        # Extract filters from the DSL query
        query_obj = dsl_query.get("query", {})
        query_bool = query_obj.get("bool", {}) if isinstance(query_obj, dict) else {}

        def process_conditions(conditions: List[Dict[str, Any]]):
            for cond in conditions or []:
                if not isinstance(cond, dict):
                    continue
                if "range" in cond and isinstance(cond["range"], dict):
                    field, range_config = next(iter(cond["range"].items()))
                    if field in ("@timestamp", "timestamp"):
                        context.active_filters["time_range"] = range_config
                    elif field == "rule.level":
                        context.active_filters["severity_filter"] = range_config
                elif "term" in cond and isinstance(cond["term"], dict):
                    field, value = next(iter(cond["term"].items()))
                    context.active_filters[f"filter_{field}"] = value
                elif "terms" in cond and isinstance(cond["terms"], dict):
                    field, values = next(iter(cond["terms"].items()))
                    if field == "rule.groups":
                        context.active_filters["rule_groups"] = values

        # Process both filter and must clauses
        process_conditions(query_bool.get("filter", []))
        process_conditions(query_bool.get("must", []))
    
    def _calculate_relevance(self, query1: str, query2: str) -> float:
        """Calculate relevance score between two queries (simple word overlap)"""
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_query_themes(self, history: List[ContextEntry]) -> List[str]:
        """Extract common themes from query history"""
        if not history:
            return []
        
        # Count word frequency across all queries
        word_counts = {}
        security_keywords = {
            "login", "authentication", "failed", "malware", "suspicious", "attack",
            "brute", "force", "network", "connection", "user", "ip", "address",
            "file", "access", "powershell", "command", "dns", "domain"
        }
        
        for entry in history:
            words = entry.query.lower().split()
            for word in words:
                if word in security_keywords and len(word) > 3:
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top themes
        sorted_themes = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:5] if count > 1]