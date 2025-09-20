# server/main.py
"""
Main FastAPI application for the SIEM AI Agent.
This serves as the central API that orchestrates NLP processing,
SIEM queries, and conversation management.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

# Import our models and services
from models import (
    QueryRequest, ApiResponse, ReportRequest, ReportResponse,
    HealthCheckResponse, ErrorResponse, QueryStats, LogResult
)
from nlp_service import generate_dsl_query, generate_suggestions, analyze_query_intent
from siem_connector import query_siem, get_siem_status, force_mock_mode
from context_manager import ContextManager
from visualization_service import create_security_report

# Global variables
app_start_time = time.time()
context_manager = ContextManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("🚀 Starting SIEM AI Agent API...")
    print("📊 Checking SIEM connectivity...")
    
    # Check SIEM status on startup
    siem_status = get_siem_status()
    if siem_status["using_mock_data"]:
        print("📄 Running in mock data mode")
    else:
        print("✅ Connected to live SIEM")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down SIEM AI Agent API...")


# FastAPI Application Setup
app = FastAPI(
    title="SIEM AI Agent API",
    description="Conversational SIEM Assistant for Investigation and Automated Threat Reporting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_type="http_error",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors"""
    print(f"❌ Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_type="internal_error",
            message="An unexpected error occurred",
            details={"error": str(exc)},
            suggestion="Please try again or contact support if the issue persists"
        ).dict()
    )


