import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load environment variables from .env file
load_dotenv()

# This is the master prompt. It teaches the AI how to behave and gives it examples.
# The quality of your entire project depends on the quality of this prompt.
MASTER_PROMPT_TEMPLATE = """
You are an expert cybersecurity analyst who translates human language into precise Elasticsearch DSL queries for a Wazuh SIEM.
Your goal is to construct a JSON query object to search the 'wazuh-alerts-*' index.
You must only respond with the raw JSON query object and nothing else. Do not add any extra text, explanations, or markdown formatting like ```json.

Here is the relevant index schema. Use these exact field names:
- @timestamp: The timestamp of the event. (Use date math like "now-1h" for time ranges).
- agent.name: The name of the host or agent.
- rule.id: The specific ID of the Wazuh rule that was triggered.
- rule.description: A text description of the alert.
- rule.groups: An array of rule categories, e.g., 'authentication', 'pci_dss', 'ossec'.
- rule.level: The severity level of the alert (a number from 0-15).
- data.srcip: The source IP address of the event traffic.
- data.dstip: The destination IP address of the event traffic.

Guidance for constructing DSL:
- Always set "track_total_hits": true for accurate counts.
- Unless the user specifies otherwise, sort by {{"@timestamp": {{"order": "desc"}}}}.
- If the user asks for "last N", set "size" to N; otherwise omit size (or leave to defaults) unless clearly implied.
- Prefer precise filters: use term queries on keyword-like fields and specific rule IDs when clearly identifiable (for example, some Windows failed logon events map to rule.id 60122). Do not hardcode rule IDs unless the user intent explicitly implies a known mapping.
- For date ranges like "between 2025-09-10 and 2025-09-20", use a range on @timestamp with "gte" and "lte" in ISO format (Z timezone), e.g., "2025-09-10T00:00:00Z" to "2025-09-20T23:59:59Z".
- Avoid inefficient wildcards; use match_phrase or terms/term appropriately.

Here are high-quality examples. Prioritize using rule.id when a specific event type is requested.

Human: what were the last 5 failed logins?
AI:
{{
  "size": 5,
  "sort": [{{ "@timestamp": {{ "order": "desc" }} }}],
  "track_total_hits": true,
  "query": {{
    "term": {{ "rule.id": 60122 }}
  }}
}}
Human: show me the last 5 successful logins
AI:
{{
  "size": 5,
  "sort": [{{ "@timestamp": {{ "order": "desc" }} }}],
  "track_total_hits": true,
  "query": {{
    "term": {{
      "rule.id": "60106"
    }}
  }}
}}

Human: show failed logins between 2025-09-10 and 2025-09-20
AI:
{{
  "sort": [{{ "@timestamp": {{ "order": "desc" }} }}],
  "track_total_hits": true,
  "query": {{
    "bool": {{
      "must": [
        {{ "term": {{ "rule.id": 60122 }} }},
        {{ "range": {{ "@timestamp": {{ "gte": "2025-09-10T00:00:00Z", "lte": "2025-09-20T23:59:59Z" }} }} }}
      ]
    }}
  }}
}}

Human: show me high severity alerts from the last hour
AI:
{{
  "query": {{
    "bool": {{
      "must": [
        {{
          "range": {{
            "rule.level": {{ "gte": 10 }}
          }}
        }},
        {{
          "range": {{
            "@timestamp": {{ "gte": "now-1h" }}
          }}
        }}
      ]
    }}
  }}
}}

Human: find network connections from 10.0.2.15 but exclude dns traffic
AI:
{{
  "query": {{
    "bool": {{
      "must": [
        {{ "term": {{ "data.srcip": "10.0.2.15" }} }}
      ],
      "must_not": [
        {{ "match": {{ "rule.description": "DNS" }} }}
      ]
    }}
  }}
}}

Human: search for any alerts related to malware
AI:
{{
  "query": {{
    "match": {{
      "rule.description": "malware"
    }}
  }}
}}

Human: show events for malicious IP 10.0.2.15 in the last 24 hours
AI:
{{
  "sort": [{{ "@timestamp": {{ "order": "desc" }} }}],
  "track_total_hits": true,
  "query": {{
    "bool": {{
      "must": [
        {{ "term": {{ "data.srcip": "10.0.2.15" }} }},
        {{ "range": {{ "@timestamp": {{ "gte": "now-24h" }} }} }}
      ]
    }}
  }}
}}

Conversation context (use these to refine the current question; consider them as prior constraints and preferences unless explicitly overridden by the user):
{conversation_context}

Active filters from the current session context (apply these unless the user contradicts them):
{active_filter_context}

Human: {user_question}
AI:
"""

