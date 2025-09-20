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

Here are high-quality examples of how to translate questions. Prioritize using rule.id when a specific event type is requested.

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
  # Hardcoded presets for common queries (bypass LLM)
  ql = (question or "").lower()
  if (
      "authentication failure" in ql or
      "failed login" in ql or
      "failed logins" in ql or
      os.getenv("NLP_FORCE_PRESET", "").strip().lower() in ("1", "true", "yes")
  ):
    preset = {
      "size": 5,
      "sort": [{"@timestamp": {"order": "desc"}}],
      "track_total_hits": True,
      "query": {
        "term": {"rule.id": 60122}
      }
    }
    print("[NLP] Using hardcoded preset DSL for authentication failure / failed login")
    try:
      print("[NLP] Preset DSL:\n" + json.dumps(preset, indent=2))
    except Exception:
      pass
    return preset

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