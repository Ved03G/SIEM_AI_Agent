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
You are an expert cybersecurity analyst who translates human language into precise OpenSearch DSL queries.
Your goal is to construct a JSON query to search the 'wazuh-alerts-*' index.
You must only respond with the JSON query object and nothing else. Do not add any extra text or explanations.

Here is the relevant wazuh-alerts-* index schema (curated from Person A). Use these exact field names and prefer exact/typed queries:
- @timestamp (date): event time
- agent.id (keyword), agent.ip (keyword), agent.name (keyword)
- rule.id (keyword), rule.level (long), rule.description (keyword), rule.groups (keyword),
  rule.mitre.id (keyword), rule.mitre.tactic (keyword), rule.mitre.technique (keyword)
- data.srcip (keyword), data.dstip (keyword), data.srcport (keyword), data.dstport (keyword),
  data.srcuser (keyword), data.dstuser (keyword)
- message (text), full_log (text)
- manager.name (keyword), location (keyword), host (keyword), program_name (keyword),
  predecoder.hostname (keyword), predecoder.program_name (keyword)
- GeoLocation.location (geo_point), GeoLocation.ip (keyword)
- data.aws.srcaddr (ip), data.aws.dstaddr (ip), data.aws.source_ip_address (ip),
  data.aws.region (keyword), data.aws.service.count (long)
- gcp.jsonPayload.* (keywords), office365.ClientIP (keyword)
- os.hostname (keyword), os.name (keyword)
- timestamp (date) [alternate field]

Query construction rules:
- Use term for keyword fields; use match or match_phrase for text fields like message/full_log.
- Use range for date/long fields (e.g., @timestamp, rule.level). Use date math like "now-1d/d" when asked.
- For IP fields (type ip or keyword containing IP), use term unless wildcards are requested.
- For negation, use bool.must_not with appropriate clauses.
- For OR logic, use bool.should with minimum_should_match: 1.
- If the user asks for "last N", set size to N and sort by @timestamp desc.
- Only return the JSON query object. No markdown and no explanations.

Here are some high-quality examples aligned to types:

Human: What were the last 5 authentication failures?
AI:
{{
  "size": 5,
  "query": {{
    "bool": {{
      "must": [
        {{ "term": {{ "rule.groups": "authentication" }} }}
      ],
      "should": [
        {{ "match_phrase": {{ "message": "failed" }} }},
        {{ "match_phrase": {{ "message": "failure" }} }},
        {{ "match_phrase": {{ "rule.description": "failed" }} }},
        {{ "match_phrase": {{ "rule.description": "failure" }} }}
      ],
      "minimum_should_match": 1
    }}
  }},
  "sort": [{{ "@timestamp": {{ "order": "desc" }} }}]
}}

Human: Show me all alerts from the agent named 'prod-web-01' yesterday.
AI:
{{
  "query": {{
    "bool": {{
      "must": [
        {{ "term": {{ "agent.name": "prod-web-01" }} }},
        {{ "range": {{ "@timestamp": {{ "gte": "now-1d/d", "lt": "now/d" }} }} }}
      ]
    }}
  }}
}}

Human: Find suspicious activity from the IP 192.168.1.105, but exclude logins.
AI:
{{
  "query": {{
    "bool": {{
      "must": [
        {{ "term": {{ "data.srcip": "192.168.1.105" }} }}
      ],
      "must_not": [
        {{ "term": {{ "rule.groups": "authentication" }} }}
      ]
    }}
  }}
}}

Human: Show me high severity alerts with a rule level greater than 10 in the last hour.
AI:
{{
  "query": {{
  "bool": {{
    "must": [
    {{ "range": {{ "rule.level": {{ "gte": 10 }} }} }},
    {{ "range": {{ "@timestamp": {{ "gte": "now-1h" }} }} }}
    ]
  }}
  }}
}}

Human: {user_question}
AI:
"""

def generate_dsl_query(question: str) -> dict:
  """
  Takes a user's natural language question and returns a valid OpenSearch DSL query as a dictionary.
  Returns an empty dictionary if the generation fails or the output is not valid JSON.
  Also logs the filled prompt, raw model response, and parsed DSL for observability.
  """
  api_key = os.getenv("GOOGLE_API_KEY", "").strip()
  if not api_key:
    # Avoid calling the API without a valid key
    return {}

  try:
    # Initialize the language model with a supported Gemini 1.5 model
    llm = ChatGoogleGenerativeAI(
      model="gemini-1.5-flash",
      temperature=0.1,
      convert_system_message_to_human=True,
    )

    # Create the prompt from the template
    prompt = PromptTemplate(template=MASTER_PROMPT_TEMPLATE, input_variables=["user_question"]) 

    # Log question and the filled prompt for transparency
    print("[NLP] Received question:", question)
    filled_prompt = prompt.format(user_question=question)
    print("[NLP] Filled prompt (truncated to 2,000 chars):\n" + filled_prompt[:2000])

    # Create a simple chain
    chain = prompt | llm

    # Invoke the chain with the user's question
    response = chain.invoke({"user_question": question})

    # The response.content should be a JSON string; parse with a safe fallback
    raw = (getattr(response, "content", "") or "").strip()
    print("[NLP] Raw model response (truncated to 2,000 chars):\n" + raw[:2000])
    try:
      parsed = json.loads(raw)
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
    return {}


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