def generate_dsl_query(question: str, conversation_context: str = "", active_filter_context: str = "") -> dict:
  """
  Takes a user's natural language question and returns a valid OpenSearch DSL query as a dictionary.
  Returns an empty dictionary if the generation fails or the output is not valid JSON.
  Also logs the filled prompt, raw model response, and parsed DSL for observability.
  """
  api_key = os.getenv("GOOGLE_API_KEY", "").strip()
  # Optional: Hardcoded preset only when explicitly forced (for testing)
  if os.getenv("NLP_FORCE_PRESET", "").strip().lower() in ("1", "true", "yes"):
    preset = {
      "size": 5,
      "sort": [{"@timestamp": {"order": "desc"}}],
      "track_total_hits": True,
      "query": {"term": {"rule.id": 60122}}
    }
    print("[NLP] Using FORCED preset DSL (override enabled)")
    try:
      print("[NLP] Preset DSL:\n" + json.dumps(preset, indent=2))
    except Exception:
      pass
    return preset

  if not api_key:
    # Avoid calling the API without a valid key
    print("[NLP] No GOOGLE_API_KEY set; cannot call model. Returning empty DSL.")
    return {}

  try:
    # Initialize the language model with a supported Gemini 1.5 model
    llm = ChatGoogleGenerativeAI(
      model="gemini-1.5-flash",
      temperature=0.1,
      convert_system_message_to_human=True,
    )

    # Create the prompt from the template
    prompt = PromptTemplate(
      template=MASTER_PROMPT_TEMPLATE,
      input_variables=["user_question", "conversation_context", "active_filter_context"],
    ) 

    # Log question and the filled prompt for transparency
    print("[NLP] Received question:", question)
    filled_prompt = prompt.format(
      user_question=question,
      conversation_context=conversation_context or "(none)",
      active_filter_context=active_filter_context or "(none)",
    )
    print("[NLP] Filled prompt (truncated to 2,000 chars):\n" + filled_prompt[:2000])

    # Create a simple chain
    chain = prompt | llm

    # Invoke the chain with the user's question
    response = chain.invoke({
      "user_question": question,
      "conversation_context": conversation_context or "",
      "active_filter_context": active_filter_context or "",
    })

    # The response.content should be a JSON string; parse with a safe fallback
    raw = (getattr(response, "content", "") or "").strip()
    print("[NLP] Raw model response (truncated to 2,000 chars):\n" + raw[:2000])
    try:
      parsed = json.loads(raw)
      parsed = _postprocess_dsl(parsed, question)
      try:
        print("[NLP] Parsed DSL:\n" + json.dumps(parsed, indent=2)[:2000])
      except Exception:
        pass
      return parsed
    except Exception:
      # Try to extract the first JSON object from any surrounding text
      start = raw.find("{")
      end = raw.rfind("}")
      if start != -1 and end != -1 and end > start:
        try:
          parsed = json.loads(raw[start : end + 1])
          parsed = _postprocess_dsl(parsed, question)
          try:
            print("[NLP] Parsed DSL (from extracted JSON):\n" + json.dumps(parsed, indent=2)[:2000])
          except Exception:
            pass
          return parsed
        except Exception:
          return {}
      return {}
  except Exception as e:
    print(f"[NLP] Unexpected error: {e}")
    return _fallback_from_question(question)


def _postprocess_dsl(dsl: dict, question: str) -> dict:
  """Enforce small best-practice defaults in the returned DSL.
  - Ensure track_total_hits: true
  - Ensure sort by @timestamp desc if not provided
  - If user asked for "last N" and no size provided, set size=N; otherwise leave as-is
  """
  try:
    d = dict(dsl) if isinstance(dsl, dict) else {}
    # track_total_hits
    if "track_total_hits" not in d:
      d["track_total_hits"] = True
    # sort default
    if "sort" not in d or not d.get("sort"):
      d["sort"] = [{"@timestamp": {"order": "desc"}}]
    # size from "last N"
    if "size" not in d and isinstance(question, str):
      import re
      m = re.search(r"last\s+(\d+)", question.lower())
      if m:
        try:
          d["size"] = int(m.group(1))
        except Exception:
          pass
    return d
  except Exception:
    return dsl


def _fallback_from_question(question: str) -> dict:
  """Generate a minimal but valid DSL when the LLM fails. Best-effort.
  Supports patterns: "last N", date range "between A and B", keywords like failed login, and IP filters.
  """
  try:
    import re
    q = (question or "").lower()
    dsl: dict = {
      "track_total_hits": True,
      "sort": [{"@timestamp": {"order": "desc"}}],
      "query": {"match_all": {}}
    }

    # last N
    m = re.search(r"last\s+(\d+)", q)
    if m:
      try:
        dsl["size"] = int(m.group(1))
      except Exception:
        pass

    # between YYYY-MM-DD and YYYY-MM-DD
    m = re.search(r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})", q)
    if m:
      start, end = m.group(1), m.group(2)
      time_filter = {"range": {"@timestamp": {"gte": f"{start}T00:00:00Z", "lte": f"{end}T23:59:59Z"}}}
    else:
      time_filter = None

    # IP address
    m = re.search(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b", q)
    ip_term = {"term": {"data.srcip": m.group(1)}} if m else None

    # failed login keyword
    if "failed login" in q or "authentication failure" in q:
      failed_clause = {"term": {"rule.id": 60122}}
    else:
      failed_clause = None

    clauses = []
    if failed_clause:
      clauses.append(failed_clause)
    if ip_term:
      clauses.append(ip_term)
    if time_filter:
      clauses.append(time_filter)

    if clauses:
      dsl["query"] = {"bool": {"must": clauses}}

    return dsl
  except Exception:
    return {"track_total_hits": True, "sort": [{"@timestamp": {"order": "desc"}}], "query": {"match_all": {}}}


# This block allows you to test the file directly
if __name__ == "__main__":
    print("--- Running NLP Brain Test ---")
    
    test_questions = [
        "show me the last 10 ssh logins",
        "any alerts from agent win-server-01 in the past 6 hours?",
        "find all activity from IP 10.0.2.15 but not authentication",
    ]
    
    for q in test_questions:
        print(f"\n[Human]: {q}")
        dsl_query = generate_dsl_query(q)
        
        if dsl_query:
            print("[AI Generated DSL]:")
            # Pretty-print the JSON
            print(json.dumps(dsl_query, indent=2))
        else:
            print("[AI]: Failed to generate a valid query.")
    
    print("\n--- Test Complete ---")