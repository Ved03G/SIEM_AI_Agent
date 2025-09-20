#!/usr/bin/env python3
"""
Simple network connectivity test for Wazuh server
"""

import socket
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(InsecureRequestWarning)

def test_port_connectivity(host, port):
    """Test if a port is open on the host"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ Socket error: {e}")
        return False

def test_http_endpoint(url):
    """Test HTTP/HTTPS endpoint"""
    try:
        response = requests.get(url, timeout=10, verify=False)
        return response.status_code, response.text[:200] if hasattr(response, 'text') else "No response text"
    except Exception as e:
        return None, str(e)

def main():
    print("🌐 Testing Network Connectivity to Wazuh Server")
    print("=" * 50)
    
    host = "169.254.97.100"
    
    # Test common ports
    ports_to_test = [
        (9200, "Elasticsearch"),
        (9443, "Alternative Elasticsearch"),
        (443, "HTTPS"),
        (80, "HTTP"),
        (22, "SSH"),
        (55000, "Wazuh API")
    ]
    
    print(f"🎯 Testing connectivity to {host}")
    for port, service in ports_to_test:
        is_open = test_port_connectivity(host, port)
        status = "✅ OPEN" if is_open else "❌ CLOSED"
        print(f"   Port {port} ({service}): {status}")
    
    print("\n🌐 Testing HTTP/HTTPS endpoints")
    endpoints_to_test = [
        "https://169.254.97.100:9200",
        "http://169.254.97.100:9200",
        "https://169.254.97.100:9443",
        "https://169.254.97.100:55000"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🔗 Testing {endpoint}")
        status_code, response = test_http_endpoint(endpoint)
        if status_code:
            print(f"   Status: {status_code}")
            print(f"   Response: {response}")
        else:
            print(f"   Error: {response}")

if __name__ == "__main__":
    main()