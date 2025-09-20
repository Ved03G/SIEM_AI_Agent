#!/usr/bin/env python3
"""
Test Wazuh Elasticsearch connection
"""

import os
import sys
from pathlib import Path

# Add project root to path and load .env from correct location
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(Path(__file__).parent))

# Load environment variables from project root
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from siem_connector import SIEMConnector
from config import Settings

def test_wazuh_connection():
    """Test connection to Wazuh server"""
    print("🧪 Testing Wazuh Elasticsearch Connection")
    print("=" * 50)
    
    # Load settings
    settings = Settings()
    print(f"📋 Configuration:")
    print(f"   Host: {settings.elasticsearch_host}")
    print(f"   Username: {settings.elasticsearch_username}")
    print(f"   Password: {'*' * len(settings.elasticsearch_password) if settings.elasticsearch_password else 'None'}")
    print(f"   Verify Certs: {settings.elasticsearch_verify_certs}")
    print()
    
    # Test connection
    connector = SIEMConnector(use_mock_data=False)
    
    if connector.connection_status == "connected":
        print("✅ Connection successful!")
        
        # Test a simple query
        print("\n🔍 Testing simple query...")
        test_query = {
            "size": 5,
            "query": {"match_all": {}},
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        try:
            results, stats = connector.query(test_query)
            print(f"📊 Query successful! Found {len(results)} results")
            print(f"⏱️  Query time: {stats.query_time_ms}ms")
            
            if results:
                print("\n📋 Sample result:")
                sample = results[0]
                print(f"   Timestamp: {sample.timestamp}")
                print(f"   Description: {sample.rule_description}")
                print(f"   Severity: {sample.severity}")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            
    else:
        print("❌ Connection failed - falling back to mock data")
        print("💡 Check your Wazuh server credentials and network connectivity")
    
    print("\n" + "=" * 50)
    print("🏁 Test complete")

if __name__ == "__main__":
    test_wazuh_connection()