import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from nlp_brain import generate_dsl_query
from langchain_google_genai import ChatGoogleGenerativeAI
from models import QueryRequest, ApiResponse, LogResult, QueryStats, RawQueryRequest, NLReportRequest, ReportResponse, ChartData
from siem_connector import SIEMConnector
from config import Settings
from context_manager import ContextManager

# Load environment variables (for GOOGLE_API_KEY, etc.)
load_dotenv()

# FastAPI app
app = FastAPI(title="SIEM AI Agent API", version="1.0.0")

# CORS configuration
FRONTEND_ORIGINS = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS if FRONTEND_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Includes OPTIONS for preflight
    allow_headers=["*"],  # Allow Authorization, Content-Type, etc.
    expose_headers=["*"],
)

# Initialize SIEM connector (will attempt connection; may use mock if not available)
siem = SIEMConnector(use_mock_data=False)
settings = Settings()
context_manager = ContextManager()


def _ensure_track_total_hits(dsl: dict) -> dict:
    try:
        d = dict(dsl)
        if "track_total_hits" not in d:
            d["track_total_hits"] = True
        return d
    except Exception:
        return dsl


def _print_dsl(label: str, dsl: dict):
    print(f"[API][{label}] DSL:")
    try:
        print(json.dumps(dsl, indent=2))
    except Exception:
        print(str(dsl))


def _build_failed_login_candidates(base_dsl: dict) -> list[tuple[str, dict]]:
    """Construct a set of candidate DSLs for failed-login style queries."""
    candidates: list[tuple[str, dict]] = []
    # 0) Original (with track_total_hits)
    candidates.append(("original", _ensure_track_total_hits(base_dsl)))

    # 1) Should-match phrases in message/description
    candidates.append((
        "phrases_message_description",
        {
            "size": base_dsl.get("size", 5),
            "sort": base_dsl.get("sort", [{"@timestamp": {"order": "desc"}}]),
            "track_total_hits": True,
            "query": {
                "bool": {
                    "should": [
                        {"match_phrase": {"message": "authentication failure"}},
                        {"match_phrase": {"message": "failed login"}},
                        {"match_phrase": {"rule.description": "authentication failure"}},
                        {"match_phrase": {"rule.description": "failed"}}
                    ],
                    "minimum_should_match": 1,
                }
            },
        },
    ))

    # 2) query_string across multiple fields
    candidates.append((
        "query_string_multi_fields",
        {
            "size": base_dsl.get("size", 5),
            "sort": base_dsl.get("sort", [{"@timestamp": {"order": "desc"}}]),
            "track_total_hits": True,
            "query": {
                "query_string": {
                    "query": '("authentication failure" OR "failed login" OR failure OR failed)',
                    "fields": ["message", "rule.description", "full_log"],
                    "default_operator": "OR"
                }
            }
        },
    ))

    # 3) Wildcard on keyword field rule.description (if keyword)
    candidates.append((
        "wildcard_rule_description",
        {
            "size": base_dsl.get("size", 5),
            "sort": base_dsl.get("sort", [{"@timestamp": {"order": "desc"}}]),
            "track_total_hits": True,
            "query": {
                "bool": {
                    "should": [
                        {"wildcard": {"rule.description": "*authentication*failure*"}},
                        {"wildcard": {"rule.description": "*failed*login*"}}
                    ],
                    "minimum_should_match": 1
                }
            }
        }
    ))

    return candidates


def _agentic_execute(user_question: str, base_dsl: dict) -> tuple[list, QueryStats, dict, str]:
    """Try a sequence of DSL variants until results are found. Returns (results, stats, final_dsl, strategy_label)."""
    # Determine if the question is about failed logins
    ql = (user_question or "").lower()
    if any(k in ql for k in ["failed login", "failed logins", "authentication failure", "login failures", "failed authentication"]):
        candidates = _build_failed_login_candidates(base_dsl)
    else:
        candidates = [("original", _ensure_track_total_hits(base_dsl))]

    last_stats = None
    last_results = []
    last_label = "original"
    last_dsl = base_dsl

    for idx, (label, dsl) in enumerate(candidates, start=1):
        print(f"[API][Strategy {idx}/{len(candidates)}] {label}")
        _print_dsl(label, dsl)
        try:
            results, stats = siem.query(dsl)
            print(f"[API][Strategy {idx}] hits={stats.total_hits} time_ms={stats.query_time_ms} indices={stats.indices_searched}")
            if stats.total_hits and stats.total_hits > 0:
                return results, stats, dsl, label
            last_stats, last_results, last_label, last_dsl = stats, results, label, dsl
        except Exception as e:
            print(f"[API][Strategy {idx}] error: {e}")
            last_stats, last_results, last_label, last_dsl = None, [], label, dsl
            continue

    # Nothing found; return last attempt
    return last_results, (last_stats or QueryStats(total_hits=0, query_time_ms=0, indices_searched=[], dsl_query=last_dsl)), last_dsl, last_label


