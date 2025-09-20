# server/visualization_service.py
"""
Visualization service for generating impressive charts and reports.
Creates matplotlib and plotly visualizations for hackathon demo impact.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import io
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict


class VisualizationService:
    """Creates stunning visualizations from SIEM data for hackathon demos"""
    
    def __init__(self):
        # Set up matplotlib styling for professional look
        plt.style.use('seaborn-v0_8')
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    
    def generate_security_dashboard(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive security dashboard with multiple charts"""
        print("📊 Generating security dashboard...")
        
        if not events:
            return {"error": "No data available for visualization"}
        
        # Convert to DataFrame for easier analysis
        df = self._events_to_dataframe(events)
        
        dashboard = {
            "summary_stats": self._generate_summary_stats(df),
            "charts": {
                "timeline": self._create_events_timeline(df),
                "severity_distribution": self._create_severity_chart(df),
                "top_attackers": self._create_top_attackers_chart(df),
                "attack_types": self._create_attack_types_chart(df),
                "geo_map": self._create_geographic_map(df),
                "hourly_patterns": self._create_hourly_patterns(df)
            },
            "insights": self._generate_insights(df)
        }
        
        print("✅ Dashboard generated successfully")
        return dashboard
    
    def _events_to_dataframe(self, events: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert SIEM events to pandas DataFrame"""
        data = []
        
        for event in events:
            try:
                timestamp = pd.to_datetime(event.get('timestamp', event.get('@timestamp')))
                rule = event.get('rule', {})
                data_field = event.get('data', {})
                geo = event.get('GeoLocation', {})
                
                data.append({
                    'timestamp': timestamp,
                    'rule_id': rule.get('id'),
                    'rule_level': int(rule.get('level', 1)),
                    'rule_description': rule.get('description', 'Unknown'),
                    'rule_groups': rule.get('groups', []),
                    'src_ip': data_field.get('srcip', ''),
                    'dst_ip': data_field.get('dstip', ''),
                    'src_user': data_field.get('srcuser', ''),
                    'country': geo.get('country_name', 'Unknown'),
                    'country_code': geo.get('country_code2', ''),
                    'message': event.get('message', ''),
                    'agent_name': event.get('agent', {}).get('name', 'Unknown')
                })
            except Exception as e:
                print(f"Warning: Error processing event: {e}")
                continue
        
        return pd.DataFrame(data)
    
    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate key summary statistics"""
        total_events = len(df)
        critical_events = len(df[df['rule_level'] >= 10])
        high_events = len(df[df['rule_level'] >= 8])
        unique_ips = df['src_ip'].nunique()
        unique_countries = df['country'].nunique()
        
        return {
            "total_events": total_events,
            "critical_alerts": critical_events,
            "high_severity": high_events,
            "unique_source_ips": unique_ips,
            "countries_involved": unique_countries,
            "time_range": {
                "start": df['timestamp'].min().isoformat() if not df.empty else None,
                "end": df['timestamp'].max().isoformat() if not df.empty else None
            }
        }
    
    def _create_events_timeline(self, df: pd.DataFrame) -> str:
        """Create interactive timeline of security events"""
        if df.empty:
            return ""
        
        # Group by hour and severity
        df['hour'] = df['timestamp'].dt.floor('H')
        timeline_data = df.groupby(['hour', 'rule_level']).size().reset_index(name='count')
        
        fig = px.line(timeline_data, x='hour', y='count', color='rule_level',
                     title='Security Events Timeline',
                     labels={'hour': 'Time', 'count': 'Number of Events', 'rule_level': 'Severity Level'})
        
        fig.update_layout(
            height=400,
            xaxis_title="Time",
            yaxis_title="Number of Events",
            legend_title="Severity Level",
            template="plotly_dark"
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="timeline_chart")
    
    def _create_severity_chart(self, df: pd.DataFrame) -> str:
        """Create severity distribution pie chart"""
        if df.empty:
            return ""
        
        severity_counts = df['rule_level'].value_counts().sort_index()
        
        # Group into categories
        categories = {
            'Low (1-3)': severity_counts[severity_counts.index <= 3].sum(),
            'Medium (4-6)': severity_counts[(severity_counts.index > 3) & (severity_counts.index <= 6)].sum(),
            'High (7-9)': severity_counts[(severity_counts.index > 6) & (severity_counts.index <= 9)].sum(),
            'Critical (10+)': severity_counts[severity_counts.index >= 10].sum()
        }
        
        fig = px.pie(values=list(categories.values()), names=list(categories.keys()),
                    title='Alert Severity Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3)
        
        fig.update_layout(height=400, template="plotly_dark")
        return fig.to_html(include_plotlyjs='cdn', div_id="severity_chart")
    
    def _create_top_attackers_chart(self, df: pd.DataFrame) -> str:
        """Create top attacking IPs bar chart"""
        if df.empty:
            return ""
        
        # Filter for external IPs and high severity events
        external_df = df[~df['src_ip'].str.startswith('192.168.') & (df['rule_level'] >= 6)]
        top_attackers = external_df['src_ip'].value_counts().head(10)
        
        if top_attackers.empty:
            # Fallback to all IPs if no external ones
            top_attackers = df['src_ip'].value_counts().head(10)
        
        fig = px.bar(x=top_attackers.index, y=top_attackers.values,
                    title='Top 10 Source IPs by Alert Count',
                    labels={'x': 'Source IP', 'y': 'Number of Alerts'},
                    color=top_attackers.values,
                    color_continuous_scale='Reds')
        
        fig.update_layout(
            height=400,
            xaxis_title="Source IP",
            yaxis_title="Number of Alerts",
            template="plotly_dark"
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="attackers_chart")
    
    def _create_attack_types_chart(self, df: pd.DataFrame) -> str:
        """Create attack types distribution"""
        if df.empty:
            return ""
        
        # Analyze rule descriptions for attack patterns
        attack_patterns = defaultdict(int)
        for desc in df['rule_description']:
            desc_lower = desc.lower()
            if 'failed' in desc_lower or 'failure' in desc_lower:
                attack_patterns['Authentication Failures'] += 1
            elif 'malware' in desc_lower:
                attack_patterns['Malware Detection'] += 1
            elif 'brute' in desc_lower:
                attack_patterns['Brute Force Attacks'] += 1
            elif 'suspicious' in desc_lower:
                attack_patterns['Suspicious Activity'] += 1
            elif 'network' in desc_lower:
                attack_patterns['Network Intrusions'] += 1
            else:
                attack_patterns['Other Security Events'] += 1
        
        fig = px.bar(x=list(attack_patterns.keys()), y=list(attack_patterns.values()),
                    title='Security Event Types Distribution',
                    color=list(attack_patterns.values()),
                    color_continuous_scale='Viridis')
        
        fig.update_layout(
            height=400,
            xaxis_title="Event Type",
            yaxis_title="Count",
            template="plotly_dark"
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="attack_types_chart")
    
    def _create_geographic_map(self, df: pd.DataFrame) -> str:
        """Create world map of attack sources"""
        if df.empty:
            return ""
        
        # Count events by country
        country_counts = df[df['country'] != 'Unknown']['country'].value_counts()
        
        if country_counts.empty:
            return "<p>No geographic data available</p>"
        
        fig = px.choropleth(
            locations=country_counts.index,
            z=country_counts.values,
            locationmode='country names',
            title='Global Distribution of Security Events',
            color_continuous_scale='Reds',
            labels={'z': 'Number of Events'}
        )
        
        fig.update_layout(
            height=500,
            geo=dict(showframe=False, showcoastlines=True),
            template="plotly_dark"
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="geo_map")
    
    def _create_hourly_patterns(self, df: pd.DataFrame) -> str:
        """Create hourly attack patterns heatmap"""
        if df.empty:
            return ""
        
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Create pivot table for heatmap
        heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        pivot_data = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_data = pivot_data.reindex(day_order)
        
        fig = px.imshow(pivot_data,
                       title='Attack Patterns by Day and Hour',
                       labels={'x': 'Hour of Day', 'y': 'Day of Week', 'color': 'Number of Events'},
                       color_continuous_scale='Reds')
        
        fig.update_layout(height=400, template="plotly_dark")
        return fig.to_html(include_plotlyjs='cdn', div_id="hourly_patterns")
    
    def _generate_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate AI-like insights from the data"""
        insights = []
        
        if df.empty:
            return ["No data available for analysis"]
        
        # Critical events insight
        critical_count = len(df[df['rule_level'] >= 10])
        if critical_count > 0:
            insights.append(f"🚨 {critical_count} critical security events detected requiring immediate attention")
        
        # Top attacker insight
        top_attacker = df['src_ip'].value_counts().head(1)
        if not top_attacker.empty:
            insights.append(f"🎯 Most active source IP: {top_attacker.index[0]} with {top_attacker.values[0]} events")
        
        # Time pattern insight
        peak_hour = df['timestamp'].dt.hour.value_counts().idxmax()
        insights.append(f"⏰ Peak attack time: {peak_hour}:00 hours")
        
        # Geographic insight
        if 'country' in df.columns:
            top_country = df[df['country'] != 'Unknown']['country'].value_counts().head(1)
            if not top_country.empty:
                insights.append(f"🌍 Most attacks originate from: {top_country.index[0]}")
        
        # Trend insight
        if len(df) > 10:
            recent_trend = len(df[df['timestamp'] > df['timestamp'].max() - timedelta(hours=24)])
            insights.append(f"📈 {recent_trend} events detected in the last 24 hours")
        
        return insights


# Global visualization service instance
viz_service = VisualizationService()


def create_security_report(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Main function to create a comprehensive security report with visuals"""
    return viz_service.generate_security_dashboard(events)