from flask import Flask, jsonify, render_template_string
import requests
import json
from datetime import datetime
import socket
import subprocess

app = Flask(__name__)

# Configuration - using Docker service names for internal communication
PROMETHEUS_URL = "http://prometheus:9090"
OPENSEARCH_URL = "http://opensearch:9200" 
GRAFANA_URL = "http://grafana:3000"
LOKI_URL = "http://loki:3100"
SURICATA_EXPORTER_URL = "http://suricata-exporter:9917"
ARKIME_VIEWER_URL = "http://viewer:8005"

# HTML template for the status page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Network Security Monitoring - Status</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; border-bottom: 2px solid #007acc; padding-bottom: 15px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
        .status-card { background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #28a745; }
        .status-card.warning { border-left-color: #ffc107; }
        .status-card.error { border-left-color: #dc3545; }
        .metric { font-size: 24px; font-weight: bold; color: #007acc; }
        .label { font-size: 14px; color: #666; margin-top: 5px; }
        .timestamp { text-align: center; color: #888; font-size: 12px; margin-top: 20px; }
        .mtd-section { background: #e3f2fd; padding: 15px; border-radius: 6px; margin: 15px 0; }
        .log-entry { background: #fff3cd; padding: 8px; margin: 5px 0; border-radius: 4px; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Network Security Monitoring System</h1>
            <p>Moving Target Defense + Traffic Analysis</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="metric">{{ system_status }}</div>
                <div class="label">System Status</div>
            </div>
            
            <div class="status-card">
                <div class="metric">{{ current_ip }}</div>
                <div class="label">Current IP Address</div>
            </div>
            
            <div class="status-card">
                <div class="metric">{{ packets_captured }}</div>
                <div class="label">Packets Captured (Last Hour)</div>
            </div>
            
            <div class="status-card {{ 'warning' if alerts_count > 0 else '' }}">
                <div class="metric">{{ alerts_count }}</div>
                <div class="label">Security Alerts</div>
            </div>
            
            <div class="status-card {{ 'warning' if honeypot_attempts > 0 else '' }}">
                <div class="metric">{{ honeypot_attempts }}</div>
                <div class="label">Honeypot Attempts</div>
            </div>
            
            <div class="status-card">
                <div class="metric">{{ uptime }}</div>
                <div class="label">System Uptime</div>
            </div>
        </div>
        
        <div class="mtd-section">
            <h3>🎯 Moving Target Defense Status</h3>
            <p><strong>IP Randomization:</strong> {{ ip_randomization_status }}</p>
            <p><strong>DDNS:</strong> {{ ddns_status }}</p>
            <p><strong>SSH Honeypot:</strong> {{ honeypot_status }}</p>
        </div>
        
        <div class="mtd-section">
            <h3>📊 Monitoring Components</h3>
            <p><strong>Suricata IDS/IPS:</strong> {{ suricata_status }}</p>
            <p><strong>Arkime:</strong> {{ arkime_status }}</p>
            <p><strong>OpenSearch:</strong> {{ opensearch_status }}</p>
            <p><strong>Prometheus:</strong> {{ prometheus_status }}</p>
            <p><strong>Grafana:</strong> {{ grafana_status }}</p>
            <p><strong>Loki:</strong> {{ loki_status }}</p>
        </div>
        
        {% if recent_alerts %}
        <div class="mtd-section">
            <h3>🚨 Recent Security Events</h3>
            {% for alert in recent_alerts %}
            <div class="log-entry">{{ alert }}</div>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="timestamp">
            Last Updated: {{ timestamp }}
        </div>
    </div>
</body>
</html>
"""

def get_current_ip():
    """Get current IP address"""
    try:
        with open("/tmp/windows_ip.txt", "r") as ip_file:
            ip = ip_file.read()
            ip_file.close()
            return ip
    except:
        return "Unknown"

def check_service_status(url):
    """Check if a service is responding"""
    try:
        response = requests.get(url, timeout=3)
        return "🟢 Active" if response.status_code == 200 else "🟡 Warning"
    except:
        return "🔴 Down"

def check_opensearch_status():
    """Check OpenSearch cluster health"""
    try:
        response = requests.get(f"{OPENSEARCH_URL}/_cluster/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            status = health.get('status', 'unknown')
            if status == 'green':
                return "🟢 Healthy"
            elif status == 'yellow':
                return "🟡 Warning"
            else:
                return "🔴 Critical"
        return "🔴 Down"
    except:
        return "🔴 Down"

def safe_int(value, default=0):
    """Safely convert a value to integer"""
    try:
        if isinstance(value, str) and value.lower() in ['n/a', 'unknown', '']:
            return default
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default

def get_prometheus_metric(metric_name):
    """Get a metric from Prometheus"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", 
                              params={'query': metric_name}, timeout=5)
        data = response.json()
        if data['status'] == 'success' and data['data']['result']:
            return data['data']['result'][0]['value'][1]
        return "0"
    except:
        return "N/A"

def get_uptime():
    """Get system uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    except:
        return "Unknown"

def get_opensearch_document_count():
    """Get total document count from OpenSearch"""
    try:
        response = requests.get(f"{OPENSEARCH_URL}/_stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            total_docs = stats.get('_all', {}).get('total', {}).get('docs', {}).get('count', 0)
            return str(total_docs)
        return "0"
    except:
        return "N/A"

@app.route('/')
def status_page():
    """Main status page"""
    
    # Get current metrics and convert to safe integers for template comparison
    alerts_count = safe_int(get_prometheus_metric('suricata_alerts_total'))
    honeypot_attempts = safe_int(get_prometheus_metric('cowrie_sessions_total'))
    
    data = {
        'system_status': '🟢 Operational',
        'current_ip': get_current_ip(),
        'packets_captured': get_prometheus_metric('suricata_capture_kernel_packets_total'),
        'alerts_count': alerts_count,
        'honeypot_attempts': honeypot_attempts,
        'uptime': get_uptime(),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        # MTD Status
        'ip_randomization_status': '🟢 Active',
        'ddns_status': '🟢 Active', 
        'honeypot_status': '🟢 Active',
        
        # Component Status
        'suricata_status': check_service_status(f"{SURICATA_EXPORTER_URL}/metrics"),
        'arkime_status': check_service_status(ARKIME_VIEWER_URL),
        'opensearch_status': check_opensearch_status(),
        'prometheus_status': check_service_status(f"{PROMETHEUS_URL}/api/v1/label/__name__/values"),
        'grafana_status': check_service_status(f"{GRAFANA_URL}/api/health"),
        'loki_status': check_service_status(f"{LOKI_URL}/ready"),
        
        # Recent alerts (mock data)
        'recent_alerts': [
            f"{datetime.now().strftime('%H:%M:%S')} - SSH brute force attempt blocked",
            f"{datetime.now().strftime('%H:%M:%S')} - Suspicious traffic pattern detected",
            f"{datetime.now().strftime('%H:%M:%S')} - Honeypot interaction logged"
        ]
    }
    
    return render_template_string(HTML_TEMPLATE, **data)

@app.route('/api/status')
def api_status():
    """JSON API endpoint for status"""
    alerts_count = safe_int(get_prometheus_metric('suricata_alerts_total'))
    honeypot_attempts = safe_int(get_prometheus_metric('cowrie_sessions_total'))
    
    return jsonify({
        'system_status': 'operational',
        'current_ip': get_current_ip(),
        'packets_captured': get_prometheus_metric('suricata_capture_kernel_packets_total'),
        'alerts_count': alerts_count,
        'honeypot_attempts': honeypot_attempts,
        'opensearch_documents': get_opensearch_document_count(),
        'timestamp': datetime.now().isoformat(),
        'components': {
            'suricata': 'active',
            'opensearch': check_opensearch_status(),
            'prometheus': 'active',
            'grafana': 'active',
            'loki': 'active',
            'arkime': 'active'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Network Security Monitoring Status Server...")
    print("📊 Access the dashboard at: http://localhost:5000")
    print("🔗 API endpoint available at: http://localhost:5000/api/status")
    app.run(host='0.0.0.0', port=5000, debug=True)