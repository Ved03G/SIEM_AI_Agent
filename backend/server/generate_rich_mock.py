"""
Generate rich mock SIEM data for hackathon demo.
Creates 400+ realistic security events across 7 days with proper variety.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


def generate_realistic_mock_data() -> List[Dict[str, Any]]:
    """Generate 400+ realistic security events for hackathon demo"""
    
    events = []
    base_time = datetime.now() - timedelta(days=7)
    
    # IP pools for different scenarios
    internal_ips = [f"192.168.1.{i}" for i in range(10, 50)]
    external_ips = [
        "45.33.32.156", "185.220.100.240", "94.102.49.190", 
        "198.98.51.189", "163.172.68.61", "89.248.171.218",
        "103.224.182.251", "37.49.224.16", "91.121.89.202"
    ]
    suspicious_ips = [
        "185.220.101.43", "198.98.62.34", "89.248.165.123", 
        "103.224.146.78", "45.33.11.200"
    ]
    
    # User pools
    normal_users = ["alice.johnson", "bob.smith", "carol.davis", "dave.wilson", "eve.brown"]
    admin_users = ["admin", "root", "administrator", "sysadmin"]
    
    # Countries for geo data
    countries = [
        {"name": "United States", "code": "US", "coords": [39.8283, -98.5795]},
        {"name": "Russia", "code": "RU", "coords": [61.5240, 105.3188]},
        {"name": "China", "code": "CN", "coords": [35.8617, 104.1954]},
        {"name": "Germany", "code": "DE", "coords": [51.1657, 10.4515]},
        {"name": "France", "code": "FR", "coords": [46.6034, 1.8883]},
        {"name": "Brazil", "code": "BR", "coords": [-14.2350, -51.9253]}
    ]
    
    # Generate events for each day
    for day in range(7):
        current_day = base_time + timedelta(days=day)
        
        # Normal activity (60% of events)
        events.extend(_generate_normal_activity(current_day, internal_ips, normal_users, 35))
        
        # Authentication events (20% of events) 
        events.extend(_generate_auth_events(current_day, internal_ips + external_ips, 
                                          normal_users + admin_users, 12))
        
        # Suspicious activity (15% of events)
        events.extend(_generate_suspicious_activity(current_day, suspicious_ips + external_ips, 9))
        
        # Critical threats (5% of events)
        events.extend(_generate_critical_threats(current_day, suspicious_ips, 3))
    
    # Add geo location data
    for event in events:
        if event.get("data", {}).get("srcip") in external_ips + suspicious_ips:
            country = random.choice(countries)
            event["GeoLocation"] = {
                "country_name": country["name"],
                "country_code2": country["code"],
                "coordinates": country["coords"],
                "ip": event["data"]["srcip"]
            }
    
    # Sort by timestamp for realistic timeline
    events.sort(key=lambda x: x["timestamp"])
    
    print(f"✅ Generated {len(events)} realistic security events")
    return events


def _generate_normal_activity(base_time: datetime, ips: List[str], 
                             users: List[str], count: int) -> List[Dict[str, Any]]:
    """Generate normal system activity"""
    events = []
    
    for i in range(count):
        event_time = base_time + timedelta(
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        events.append({
            "timestamp": event_time.isoformat() + "Z",
            "@timestamp": event_time.isoformat() + "Z", 
            "agent": {
                "id": f"win-server-0{random.randint(1,3)}",
                "name": f"Windows-{random.randint(1,3)}",
                "ip": random.choice(ips)
            },
            "rule": {
                "id": random.choice(["5156", "4625", "4648", "4776"]),
                "level": random.randint(1, 5),
                "description": random.choice([
                    "Windows Logon", 
                    "Network connection established",
                    "Service started",
                    "User account accessed"
                ]),
                "groups": ["windows", "authentication"]
            },
            "data": {
                "srcip": random.choice(ips),
                "srcuser": random.choice(users),
                "action": "allowed"
            },
            "manager": {"name": "wazuh-manager"},
            "location": "EventChannel",
            "message": f"User {random.choice(users)} logged in successfully"
        })
    
    return events


def _generate_auth_events(base_time: datetime, ips: List[str], 
                         users: List[str], count: int) -> List[Dict[str, Any]]:
    """Generate authentication events (mix of success/failure)"""
    events = []
    
    for i in range(count):
        event_time = base_time + timedelta(
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        is_failed = random.random() < 0.3  # 30% failed logins
        
        events.append({
            "timestamp": event_time.isoformat() + "Z",
            "@timestamp": event_time.isoformat() + "Z",
            "agent": {
                "id": f"dc-{random.randint(1,2)}",
                "name": f"Domain-Controller-{random.randint(1,2)}",
                "ip": "192.168.1.10"
            },
            "rule": {
                "id": "4625" if is_failed else "4624",
                "level": 8 if is_failed else 3,
                "description": "An account failed to log on" if is_failed else "An account was successfully logged on",
                "groups": ["authentication", "authentication_failed" if is_failed else "authentication_success"]
            },
            "data": {
                "srcip": random.choice(ips),
                "srcuser": random.choice(users),
                "dstuser": random.choice(users),
                "win": {
                    "eventdata": {
                        "logonType": "3",
                        "status": "0xC000006D" if is_failed else "0x0"
                    }
                }
            },
            "manager": {"name": "wazuh-manager"},
            "location": "Security",
            "message": f"Failed login attempt for user {random.choice(users)}" if is_failed else f"Successful login for user {random.choice(users)}"
        })
    
    return events


def _generate_suspicious_activity(base_time: datetime, ips: List[str], count: int) -> List[Dict[str, Any]]:
    """Generate suspicious security events"""
    events = []
    
    suspicious_activities = [
        {
            "rule_id": "31151",
            "level": 8,
            "description": "Multiple failed login attempts",
            "groups": ["authentication_failures", "attacks"],
            "message": "Brute force attack detected"
        },
        {
            "rule_id": "40111", 
            "level": 9,
            "description": "Suspicious network connection",
            "groups": ["network", "attacks"],
            "message": "Connection to known malicious IP"
        },
        {
            "rule_id": "554",
            "level": 7,
            "description": "PowerShell execution detected",
            "groups": ["windows", "powershell"],
            "message": "Suspicious PowerShell command execution"
        }
    ]
    
    for i in range(count):
        event_time = base_time + timedelta(
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        activity = random.choice(suspicious_activities)
        
        events.append({
            "timestamp": event_time.isoformat() + "Z",
            "@timestamp": event_time.isoformat() + "Z",
            "agent": {
                "id": f"web-server-{random.randint(1,3)}",
                "name": f"WebServer-{random.randint(1,3)}",
                "ip": "192.168.1.20"
            },
            "rule": {
                "id": activity["rule_id"],
                "level": activity["level"],
                "description": activity["description"],
                "groups": activity["groups"]
            },
            "data": {
                "srcip": random.choice(ips),
                "dstip": "192.168.1.20",
                "srcport": str(random.randint(1024, 65535)),
                "dstport": "443"
            },
            "manager": {"name": "wazuh-manager"},
            "location": "IIS",
            "message": activity["message"]
        })
    
    return events


def _generate_critical_threats(base_time: datetime, ips: List[str], count: int) -> List[Dict[str, Any]]:
    """Generate critical security threats"""
    events = []
    
    critical_threats = [
        {
            "rule_id": "87105",
            "level": 12,
            "description": "Malware detected",
            "groups": ["malware", "critical"],
            "message": "Trojan.Win32.Agent detected in file system"
        },
        {
            "rule_id": "100002",
            "level": 15,
            "description": "Ransomware activity detected", 
            "groups": ["malware", "ransomware", "critical"],
            "message": "File encryption activity detected - possible ransomware"
        }
    ]
    
    for i in range(count):
        event_time = base_time + timedelta(
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        threat = random.choice(critical_threats)
        
        events.append({
            "timestamp": event_time.isoformat() + "Z",
            "@timestamp": event_time.isoformat() + "Z",
            "agent": {
                "id": f"endpoint-{random.randint(1,5)}",
                "name": f"Workstation-{random.randint(1,5)}",
                "ip": "192.168.1.100"
            },
            "rule": {
                "id": threat["rule_id"],
                "level": threat["level"],
                "description": threat["description"],
                "groups": threat["groups"]
            },
            "data": {
                "srcip": random.choice(ips),
                "process": "malware.exe",
                "hash": f"md5:{random.randint(100000, 999999)}"
            },
            "manager": {"name": "wazuh-manager"},
            "location": "Endpoint",
            "message": threat["message"]
        })
    
    return events


if __name__ == "__main__":
    # Generate and save mock data
    mock_data = generate_realistic_mock_data()
    
    with open("mock_siem_data_rich.json", "w") as f:
        json.dump(mock_data, f, indent=2)
    
    print(f"📄 Saved {len(mock_data)} events to mock_siem_data_rich.json")