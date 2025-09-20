# SIEM AI Agent — NLP Brain

This module turns natural language questions into Elasticsearch DSL queries for the `wazuh-alerts-*` index using Google Gemini via LangChain.

## Setup

1. Create/activate a virtual environment (already present here as `venv`).
2. Install dependencies (already installed in this workspace). If needed, use `requirements.txt`.
3. Set your Google API key in a `.env` file at project root:

```
GOOGLE_API_KEY=your-real-api-key
```

## Run a quick test

Run `nlp_brain.py` to generate sample queries. If the API key is missing or a placeholder, the script safely skips calls and prints a failure message for each sample.

## File overview

- `nlp_brain.py` — Contains the master prompt and the `generate_dsl_query(question)` function.
- `.env` — Place your `GOOGLE_API_KEY` here (excluded by `.gitignore`).
- `requirements.txt` — Minimal dependencies for reproducibility.
- `.gitignore` — Keeps venv and secrets out of version control.

## Notes

- When Person A provides the authoritative `wazuh-alerts-*` index schema, update the prompt’s schema section to improve accuracy.