# --- API Endpoints ---

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information"""
    return {
        "service": "SIEM AI Agent API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    siem_status = get_siem_status()
    
    # Determine overall status
    if siem_status["status"] == "connected":
        status = "healthy"
    elif siem_status["using_mock_data"]:
        status = "healthy"  # Mock mode is acceptable for development
    else:
        status = "degraded"
    
    return HealthCheckResponse(
        status=status,
        elasticsearch_connected=(siem_status["status"] == "connected"),
        nlp_service_ready=True,  # NLP service is always ready in this implementation
        uptime_seconds=int(time.time() - app_start_time),
        version="1.0.0"
    )


@app.post("/query", response_model=ApiResponse)
async def handle_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint for processing natural language SIEM queries.
    
    This endpoint orchestrates the entire process:
    1. Analyzes the query intent and type
    2. Retrieves conversation context if provided
    3. Calls the NLP service to generate Elasticsearch DSL
    4. Executes the query against the SIEM
    5. Formats and returns results with suggestions
    6. Updates conversation context
    """
    query_start_time = time.time()
    
    try:
        print(f"🔍 Processing query: '{request.question}'")
        
        # Generate or use session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Analyze query intent
        query_type = analyze_query_intent(request.question)
        print(f"📊 Query type identified: {query_type}")
        
        # Get conversation context
        conversation_context = None
        if session_id:
            conversation_context = context_manager.get_context(session_id)
            print(f"💭 Retrieved context with {len(conversation_context.history) if conversation_context else 0} previous queries")
        
        # Prepare context for NLP processing
        context_queries = []
        if conversation_context:
            context_queries = [entry.query for entry in conversation_context.history[-3:]]  # Last 3 queries
        
        # Add any additional context from the request
        if request.context:
            context_queries.extend(request.context)
        
        # Generate DSL query using NLP service
        dsl_query = generate_dsl_query(
            question=request.question,
            context=context_queries,
            max_results=request.max_results or 20
        )
        
        # Apply time range filter if specified
        if request.time_range:
            # This would be enhanced to parse various time range formats
            print(f"⏰ Time range filter requested: {request.time_range}")
        
        # Execute query against SIEM
        results, query_stats = query_siem(dsl_query)
        
        # Generate natural language summary
        summary = _generate_summary(request.question, results, query_stats)
        
        # Generate follow-up suggestions
        suggestions = generate_suggestions(request.question, len(results))
        
        # Prepare response
        response = ApiResponse(
            summary=summary,
            results=results,
            query_stats=query_stats,
            session_id=session_id,
            suggestions=suggestions,
            has_more_results=(len(results) == (request.max_results or 20) and query_stats.total_hits > len(results))
        )
        
        # Update context in background
        background_tasks.add_task(
            _update_context,
            session_id,
            request.question,
            dsl_query,
            len(results),
            summary
        )
        
        query_time = int((time.time() - query_start_time) * 1000)
        print(f"✅ Query completed successfully in {query_time}ms")
        
        return response
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@app.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate automated security reports based on SIEM data.
    
    This endpoint creates comprehensive reports with summaries,
    analysis, and visualizations based on the specified criteria.
    """
    try:
        print(f"📊 Generating {request.report_type} report for {request.time_period}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create a query based on report type and time period
        report_query = _create_report_query(request.report_type, request.time_period, request.filters)
        
        # Execute the query
        results, query_stats = query_siem(report_query)
        
        # Generate report content
        report_response = _generate_report_content(
            request.report_type,
            request.time_period,
            results,
            request.include_charts
        )
        
        # Add session ID and generation timestamp
        report_response.session_id = session_id
        report_response.generation_timestamp = datetime.now()
        
        print(f"📋 Report generated successfully with {len(results)} events analyzed")
        return report_response
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@app.get("/dashboard", response_class=HTMLResponse)
async def visual_security_dashboard():
    """
    🎯 HACKATHON SHOWCASE: Visual Security Dashboard
    
    This is the WOW factor endpoint that generates stunning visualizations
    for judges. Creates interactive charts, geo maps, and insights.
    """
    try:
        print("🎨 Generating visual security dashboard...")
        
        # Get all recent data for comprehensive visualization
        dashboard_query = {
            "size": 500,  # Get lots of data for rich visuals
            "query": {"match_all": {}},
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        results, _ = query_siem(dashboard_query)
        
        # Convert LogResult objects to dictionaries for visualization
        events_data = []
        for result in results:
            if hasattr(result, 'dict'):
                events_data.append(result.dict())
            elif isinstance(result, dict):
                events_data.append(result)
        
        # Generate visual dashboard
        dashboard_data = create_security_report(events_data)
        
        # Create HTML dashboard
        html_content = _create_dashboard_html(dashboard_data)
        
        print("✅ Visual dashboard generated successfully")
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        error_html = f"""
        <html><body>
        <h1>Dashboard Error</h1>
        <p>Error generating dashboard: {str(e)}</p>
        </body></html>
        """
        return HTMLResponse(content=error_html, status_code=500)


@app.get("/dashboard/api")
async def dashboard_api():
    """API version of dashboard for frontend integration"""
    try:
        dashboard_query = {
            "size": 500,
            "query": {"match_all": {}},
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        results, query_stats = query_siem(dashboard_query)
        
        # Convert to dicts
        events_data = []
        for result in results:
            if hasattr(result, 'dict'):
                events_data.append(result.dict())
            elif isinstance(result, dict):
                events_data.append(result)
        
        dashboard_data = create_security_report(events_data)
        dashboard_data["query_stats"] = query_stats.dict() if hasattr(query_stats, 'dict') else query_stats
        
        return dashboard_data
        
    except Exception as e:
        print(f"❌ Error generating dashboard API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/context/{session_id}")
async def get_conversation_context(session_id: str):
    """Get conversation context for a specific session"""
    try:
        context = context_manager.get_context(session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "query_count": len(context.history),
            "last_updated": context.last_updated,
            "active_filters": context.active_filters,
            "recent_queries": [entry.query for entry in context.history[-5:]]  # Last 5 queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve context: {str(e)}")


@app.delete("/context/{session_id}")
async def clear_conversation_context(session_id: str):
    """Clear conversation context for a specific session"""
    try:
        context_manager.clear_context(session_id)
        return {"message": f"Context cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear context: {str(e)}")


@app.get("/siem/status")
async def get_siem_connection_status():
    """Get SIEM connection status and health information"""
    return get_siem_status()


@app.post("/siem/mock-mode")
async def toggle_mock_mode(enable: bool = True):
    """Toggle mock data mode (for testing purposes)"""
    try:
        force_mock_mode(enable)
        mode = "enabled" if enable else "disabled"
        return {"message": f"Mock mode {mode}", "using_mock_data": enable}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle mock mode: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """Get API metrics and usage statistics"""
    return {
        "uptime_seconds": int(time.time() - app_start_time),
        "active_sessions": context_manager.get_active_session_count(),
        "total_sessions": context_manager.get_total_session_count(),
        "siem_status": get_siem_status()
    }


# --- Helper Functions ---

def _generate_summary(question: str, results: List[LogResult], query_stats: QueryStats) -> str:
    """Generate a natural language summary of query results"""
    result_count = len(results)
    total_hits = query_stats.total_hits
    
    if result_count == 0:
        return f"No security events found matching '{question}'. Try broadening your search criteria or checking the time range."
    
    summary = f"Found {result_count} security events"
    if total_hits > result_count:
        summary += f" (showing {result_count} of {total_hits} total matches)"
    
    summary += f" for '{question}'."
    
    # Add insights based on results
    if results:
        # Count by severity
        severity_counts = {}
        for result in results:
            severity = result.severity or "unknown"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts:
            high_severity_count = severity_counts.get("high", 0) + severity_counts.get("critical", 0)
            if high_severity_count > 0:
                summary += f" {high_severity_count} events are high or critical severity."
    
    return summary


async def _update_context(session_id: str, query: str, dsl_query: Dict[str, Any], 
                         result_count: int, summary: str):
    """Update conversation context (runs in background)"""
    try:
        context_manager.add_to_context(session_id, query, dsl_query, result_count, summary)
        print(f"💾 Updated context for session {session_id}")
    except Exception as e:
        print(f"⚠️  Failed to update context: {e}")


def _create_report_query(report_type: str, time_period: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Create DSL query for report generation"""
    # Basic query structure for reports
    query = {
        "size": 1000,  # Reports typically need more data
        "sort": [{"timestamp": {"order": "desc"}}],
        "query": {
            "bool": {
                "must": [{"match_all": {}}],
                "filter": []
            }
        },
        "aggs": {
            "severity_distribution": {
                "terms": {"field": "rule.level"}
            },
            "top_rules": {
                "terms": {"field": "rule.id", "size": 10}
            },
            "events_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "calendar_interval": "hour"
                }
            }
        }
    }
    
    # Add report type specific filters
    if report_type == "malware_summary":
        query["query"]["bool"]["must"].append({
            "terms": {"rule.groups": ["malware", "virus", "trojan"]}
        })
    elif report_type == "login_analysis":
        query["query"]["bool"]["must"].append({
            "terms": {"rule.groups": ["authentication_failed", "authentication_success"]}
        })
    
    # Add time period filter
    if time_period:
        # This would be enhanced to parse various time period formats
        print(f"📅 Report time period: {time_period}")
    
    # Add custom filters
    for field, value in filters.items():
        query["query"]["bool"]["filter"].append({
            "term": {field: value}
        })
    
    return query