@app.get("/api/health")
def health():
    status = siem.get_connection_status()
    nlp_ready = bool(os.getenv("GOOGLE_API_KEY", "").strip())
    return {
        "status": "healthy",
        "opensearch": status,
        "nlp_service_ready": nlp_ready,
        "version": "1.0.0",
    }


@app.post("/api/query")
def handle_query(request: QueryRequest) -> JSONResponse:
    user_question = request.question.strip()
    if not user_question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    # 1) Generate DSL from the master prompt (nlp_brain)
    print(f"[API] New query request: '{user_question}'")
    status = siem.get_connection_status()
    print(f"[API] OpenSearch connection status: {status}")
    # Prepare conversation context if session provided
    session_id = request.session_id or os.getenv("DEFAULT_SESSION_ID", "default-session")
    relevant_snippets = []
    active_filter_ctx = {}
    ctx = None
    if session_id:
        try:
            ctx = context_manager.get_context(session_id)
            if ctx and ctx.history:
                # Build a small textual context from last few entries
                for entry in ctx.history[-3:]:
                    relevant_snippets.append(
                        f"Prev: '{entry.query}' -> results={entry.result_count}"
                    )
                active_filter_ctx = ctx.active_filters or {}
        except Exception as e:
            print(f"[API] Context fetch error: {e}")

    conversation_context_text = "\n".join(relevant_snippets) if relevant_snippets else ""
    active_filter_context_text = json.dumps(active_filter_ctx) if active_filter_ctx else ""

    dsl_query = generate_dsl_query(
        user_question,
        conversation_context=conversation_context_text,
        active_filter_context=active_filter_context_text,
    )
    print("[API] NLP-generated DSL:")
    try:
        print(json.dumps(dsl_query, indent=2))
    except Exception:
        print(str(dsl_query))
    if not dsl_query:
        return JSONResponse(
            status_code=422,
            content={
                "summary": "Failed to generate a valid DSL query for the input",
                "dsl": {},
                "results": [],
                "query_stats": {"total_hits": 0, "query_time_ms": 0, "indices_searched": [], "dsl_query": {}},
            },
        )

    # 2) Agentic execution: try multiple strategies until we get results
    try:
        results, stats, final_dsl, strategy = _agentic_execute(user_question, dsl_query)
        print(f"[API] Final strategy={strategy} hits={stats.total_hits} time_ms={stats.query_time_ms} indices={stats.indices_searched}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SIEM query failed: {e}")

    # Convert pydantic models to dictionaries for JSON response
    results_payload = [r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in results]
    stats_payload = stats.model_dump() if hasattr(stats, "model_dump") else stats.dict()

    # 3) Optional: Summarize results with Gemini if API key configured
    summary = "No results found."
    if results_payload:
        try:
            api_key = os.getenv("GOOGLE_API_KEY", "").strip()
            if api_key:
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, convert_system_message_to_human=True)
                summary_prompt = (
                    "Summarize these SIEM results for the user query in a clear paragraph.\n"
                    f"User query: {user_question}\n"
                    f"Results (truncated): {json.dumps(results_payload[:5], indent=2)}"
                )
                summary_response = llm.invoke(summary_prompt)
                summary = getattr(summary_response, "content", None) or summary
            else:
                summary = f"Found {len(results_payload)} results. Showing first {min(5, len(results_payload))}."
        except Exception:
            summary = f"Found {len(results_payload)} results."

    # Build repro curl
    try:
        hosts = settings.get_opensearch_hosts()
        host = hosts[0] if hosts else "https://localhost:9200"
        repro_curl = (
            "curl -k -u <user>:<pass> -H 'Content-Type: application/json' -X POST '"
            + host
            + "/"
            + (stats.indices_searched[0] if stats.indices_searched else "wazuh-alerts-*")
            + "/_search?pretty' -d '"
            + json.dumps(final_dsl)
            + "'"
        )
    except Exception:
        repro_curl = None

    # 4) Update session context
    try:
        if session_id:
            summary_for_context = summary if isinstance(summary, str) else str(summary)
            context_manager.add_to_context(
                session_id=session_id,
                query=user_question,
                dsl_query=final_dsl if 'final_dsl' in locals() else dsl_query,
                result_count=stats_payload.get("total_hits", 0) if isinstance(stats_payload, dict) else 0,
                summary=summary_for_context,
            )
    except Exception as e:
        print(f"[API] Context update error: {e}")

    response = {
        "summary": summary,
        "results": results_payload,
        "query_stats": stats_payload,
        "final_dsl": final_dsl if 'final_dsl' in locals() else dsl_query,
        "strategy": strategy if 'strategy' in locals() else "original",
        "repro_curl": repro_curl,
        "session_id": session_id,
    }
    return JSONResponse(content=response)


