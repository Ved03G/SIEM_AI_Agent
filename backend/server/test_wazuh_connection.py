#!/usr/bin/env python3
"""
Test Wazuh OpenSearch connection (no mock fallback)
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path and load .env from correct location
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(Path(__file__).parent))

# Load environment variables from project root
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from opensearchpy import OpenSearch

def test_wazuh_connection():
    """Test direct connection to Wazuh OpenSearch (no mock)."""
    print("🧪 Testing Wazuh OpenSearch Connection (no mock)")
    print("=" * 50)

    try:
        # Minimal client like simpe-test.py
        username = os.getenv("OPENSEARCH_USERNAME", "admin")
        password = os.getenv("OPENSEARCH_PASSWORD", "SecretPassword")
        client = OpenSearch(
            hosts=[{"host": "localhost", "port": 9200}],
            http_auth=(username, password),
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30
        )
        # Basic health check
        if not client.ping():
            raise RuntimeError("Ping to OpenSearch failed")

        info = client.info()
        print("✅ Connection successful!")
        print(f"📊 OpenSearch version: {info.get('version', {}).get('number', 'unknown')}")

        # Optional: run a precise sample query (Windows failed logon rule.id=60122)
        print("\n🔍 Running a sample failed logon query (rule.id=60122) against 'wazuh-alerts-*'...")
        test_query = {
            "size": 5,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "track_total_hits": True,
            "query": {
                "term": {"rule.id": 60122}
            }
        }
        resp = client.search(index="wazuh-alerts-*", body=test_query, request_timeout=30)
        total_hits = resp.get("hits", {}).get("total", {})
        total = total_hits.get("value", 0) if isinstance(total_hits, dict) else total_hits
        print(f"📈 Query OK. Hits: {total}")

    except Exception as e:
        print("❌ Connection or query failed.")
        print(f"   Error:{e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🏁 Test complete")

if __name__ == "__main__":
    test_wazuh_connection()