# server/main_hackathon.py
"""
🎯 HACKATHON-OPTIMIZED SIEM AI AGENT
Streamlined to 4 core endpoints for maximum demo impact with judges.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

# Import our simplified models and services
from models import (
    QueryRequest, ApiResponse, ReportRequest, HealthCheckResponse
)
from nlp_service import generate_dsl_query, generate_suggestions
from siem_connector import query_siem, get_siem_status
from visualization_service import create_security_report

# Global variables
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    print("🚀 Starting HACKATHON SIEM AI Agent...")
    print("🎯 Optimized for demo impact with 4 core endpoints")
    
    siem_status = get_siem_status()
    if siem_status["using_mock_data"]:
        print("🎨 Running with 400+ rich demo events")
    else:
        print("✅ Connected to live SIEM")
    
    yield
    print("🏁 Demo complete!")


# FastAPI Application Setup
app = FastAPI(
    title="🛡️ SIEM AI Agent - Hackathon Demo",
    description="Conversational SIEM Assistant powered by Gemini AI with stunning visualizations",
    version="2.0.0-hackathon",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === CORE ENDPOINT #1: NATURAL LANGUAGE QUERY ===

@app.post("/query", response_model=ApiResponse)
async def handle_query(request: QueryRequest):
    """
    🧠 MAIN NLP ENDPOINT: Convert natural language to security insights
    
    This is the core demo feature powered by Gemini AI.
    Examples:
    - "Show me failed logins in the last 24 hours"
    - "Find suspicious activity from Russia"
    - "Any malware detected this week?"
    """
    query_start_time = time.time()
    
    try:
        print(f"🧠 Processing: '{request.question}'")
        
        # Use Gemini AI to generate DSL query
        dsl_query = generate_dsl_query(request.question, request.context)
        
        # Execute against SIEM data
        results, query_stats = query_siem(dsl_query)
        
        # Generate intelligent suggestions
        suggestions = generate_suggestions(request.question, [r.dict() if hasattr(r, 'dict') else r for r in results])
        
        # Create natural language summary
        summary = _create_smart_summary(request.question, results)
        
        # Generate session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        response = ApiResponse(
            summary=summary,
            results=results,
            query_stats=query_stats,
            session_id=session_id,
            suggestions=suggestions,
            has_more_results=len(results) >= 20
        )
        
        query_time = int((time.time() - query_start_time) * 1000)
        print(f"✅ Query completed in {query_time}ms with {len(results)} results")
        
        return response
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# === CORE ENDPOINT #2: VISUAL DASHBOARD ===

@app.get("/dashboard", response_class=HTMLResponse)
async def visual_dashboard():
    """
    🎨 VISUAL WOW FACTOR: Stunning security dashboard
    
    This endpoint generates beautiful interactive visualizations:
    - Real-time security metrics
    - Global attack maps
    - Trend analysis charts
    - AI-powered insights
    """
    try:
        print("🎨 Generating visual security dashboard...")
        
        # Get comprehensive data for visualization
        dashboard_query = {
            "size": 500,
            "query": {"match_all": {}},
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        results, _ = query_siem(dashboard_query)
        
        # Convert to visualization format
        events_data = []
        for result in results:
            if hasattr(result, 'dict'):
                events_data.append(result.dict())
            elif isinstance(result, dict):
                events_data.append(result)
        
        # Generate visual dashboard with charts
        dashboard_data = create_security_report(events_data)
        
        # Create stunning HTML dashboard
        html_content = _create_hackathon_dashboard_html(dashboard_data)
        
        print("✅ Visual dashboard ready for demo")
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        error_html = f"""
        <html><body style="background: #1e3c72; color: white; padding: 50px; font-family: Arial;">
        <h1>🛡️ Dashboard Loading...</h1>
        <p>Preparing security visualizations...</p>
        <p><em>Error: {str(e)}</em></p>
        </body></html>
        """
        return HTMLResponse(content=error_html, status_code=500)


# === CORE ENDPOINT #3: INTELLIGENT SUGGESTIONS ===

@app.get("/suggestions")
async def get_suggestions(query: str = ""):
    """
    💡 SMART SUGGESTIONS: AI-powered follow-up queries
    
    Provides intelligent suggestions for security investigation.
    Perfect for guiding users through complex security analysis.
    """
    try:
        print(f"💡 Generating suggestions for: '{query}'")
        
        # Get recent events for context
        recent_query = {
            "size": 50,
            "query": {"match_all": {}},
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        results, _ = query_siem(recent_query)
        events_data = [r.dict() if hasattr(r, 'dict') else r for r in results]
        
        # Generate contextual suggestions
        suggestions = generate_suggestions(query, events_data)
        
        return {
            "suggestions": suggestions,
            "context": f"Based on {len(results)} recent security events",
            "categories": {
                "investigation": suggestions[:2],
                "analysis": suggestions[2:4] if len(suggestions) > 2 else [],
                "reporting": ["Generate security report", "Create visual dashboard"]
            }
        }
        
    except Exception as e:
        print(f"❌ Suggestions error: {e}")
        return {
            "suggestions": [
                "Show me failed logins in the last 24 hours",
                "Find suspicious network activity",
                "Generate security report for this week",
                "Display global attack patterns"
            ],
            "context": "Default suggestions",
            "error": str(e)
        }


# === CORE ENDPOINT #4: HEALTH CHECK ===

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    ✅ SYSTEM STATUS: Health monitoring for demo reliability
    
    Ensures all systems are ready for the hackathon presentation.
    """
    siem_status = get_siem_status()
    
    status = "healthy" if siem_status["status"] == "connected" or siem_status["using_mock_data"] else "degraded"
    
    return HealthCheckResponse(
        status=status,
        elasticsearch_connected=(siem_status["status"] == "connected"),
        nlp_service_ready=True,
        uptime_seconds=int(time.time() - app_start_time),
        version="2.0.0-hackathon",
        demo_features={
            "gemini_ai": True,
            "visual_dashboard": True,
            "rich_mock_data": siem_status["using_mock_data"],
            "event_count": 400 if siem_status["using_mock_data"] else "unknown"
        }
    )