def _generate_report_content(report_type: str, time_period: str, 
                           results: List[LogResult], include_charts: bool) -> ReportResponse:
    """Generate comprehensive report content"""
    # Create report title
    report_title = f"{report_type.replace('_', ' ').title()} Report - {time_period}"
    
    # Generate executive summary
    executive_summary = f"Security analysis for {time_period} period identified {len(results)} relevant events."
    
    # Generate detailed analysis
    detailed_analysis = _create_detailed_analysis(results, report_type)
    
    # Generate key findings
    key_findings = _extract_key_findings(results, report_type)
    
    # Generate recommendations
    recommendations = _generate_recommendations(results, report_type)
    
    # Generate charts if requested
    charts = []
    if include_charts:
        charts = _generate_charts(results)
    
    return ReportResponse(
        report_title=report_title,
        executive_summary=executive_summary,
        detailed_analysis=detailed_analysis,
        charts=charts,
        key_findings=key_findings,
        recommendations=recommendations,
        data_sources=["wazuh-alerts", "mock-data"],
        session_id="",  # Will be set by caller
        generation_timestamp=datetime.now()
    )


def _create_detailed_analysis(results: List[LogResult], report_type: str) -> str:
    """Create detailed analysis text for reports"""
    if not results:
        return "No security events found for the specified criteria and time period."
    
    analysis = f"Analysis of {len(results)} security events:\n\n"
    
    # Severity distribution
    severity_counts = {}
    for result in results:
        severity = str(result.severity or "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    analysis += "Severity Distribution:\n"
    for severity, count in sorted(severity_counts.items()):
        analysis += f"- {severity.title()}: {count} events\n"
    
    return analysis


def _extract_key_findings(results: List[LogResult], report_type: str) -> List[str]:
    """Extract key findings from the analysis"""
    findings = []
    
    if not results:
        findings.append("No security events detected during the analysis period")
        return findings
    
    # Count high severity events
    high_severity = [r for r in results if r.severity in ["high", "critical"]]
    if high_severity:
        findings.append(f"{len(high_severity)} high or critical severity events detected")
    
    # Count unique source IPs
    unique_ips = set(r.source_ip for r in results if r.source_ip)
    if unique_ips:
        findings.append(f"Events originated from {len(unique_ips)} unique IP addresses")
    
    # Count affected users
    unique_users = set(r.user for r in results if r.user)
    if unique_users:
        findings.append(f"{len(unique_users)} user accounts involved in security events")
    
    return findings


def _generate_recommendations(results: List[LogResult], report_type: str) -> List[str]:
    """Generate security recommendations based on findings"""
    recommendations = []
    
    if not results:
        recommendations.append("Continue monitoring for security events")
        return recommendations
    
    # Check for authentication failures
    auth_failures = [r for r in results if "authentication_failed" in str(r.raw_data)]
    if auth_failures:
        recommendations.append("Review and strengthen authentication policies")
        recommendations.append("Consider implementing multi-factor authentication")
    
    # Check for external connections
    external_events = [r for r in results if r.source_ip and not r.source_ip.startswith("192.168.")]
    if external_events:
        recommendations.append("Review firewall rules for external connections")
        recommendations.append("Implement geo-blocking for high-risk regions")
    
    recommendations.append("Maintain regular security monitoring and review cycles")
    
    return recommendations


def _generate_charts(results: List[LogResult]) -> List[Dict[str, Any]]:
    """Generate chart data for visualizations"""
    charts = []
    
    if not results:
        return charts
    
    # Severity distribution chart
    severity_counts = {}
    for result in results:
        severity = str(result.severity or "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    if severity_counts:
        charts.append({
            "chart_type": "pie",
            "title": "Events by Severity Level",
            "data": [{"name": k, "value": v} for k, v in severity_counts.items()],
            "x_axis_label": "Severity",
            "y_axis_label": "Count"
        })
    
    return charts


def _create_dashboard_html(dashboard_data: Dict[str, Any]) -> str:
    """Create beautiful HTML dashboard for hackathon demo"""
    summary = dashboard_data.get("summary_stats", {})
    charts = dashboard_data.get("charts", {})
    insights = dashboard_data.get("insights", [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🛡️ SIEM AI Agent - Security Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                min-height: 100vh;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }}
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #4ECDC4;
            }}
            .stat-label {{
                margin-top: 10px;
                opacity: 0.8;
            }}
            .chart-container {{
                background: rgba(255,255,255,0.1);
                margin: 20px 0;
                border-radius: 15px;
                padding: 20px;
                backdrop-filter: blur(10px);
            }}
            .insights-panel {{
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                padding: 20px;
                border-radius: 15px;
                margin-top: 30px;
            }}
            .insight {{
                background: rgba(255,255,255,0.2);
                padding: 15px;
                margin: 10px 0;
                border-radius: 10px;
                border-left: 5px solid #FFEAA7;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                opacity: 0.7;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ SIEM AI Agent Dashboard</h1>
            <p>Real-time Security Analytics & Threat Intelligence</p>
            <p><em>Powered by Gemini AI & Advanced Analytics</em></p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{summary.get('total_events', 0)}</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary.get('critical_alerts', 0)}</div>
                <div class="stat-label">Critical Alerts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary.get('unique_source_ips', 0)}</div>
                <div class="stat-label">Unique IPs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary.get('countries_involved', 0)}</div>
                <div class="stat-label">Countries</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📈 Security Events Timeline</h2>
            {charts.get('timeline', '<p>Timeline chart not available</p>')}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="chart-container">
                <h3>🎯 Severity Distribution</h3>
                {charts.get('severity_distribution', '<p>Chart not available</p>')}
            </div>
            <div class="chart-container">
                <h3>🌐 Top Attack Sources</h3>
                {charts.get('top_attackers', '<p>Chart not available</p>')}
            </div>
        </div>
        
        <div class="chart-container">
            <h2>🗺️ Global Attack Map</h2>
            {charts.get('geo_map', '<p>Map not available</p>')}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="chart-container">
                <h3>⚡ Attack Types</h3>
                {charts.get('attack_types', '<p>Chart not available</p>')}
            </div>
            <div class="chart-container">
                <h3>🕐 Hourly Patterns</h3>
                {charts.get('hourly_patterns', '<p>Chart not available</p>')}
            </div>
        </div>
        
        <div class="insights-panel">
            <h2>🧠 AI Security Insights</h2>
            {"".join([f'<div class="insight">{insight}</div>' for insight in insights])}
        </div>
        
        <div class="footer">
            <p>🚀 Powered by SIEM AI Agent | Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>💡 <strong>Hackathon Demo:</strong> This dashboard showcases real-time security analytics capabilities</p>
        </div>
    </body>
    </html>
    """
    
    return html_content


# --- Application Entry Point ---
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SIEM AI Agent server...")
    print("📖 API documentation available at: http://localhost:8000/docs")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )