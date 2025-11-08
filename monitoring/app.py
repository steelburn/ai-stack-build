from flask import Flask, render_template_string, request, Response
import requests
import time
from flask_cors import CORS
import os
import json
import docker
from functools import wraps

app = Flask(__name__)

# Enable CORS with security restrictions
CORS(app, resources={
    r"/*": {
        "origins": ["https://localhost", "https://localhost:443", "http://localhost", "http://localhost:80"],
        "methods": ["GET"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["X-Custom-Header"],
        "supports_credentials": False
    }
})

# Basic authentication
def check_auth(username, password):
    expected_username = os.getenv('MONITORING_USERNAME') or read_secret_file('/run/secrets/monitoring_username')
    expected_password = os.getenv('MONITORING_PASSWORD') or read_secret_file('/run/secrets/monitoring_password')
    return username == expected_username and password == expected_password

def read_secret_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except:
        return None

def get_docker_client():
    """Get Docker client for log monitoring"""
    try:
        return docker.from_env()
    except Exception as e:
        print("Failed to connect to Docker: {}".format(e))
        return None

def get_container_logs(container_name, lines=50, since=None):
    """Fetch recent logs from a Docker container"""
    try:
        client = get_docker_client()
        if not client:
            return []

        # Find container by name (may include project prefix)
        containers = client.containers.list(all=True)
        target_container = None

        for container in containers:
            if container_name in container.name:
                target_container = container
                break

        if not target_container:
            return ["Container '{}' not found".format(container_name)]

        # Get logs
        logs = target_container.logs(tail=lines, since=since, timestamps=True)
        log_lines = logs.decode('utf-8').strip().split('\n')

        # Filter out empty lines and format
        formatted_logs = []
        for line in log_lines:
            if line.strip():
                formatted_logs.append(line)

        return formatted_logs[-lines:]  # Return last N lines

    except Exception as e:
        return ["Error fetching logs: {}".format(str(e))]

def get_container_resources(container_name):
    """Get resource usage statistics for a Docker container"""
    try:
        client = get_docker_client()
        if not client:
            return None

        # Find container by name
        containers = client.containers.list(all=True)
        target_container = None

        for container in containers:
            if container_name in container.name:
                target_container = container
                break

        if not target_container:
            return None

        # Get container stats
        stats = target_container.stats(stream=False)

        # Extract CPU usage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        cpu_percent = 0.0
        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100

        # Extract memory usage
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0

        # Extract network I/O
        networks = stats.get('networks', {})
        rx_bytes = 0
        tx_bytes = 0
        for net_name, net_stats in networks.items():
            rx_bytes += net_stats.get('rx_bytes', 0)
            tx_bytes += net_stats.get('tx_bytes', 0)

        # Extract block I/O (disk)
        blkio_stats = stats.get('blkio_stats', {})
        io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
        read_bytes = 0
        write_bytes = 0
        for io_stat in io_service_bytes:
            if io_stat.get('op') == 'Read':
                read_bytes += io_stat.get('value', 0)
            elif io_stat.get('op') == 'Write':
                write_bytes += io_stat.get('value', 0)

        return {
            'cpu_percent': round(cpu_percent, 2),
            'memory_usage': memory_usage,
            'memory_limit': memory_limit,
            'memory_percent': round(memory_percent, 2),
            'network_rx': rx_bytes,
            'network_tx': tx_bytes,
            'disk_read': read_bytes,
            'disk_write': write_bytes,
            'container_status': target_container.status,
            'container_id': target_container.short_id
        }

    except Exception as e:
        print("Error getting container resources for {}: {}".format(container_name, str(e)))
        return None

def format_bytes(bytes_value):
    """Format bytes into human readable format"""
    if bytes_value == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return "{:.1f} {}".format(bytes_value, unit)
        bytes_value /= 1024.0
    return "{:.1f} PB".format(bytes_value)

def load_services():
    """
    Load services configuration from multiple sources:
    1. JSON file specified by SERVICES_CONFIG env var
    2. Environment variables with pattern SERVICE_{N}_NAME and SERVICE_{N}_URL
    3. Fallback to hardcoded defaults
    """
    # Try loading from JSON config file
    config_file = os.getenv('SERVICES_CONFIG')
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                services = json.load(f)
                print("Loaded services from config file: {}".format(config_file))
                return services
        except Exception as e:
            print("Error loading config file {}: {}".format(config_file, e))

    # Try loading from environment variables
    services = {}
    index = 1
    while True:
        name_key = 'SERVICE_{}_NAME'.format(index)
        url_key = 'SERVICE_{}_URL'.format(index)

        name = os.getenv(name_key)
        url = os.getenv(url_key)

        if not name or not url:
            break

        services['service_{}'.format(index)] = {'url': url, 'name': name}
        index += 1

    if services:
        print("Loaded {} services from environment variables".format(len(services)))
        return services

    # Fallback to hardcoded defaults
    print("Using default hardcoded services configuration")
    return {
        'dify-api': {'url': 'http://dify-api:8080/health', 'name': 'Dify API'},
        'dify-web': {'url': 'http://dify-web:3000/health', 'name': 'Dify Web'},
        'dify-worker': {'url': 'http://dify-worker:8080/health', 'name': 'Dify Worker'},
        'ollama': {'url': 'http://ollama:11434/api/version', 'name': 'Ollama'},
        'litellm': {'url': 'http://litellm:4000/health', 'name': 'LiteLLM'},
        'mem0': {'url': 'http://mem0:8000/health', 'name': 'Mem0'},
        'n8n': {'url': 'http://n8n:5678/healthz', 'name': 'N8N'},
        'flowise': {'url': 'http://flowise:3000/api/v1/health', 'name': 'Flowise'},
        'openwebui': {'url': 'http://openwebui:8080/health', 'name': 'OpenWebUI'},
        'qdrant': {'url': 'http://qdrant:6333/health', 'name': 'Qdrant'}
    }

def authenticate():
    return Response(
        'Authentication required', 401,
        {'WWW-Authenticate': 'Basic realm="Monitoring Dashboard"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

SERVICES = load_services()

def check_service(url, name):
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        response_time = round((time.time() - start) * 1000, 2)  # ms
        if response.status_code == 200:
            return {'status': 'up', 'response_time': response_time, 'error': None}
        else:
            return {'status': 'down', 'response_time': None, 'error': 'HTTP {}'.format(response.status_code)}
    except requests.exceptions.RequestException as e:
        return {'status': 'down', 'response_time': None, 'error': str(e)}

@app.route('/')
@requires_auth
def index():
    statuses = {}
    for service, info in SERVICES.items():
        statuses[service] = check_service(info['url'], info['name'])
        statuses[service]['name'] = info['name']

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Stack Status Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            h1 { color: #333; text-align: center; }
            .container { max-width: 1200px; margin: 0 auto; }
            table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #2c3e50; color: white; font-weight: bold; }
            .up { color: #27ae60; font-weight: bold; }
            .down { color: #e74c3c; font-weight: bold; }
            .refresh { text-align: center; margin: 20px 0; }
            .refresh button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .refresh button:hover { background: #2980b9; }
            .logs-link { color: #3498db; text-decoration: none; }
            .logs-link:hover { text-decoration: underline; }
            .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
            .status-up { background-color: #27ae60; }
            .status-down { background-color: #e74c3c; }
            .response-time { font-size: 0.9em; color: #666; }
        </style>
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <div class="container">
            <h1>AI Stack Services Status</h1>
            <div style="text-align: center; margin-bottom: 20px;">
                <a href="/resources" style="background: #e67e22; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; margin-right: 10px;">📊 Resource Monitor</a>
            </div>
            <div class="refresh">
                <button onclick="location.reload()">Refresh Now</button>
                <p style="margin-top: 10px; color: #666; font-size: 0.9em;">Auto-refresh every 30 seconds</p>
            </div>
            <table>
                <tr>
                    <th>Service</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Actions</th>
                </tr>
                {% for service, status in statuses.items() %}
                <tr>
                    <td>{{ status.name }}</td>
                    <td>
                        <span class="status-indicator status-{{ 'up' if status.status == 'up' else 'down' }}"></span>
                        <span class="{{ status.status }}">{{ status.status.upper() }}</span>
                    </td>
                    <td class="response-time">{{ status.response_time or 'N/A' }}</td>
                    <td>
                        <a href="/logs/{{ service }}" class="logs-link">View Logs</a> |
                        <a href="/resources" class="logs-link">View Resources</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, statuses=statuses)

@app.route('/logs/<service_name>')
@requires_auth
def view_logs(service_name):
    if service_name not in SERVICES:
        return "Service not found", 404

    service_info = SERVICES[service_name]
    logs = get_container_logs(service_name)

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logs - {{ service_name }}</title>
        <style>
            body { font-family: 'Courier New', monospace; margin: 20px; background-color: #1e1e1e; color: #f8f8f2; }
            h1 { color: #66d9ef; margin-bottom: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .log-container { background: #2d2d2d; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.3); max-height: 70vh; overflow-y: auto; }
            .log-line { margin: 2px 0; padding: 2px 0; border-bottom: 1px solid #444; white-space: pre-wrap; word-wrap: break-word; }
            .log-line:nth-child(even) { background-color: #333; }
            .error { color: #f92672; }
            .warning { color: #fd971f; }
            .info { color: #a6e22e; }
            .debug { color: #75715e; }
            .back-link { color: #66d9ef; text-decoration: none; margin-bottom: 20px; display: inline-block; }
            .back-link:hover { text-decoration: underline; }
            .refresh-btn { background: #49483e; color: #f8f8f2; border: 1px solid #75715e; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-bottom: 20px; }
            .refresh-btn:hover { background: #75715e; }
            .log-count { color: #a6e22e; font-size: 0.9em; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>Logs: {{ service_name }} ({{ service_info.name }})</h1>
            <button onclick="location.reload()" class="refresh-btn">Refresh Logs</button>
            <div class="log-count">Showing last {{ logs|length }} log entries</div>
            <div class="log-container">
                {% for log_line in logs %}
                <div class="log-line{% if 'ERROR' in log_line or 'error' in log_line %} error{% elif 'WARN' in log_line or 'warning' in log_line %} warning{% elif 'INFO' in log_line %} info{% elif 'DEBUG' in log_line %} debug{% endif %}">{{ log_line }}</div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, service_name=service_name, service_info=service_info, logs=logs)

@app.route('/resources')
@requires_auth
def view_resources():
    resources = {}
    for service, info in SERVICES.items():
        resource_data = get_container_resources(service)
        if resource_data:
            resources[service] = {
                'name': info['name'],
                **resource_data
            }

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resource Monitor - AI Stack</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            h1 { color: #333; text-align: center; }
            .container { max-width: 1400px; margin: 0 auto; }
            table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 0.9em; }
            th { background-color: #2c3e50; color: white; font-weight: bold; }
            .back-link { color: #3498db; text-decoration: none; margin-bottom: 20px; display: inline-block; }
            .back-link:hover { text-decoration: underline; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }
            .refresh-btn:hover { background: #2980b9; }
            .resource-bar { width: 100%; height: 20px; background-color: #ecf0f1; border-radius: 10px; overflow: hidden; margin: 2px 0; }
            .cpu-bar { background: linear-gradient(to right, #e74c3c, #f39c12, #27ae60); }
            .memory-bar { background: linear-gradient(to right, #3498db, #9b59b6); }
            .resource-value { font-weight: bold; margin-bottom: 5px; }
            .resource-percent { font-size: 0.8em; color: #666; }
            .status-running { color: #27ae60; font-weight: bold; }
            .status-stopped { color: #e74c3c; font-weight: bold; }
            .metric-group { margin-bottom: 15px; }
            .metric-label { font-weight: bold; color: #555; margin-bottom: 5px; }
        </style>
        <meta http-equiv="refresh" content="10">
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>Resource Monitor - AI Stack Services</h1>
            <button onclick="location.reload()" class="refresh-btn">Refresh Now</button>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 20px;">Auto-refresh every 10 seconds</p>

            <table>
                <tr>
                    <th>Service</th>
                    <th>Status</th>
                    <th>CPU Usage</th>
                    <th>Memory Usage</th>
                    <th>Network I/O</th>
                    <th>Disk I/O</th>
                </tr>
                {% for service, resource in resources.items() %}
                <tr>
                    <td><strong>{{ resource.name }}</strong><br><small style="color: #666;">{{ service }}</small></td>
                    <td class="status-{{ resource.container_status }}">{{ resource.container_status.title() }}</td>
                    <td>
                        <div class="metric-group">
                            <div class="resource-value">{{ resource.cpu_percent }}%</div>
                            <div class="resource-bar">
                                <div class="cpu-bar" style="width: {{ resource.cpu_percent }}%; height: 100%;"></div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <div class="metric-group">
                            <div class="resource-value">{{ resource.memory_percent }}%</div>
                            <div class="resource-percent">{{ format_bytes(resource.memory_usage) }} / {{ format_bytes(resource.memory_limit) }}</div>
                            <div class="resource-bar">
                                <div class="memory-bar" style="width: {{ resource.memory_percent }}%; height: 100%;"></div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <div class="metric-group">
                            <div class="metric-label">RX: {{ format_bytes(resource.network_rx) }}</div>
                            <div class="metric-label">TX: {{ format_bytes(resource.network_tx) }}</div>
                        </div>
                    </td>
                    <td>
                        <div class="metric-group">
                            <div class="metric-label">Read: {{ format_bytes(resource.disk_read) }}</div>
                            <div class="metric-label">Write: {{ format_bytes(resource.disk_write) }}</div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </table>

            {% if not resources %}
            <div style="text-align: center; padding: 40px; background: white; border-radius: 8px; margin-top: 20px;">
                <h3 style="color: #e74c3c;">No Resource Data Available</h3>
                <p>Unable to fetch container resource statistics. Please check Docker connectivity.</p>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, resources=resources, format_bytes=format_bytes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)