# === HELPER FUNCTIONS ===

def _create_smart_summary(question: str, results: List) -> str:
    """Create intelligent summary of query results"""
    result_count = len(results)
    
    if result_count == 0:
        return f"No security events found matching your query: '{question}'"
    
    # Analyze results for smart insights
    high_severity = sum(1 for r in results if hasattr(r, 'rule') and getattr(r.rule, 'level', 0) >= 8)
    unique_ips = len(set(getattr(r, 'source_ip', '') for r in results if hasattr(r, 'source_ip')))
    
    summary = f"Found {result_count} security events"
    
    if high_severity > 0:
        summary += f" including {high_severity} high-severity alerts"
    
    if unique_ips > 1:
        summary += f" from {unique_ips} different source IPs"
    
    # Add contextual insights based on question
    if "failed" in question.lower() or "login" in question.lower():
        summary += ". Authentication events detected - consider reviewing access patterns."
    elif "malware" in question.lower():
        summary += ". Potential threats identified - immediate investigation recommended."
    elif "suspicious" in question.lower():
        summary += ". Anomalous activity patterns detected - further analysis advised."
    
    return summary


def _create_hackathon_dashboard_html(dashboard_data: Dict[str, Any]) -> str:
    """Create stunning dashboard HTML optimized for hackathon demo"""
    summary = dashboard_data.get("summary_stats", {})
    charts = dashboard_data.get("charts", {})
    insights = dashboard_data.get("insights", [])
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🛡️ SIEM AI Agent - Live Security Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                overflow-x: hidden;
            }}
            
            .hero {{
                text-align: center;
                padding: 40px 20px;
                background: rgba(0,0,0,0.3);
                backdrop-filter: blur(20px);
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            
            .hero h1 {{
                font-size: 3.5em;
                margin: 0;
                background: linear-gradient(45deg, #4ECDC4, #44A08D);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .hero p {{
                font-size: 1.2em;
                opacity: 0.9;
                margin: 10px 0;
            }}
            
            .stats-section {{
                padding: 30px 20px;
                background: rgba(255,255,255,0.05);
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 25px;
                max-width: 1200px;
                margin: 0 auto;
            }}
            
            .stat-card {{
                background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
                padding: 30px;
                border-radius: 20px;
                text-align: center;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            }}
            
            .stat-number {{
                font-size: 3em;
                font-weight: 800;
                background: linear-gradient(45deg, #4ECDC4, #44A08D);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 10px;
            }}
            
            .stat-label {{
                font-size: 1.1em;
                opacity: 0.8;
                font-weight: 500;
            }}
            
            .charts-section {{
                padding: 40px 20px;
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .chart-container {{
                background: rgba(255,255,255,0.08);
                margin: 30px 0;
                border-radius: 25px;
                padding: 30px;
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255,255,255,0.1);
            }}
            
            .chart-title {{
                font-size: 1.8em;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            
            .charts-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin: 30px 0;
            }}
            
            .insights-panel {{
                background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
                padding: 40px;
                border-radius: 25px;
                margin: 40px 20px;
                max-width: 1200px;
                margin-left: auto;
                margin-right: auto;
            }}
            
            .insights-title {{
                font-size: 2.2em;
                margin-bottom: 20px;
                font-weight: 700;
            }}
            
            .insight {{
                background: rgba(255,255,255,0.2);
                padding: 20px;
                margin: 15px 0;
                border-radius: 15px;
                border-left: 5px solid #FFEAA7;
                font-size: 1.1em;
                line-height: 1.4;
            }}
            
            .demo-badge {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                padding: 10px 20px;
                border-radius: 25px;
                font-weight: bold;
                z-index: 1000;
                animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(78, 205, 196, 0.7); }}
                70% {{ box-shadow: 0 0 0 10px rgba(78, 205, 196, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(78, 205, 196, 0); }}
            }}
            
            .footer {{
                text-align: center;
                padding: 40px;
                background: rgba(0,0,0,0.3);
                margin-top: 60px;
            }}
            
            @media (max-width: 768px) {{
                .charts-grid {{
                    grid-template-columns: 1fr;
                }}
                .hero h1 {{
                    font-size: 2.5em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="demo-badge">🏆 HACKATHON DEMO</div>
        
        <div class="hero">
            <h1>🛡️ SIEM AI Agent</h1>
            <p><strong>Live Security Dashboard</strong></p>
            <p>Real-time Threat Intelligence • Powered by Gemini AI • Advanced Analytics</p>
        </div>
        
        <div class="stats-section">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{summary.get('total_events', 0)}</div>
                    <div class="stat-label">Security Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{summary.get('critical_alerts', 0)}</div>
                    <div class="stat-label">Critical Alerts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{summary.get('unique_source_ips', 0)}</div>
                    <div class="stat-label">Unique Source IPs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{summary.get('countries_involved', 0)}</div>
                    <div class="stat-label">Countries Involved</div>
                </div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">📈 Real-time Security Events Timeline</div>
                {charts.get('timeline', '<p style="text-align: center; opacity: 0.7;">Chart loading...</p>')}
            </div>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">🎯 Alert Severity Breakdown</div>
                    {charts.get('severity_distribution', '<p style="text-align: center; opacity: 0.7;">Chart loading...</p>')}
                </div>
                <div class="chart-container">
                    <div class="chart-title">🌐 Top Attack Sources</div>
                    {charts.get('top_attackers', '<p style="text-align: center; opacity: 0.7;">Chart loading...</p>')}
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">🗺️ Global Threat Intelligence Map</div>
                {charts.get('geo_map', '<p style="text-align: center; opacity: 0.7;">Map loading...</p>')}
            </div>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">⚡ Attack Vector Analysis</div>
                    {charts.get('attack_types', '<p style="text-align: center; opacity: 0.7;">Chart loading...</p>')}
                </div>
                <div class="chart-container">
                    <div class="chart-title">🕐 Temporal Attack Patterns</div>
                    {charts.get('hourly_patterns', '<p style="text-align: center; opacity: 0.7;">Chart loading...</p>')}
                </div>
            </div>
        </div>
        
        <div class="insights-panel">
            <div class="insights-title">🧠 AI-Powered Security Insights</div>
            {"".join([f'<div class="insight">{insight}</div>' for insight in insights]) if insights else '<div class="insight">🔍 Analyzing security patterns... AI insights will appear here.</div>'}
        </div>
        
        <div class="footer">
            <h3>🚀 SIEM AI Agent Dashboard</h3>
            <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Powered by Gemini AI</p>
            <p><strong>💡 Hackathon Demo:</strong> Showcasing next-generation security analytics</p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    print("🎯 HACKATHON MODE: Starting optimized SIEM AI Agent...")
    print("🌟 4 Core Endpoints Ready for Demo")
    print("📊 Visual Dashboard: http://localhost:8000/dashboard")
    print("📖 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main_hackathon:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )