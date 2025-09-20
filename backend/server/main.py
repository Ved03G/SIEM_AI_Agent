import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from nlp_brain import generate_dsl_query
from langchain_google_genai import ChatGoogleGenerativeAI
from models import QueryRequest, ApiResponse, LogResult, QueryStats, RawQueryRequest
from siem_connector import SIEMConnector

# Load environment variables (for GOOGLE_API_KEY, etc.)
load_dotenv()

# FastAPI app
app = FastAPI(title="SIEM AI Agent API", version="1.0.0")

# Initialize SIEM connector (will attempt connection; may use mock if not available)
siem = SIEMConnector(use_mock_data=False)


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
    dsl_query = generate_dsl_query(user_question)
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

    # 2) Execute the query via SIEM connector (OpenSearch or mock)
    try:
        results, stats = siem.query(dsl_query)
        print(f"[API] Query executed. hits={stats.total_hits} time_ms={stats.query_time_ms} indices={stats.indices_searched}")
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

    response = {
        "summary": summary,
        "results": results_payload,
        "query_stats": stats_payload,
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

# Optional: mount static if needed
# from fastapi.staticfiles import StaticFiles
# app.mount("/", StaticFiles(directory="static", html=True), name="static")