@app.post("/api/query_raw")
def handle_query_raw(request: RawQueryRequest) -> JSONResponse:
    """Execute a raw OpenSearch DSL query without NLP."""
    dsl_query = request.dsl
    print("[API] Raw query received. DSL:")
    try:
        print(json.dumps(dsl_query, indent=2))
    except Exception:
        print(str(dsl_query))

    status = siem.get_connection_status()
    print(f"[API] OpenSearch connection status: {status}")

    try:
        results, stats = siem.query(dsl_query)
        print(f"[API] Raw query executed. hits={stats.total_hits} time_ms={stats.query_time_ms} indices={stats.indices_searched}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SIEM raw query failed: {e}")

    results_payload = [r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in results]
    stats_payload = stats.model_dump() if hasattr(stats, "model_dump") else stats.dict()

    response = {
        "summary": f"Found {len(results_payload)} results.",
        "results": results_payload,
        "query_stats": stats_payload,
    }
    return JSONResponse(content=response)


@app.post("/api/context/clear")
def clear_context(request: QueryRequest) -> JSONResponse:
    session_id = request.session_id or os.getenv("DEFAULT_SESSION_ID", "default-session")
    cleared = context_manager.clear_context(session_id)
    return JSONResponse(content={"session_id": session_id, "cleared": cleared})


@app.get("/api/context/summary")
def context_summary(session_id: str) -> JSONResponse:
    summary = context_manager.get_session_summary(session_id)
    return JSONResponse(content=summary)


