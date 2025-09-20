# server/models.py
"""
Data models for the SIEM AI Agent API using Pydantic for validation and serialization.
These models define the contract between frontend and backend components.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class QueryType(str, Enum):
    """Types of queries supported by the SIEM AI Agent"""
    INVESTIGATION = "investigation"
    REPORT = "report"
    CONTEXTUAL = "contextual"


class SeverityLevel(str, Enum):
    """Security event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QueryRequest(BaseModel):
    """
    Request model for natural language queries to the SIEM.
    Supports both single queries and conversational context.
    """
    question: str = Field(..., description="Natural language question about security events")
    query_type: QueryType = Field(default=QueryType.INVESTIGATION, description="Type of query being performed")
    session_id: Optional[str] = Field(None, description="Session ID for maintaining conversation context")
    context: Optional[List[str]] = Field(default=[], description="Previous queries in this conversation")
    time_range: Optional[str] = Field(None, description="Time range filter (e.g., 'last 24 hours', 'yesterday')")
    max_results: Optional[int] = Field(default=20, description="Maximum number of results to return")


class LogResult(BaseModel):
    """
    Structure for individual security event/log results from SIEM queries.
    Represents a single alert or log entry.
    """
    timestamp: str = Field(..., description="Event timestamp in ISO format")
    event_id: Optional[str] = Field(None, description="Unique event identifier")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    destination_ip: Optional[str] = Field(None, description="Destination IP address")
    user: Optional[str] = Field(None, description="Associated username")
    rule_id: Optional[str] = Field(None, description="SIEM rule ID that triggered")
    rule_description: str = Field(..., description="Human-readable rule description")
    severity: Optional[SeverityLevel] = Field(None, description="Event severity level")
    source_system: Optional[str] = Field(None, description="System that generated the event")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw event data from SIEM")
    details: str = Field(..., description="Formatted event details for display")


class QueryStats(BaseModel):
    """Statistics about the executed query"""
    total_hits: int = Field(..., description="Total number of matching events")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
    indices_searched: List[str] = Field(default=[], description="Elasticsearch indices that were searched")
    dsl_query: Dict[str, Any] = Field(..., description="The actual Elasticsearch DSL query that was executed")


class ApiResponse(BaseModel):
    """
    Main response model for SIEM queries.
    Contains results, metadata, and conversation context.
    """
    summary: str = Field(..., description="Natural language summary of the query results")
    results: List[LogResult] = Field(..., description="List of matching security events")
    query_stats: QueryStats = Field(..., description="Query execution statistics")
    session_id: str = Field(..., description="Session ID for conversation tracking")
    suggestions: Optional[List[str]] = Field(default=[], description="Suggested follow-up queries")
    has_more_results: bool = Field(default=False, description="Whether there are more results available")


class RawQueryRequest(BaseModel):
    """Request model for directly submitting an OpenSearch DSL query"""
    dsl: Dict[str, Any] = Field(..., description="Raw OpenSearch DSL query to execute")


class ReportRequest(BaseModel):
    """Request model for generating automated security reports"""
    report_type: str = Field(..., description="Type of report to generate (e.g., 'malware_summary', 'login_analysis')")
    time_period: str = Field(..., description="Time period for the report (e.g., 'last_week', 'last_month')")
    include_charts: bool = Field(default=True, description="Whether to include visual charts in the report")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Additional filters for the report")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")


class ChartData(BaseModel):
    """Data structure for charts and visualizations"""
    chart_type: str = Field(..., description="Type of chart (bar, line, pie, etc.)")
    title: str = Field(..., description="Chart title")
    data: List[Dict[str, Union[str, int, float]]] = Field(..., description="Chart data points")
    x_axis_label: Optional[str] = Field(None, description="X-axis label")
    y_axis_label: Optional[str] = Field(None, description="Y-axis label")


class ReportResponse(BaseModel):
    """Response model for generated reports"""
    report_title: str = Field(..., description="Title of the generated report")
    executive_summary: str = Field(..., description="High-level summary of findings")
    detailed_analysis: str = Field(..., description="Detailed analysis and findings")
    charts: List[ChartData] = Field(default=[], description="Visual charts and graphs")
    key_findings: List[str] = Field(..., description="List of key findings from the analysis")
    recommendations: List[str] = Field(default=[], description="Security recommendations based on findings")
    data_sources: List[str] = Field(..., description="SIEM indices and data sources used")
    generation_timestamp: datetime = Field(default_factory=datetime.now, description="When the report was generated")
    session_id: str = Field(..., description="Session ID for conversation tracking")


class ContextEntry(BaseModel):
    """Entry in conversation context history"""
    timestamp: datetime = Field(default_factory=datetime.now, description="When the query was made")
    query: str = Field(..., description="The original natural language query")
    dsl_query: Dict[str, Any] = Field(..., description="The generated Elasticsearch DSL query")
    result_count: int = Field(..., description="Number of results returned")
    summary: str = Field(..., description="Summary of the results")


class ConversationContext(BaseModel):
    """Model for tracking conversation state across multiple queries"""
    session_id: str = Field(..., description="Unique session identifier")
    history: List[ContextEntry] = Field(default=[], description="Query history for this session")
    active_filters: Dict[str, Any] = Field(default={}, description="Currently active filters")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error_type: str = Field(..., description="Type of error that occurred")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    suggestion: Optional[str] = Field(None, description="Suggested action to resolve the error")
    session_id: Optional[str] = Field(None, description="Session ID if available")


class HealthCheckResponse(BaseModel):
    """Health check response for monitoring"""
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    elasticsearch_connected: bool = Field(..., description="Whether Elasticsearch connection is active")
    nlp_service_ready: bool = Field(..., description="Whether NLP service is ready")
    uptime_seconds: int = Field(..., description="Service uptime in seconds")
    version: str = Field(..., description="API version")
    demo_features: Optional[Dict[str, Any]] = Field(default={}, description="Demo-specific feature status")