def _build_report_from_results(user_question: str, results: list[LogResult], include_charts: bool) -> dict:
    """Aggregate results and construct a narrative and chart data."""
    # Simple aggregations
    total = len(results)
    by_rule: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    hourly: dict[str, int] = {}

    for r in results:
        rule_desc = (r.rule_description or "Unknown").strip()
        by_rule[rule_desc] = by_rule.get(rule_desc, 0) + 1
        agent = (r.source_system or "unknown").strip()
        by_agent[agent] = by_agent.get(agent, 0) + 1
        # bucket by hour for a simple timeline
        try:
            ts = r.timestamp
            hour_key = ts[:13]  # YYYY-MM-DDTHH
            hourly[hour_key] = min(10_000, hourly.get(hour_key, 0) + 1)
        except Exception:
            pass

    # Build charts
    charts: list[ChartData] = []
    if include_charts:
        top_rules = sorted(by_rule.items(), key=lambda x: x[1], reverse=True)[:10]
        charts.append(ChartData(
            chart_type="bar",
            title="Top Rule Descriptions",
            data=[{"label": k, "value": v} for k, v in top_rules],
            x_axis_label="Rule",
            y_axis_label="Count",
        ))
        top_agents = sorted(by_agent.items(), key=lambda x: x[1], reverse=True)[:10]
        charts.append(ChartData(
            chart_type="bar",
            title="Events by Agent",
            data=[{"label": k, "value": v} for k, v in top_agents],
            x_axis_label="Agent",
            y_axis_label="Count",
        ))
        timeline = sorted(hourly.items(), key=lambda x: x[0])
        charts.append(ChartData(
            chart_type="line",
            title="Events Over Time (hourly)",
            data=[{"x": k, "y": v} for k, v in timeline],
            x_axis_label="Hour",
            y_axis_label="Events",
        ))

    # Narrative summary (optionally LLM-enhanced)
    narrative = f"Report for: {user_question}. Total events analyzed: {total}. "
    if by_rule:
        top_rule, top_rule_count = max(by_rule.items(), key=lambda x: x[1])
        narrative += f"Most frequent rule: '{top_rule}' ({top_rule_count}). "
    if by_agent:
        top_agent, top_agent_count = max(by_agent.items(), key=lambda x: x[1])
        narrative += f"Top agent: '{top_agent}' ({top_agent_count}). "

    try:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if api_key and total > 0:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, convert_system_message_to_human=True)
            sample = [r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in results[:20]]
            prompt = (
                "Generate a concise executive summary (4-6 sentences) for this SIEM report.\n"
                f"User request: {user_question}\n"
                f"Stats: total={total}, rules={len(by_rule)}, agents={len(by_agent)}\n"
                f"Sample events: {json.dumps(sample)[:3000]}"
            )
            resp = llm.invoke(prompt)
            llm_text = getattr(resp, "content", None)
            if isinstance(llm_text, str) and len(llm_text) > 0:
                narrative = llm_text
    except Exception:
        pass

    # Key findings (top items)
    key_findings = []
    for k, v in sorted(by_rule.items(), key=lambda x: x[1], reverse=True)[:3]:
        key_findings.append(f"Rule '{k}' occurred {v} times")
    for k, v in sorted(by_agent.items(), key=lambda x: x[1], reverse=True)[:2]:
        key_findings.append(f"Agent '{k}' generated {v} events")

    return {"narrative": narrative, "charts": charts, "key_findings": key_findings}


@app.post("/api/report")
def generate_report_from_natural_language(request: NLReportRequest) -> JSONResponse:
    """Generate a report from a natural language instruction."""
    user_question = request.question.strip()
    if not user_question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    # Build context text
    session_id = request.session_id or os.getenv("DEFAULT_SESSION_ID", "default-session")
    relevant_snippets = []
    active_filter_ctx = {}
    ctx = None
    if session_id:
        try:
            ctx = context_manager.get_context(session_id)
            if ctx and ctx.history:
                for entry in ctx.history[-3:]:
                    relevant_snippets.append(f"Prev: '{entry.query}' -> results={entry.result_count}")
                active_filter_ctx = ctx.active_filters or {}
        except Exception as e:
            print(f"[API][report] Context fetch error: {e}")

    conversation_context_text = "\n".join(relevant_snippets) if relevant_snippets else ""
    active_filter_context_text = json.dumps(active_filter_ctx) if active_filter_ctx else ""

    # Generate DSL via NLP
    dsl_query = generate_dsl_query(
        user_question,
        conversation_context=conversation_context_text,
        active_filter_context=active_filter_context_text,
    )
    if not dsl_query:
        raise HTTPException(status_code=422, detail="Failed to generate DSL for report")

    # Ensure sufficient size for aggregation (but keep reasonable cap)
    try:
        if "size" not in dsl_query:
            dsl_query["size"] = min(max(request.max_results, 100), 5000)
        else:
            dsl_query["size"] = min(dsl_query["size"], 5000)
    except Exception:
        dsl_query["size"] = 1000

    # Execute search
    try:
        results, stats = siem.query(dsl_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SIEM report query failed: {e}")

    # Build report artifacts
    agg = _build_report_from_results(user_question, results, include_charts=request.include_charts)
    narrative = agg["narrative"]
    charts = agg["charts"]
    key_findings = agg["key_findings"]

    response = {
        "report_title": user_question,
        "executive_summary": narrative,
        "detailed_analysis": "",  # can be expanded later
        "charts": [c.model_dump() if hasattr(c, "model_dump") else c for c in charts],
        "key_findings": key_findings,
        "recommendations": [],
        "data_sources": stats.indices_searched if hasattr(stats, "indices_searched") else [],
        "generation_timestamp": datetime.now().isoformat(),
        "session_id": session_id,
    }
    return JSONResponse(content=response)

# Optional: mount static if needed
# from fastapi.staticfiles import StaticFiles
# app.mount("/", StaticFiles(directory="static", html=True), name="static")