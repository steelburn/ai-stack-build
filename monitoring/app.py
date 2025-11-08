# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, Response
import requests
import time
from flask_cors import CORS
import os
import json
import docker
from functools import wraps
import psutil
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import threading
import json

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

# Prometheus Metrics
# Service health metrics
service_up = Gauge('ai_stack_service_up', 'Service health status (1=up, 0=down)', ['service'])
service_response_time = Gauge('ai_stack_service_response_time_ms', 'Service response time in milliseconds', ['service'])

# Resource metrics
container_cpu_percent = Gauge('ai_stack_container_cpu_percent', 'Container CPU usage percentage', ['container'])
container_memory_percent = Gauge('ai_stack_container_memory_percent', 'Container memory usage percentage', ['container'])
container_memory_usage = Gauge('ai_stack_container_memory_usage_bytes', 'Container memory usage in bytes', ['container'])
container_network_rx = Gauge('ai_stack_container_network_rx_bytes', 'Container network receive bytes', ['container'])
container_network_tx = Gauge('ai_stack_container_network_tx_bytes', 'Container network transmit bytes', ['container'])

# System metrics
system_cpu_percent = Gauge('ai_stack_system_cpu_percent', 'System CPU usage percentage')
system_memory_percent = Gauge('ai_stack_system_memory_percent', 'System memory usage percentage')
system_disk_usage_percent = Gauge('ai_stack_system_disk_usage_percent', 'System disk usage percentage', ['mountpoint'])

# Request metrics
http_requests_total = Counter('ai_stack_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration = Histogram('ai_stack_http_request_duration_seconds', 'HTTP request duration in seconds', ['method', 'endpoint'])

# Metrics history storage
METRICS_HISTORY = {}
HISTORY_MAX_POINTS = 100  # Keep last 100 data points
history_lock = threading.Lock()

def check_service(url, name):
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        response_time = round((time.time() - start) * 1000, 2)  # ms
        if response.status_code == 200:
            service_up.labels(service=name).set(1)
            service_response_time.labels(service=name).set(response_time)
            return {'status': 'up', 'response_time': response_time, 'error': None}
        else:
            service_up.labels(service=name).set(0)
            return {'status': 'down', 'response_time': None, 'error': 'HTTP {}'.format(response.status_code)}
    except requests.exceptions.RequestException as e:
        service_up.labels(service=name).set(0)
        return {'status': 'down', 'response_time': None, 'error': str(e)}

def store_metrics_snapshot():
    """Store current metrics snapshot for historical analysis"""
    with history_lock:
        timestamp = time.time()

        # Collect current service statuses
        service_statuses = {}
        for service, info in SERVICES.items():
            if info.get('optional', False):
                client = get_docker_client()
                if client:
                    try:
                        containers = client.containers.list(filters={'name': service})
                        if not containers:
                            continue
                    except:
                        pass

            status = check_service(info['url'], info['name'])
            service_statuses[service] = {
                'status': status['status'],
                'response_time': status['response_time'],
                'timestamp': timestamp
            }

        # Collect system metrics
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'timestamp': timestamp
        }

        # Collect container resource metrics
        container_resources = {}
        for service, info in SERVICES.items():
            resource_data = get_container_resources(service)
            if resource_data:
                container_resources[service] = dict(resource_data)
                container_resources[service]['timestamp'] = timestamp

        # Store in history
        snapshot = {
            'timestamp': timestamp,
            'services': service_statuses,
            'system': system_metrics,
            'containers': container_resources
        }

        if 'snapshots' not in METRICS_HISTORY:
            METRICS_HISTORY['snapshots'] = []

        METRICS_HISTORY['snapshots'].append(snapshot)

        # Keep only recent snapshots
        if len(METRICS_HISTORY['snapshots']) > HISTORY_MAX_POINTS:
            METRICS_HISTORY['snapshots'] = METRICS_HISTORY['snapshots'][-HISTORY_MAX_POINTS:]

# Start background metrics collection
def metrics_collection_worker():
    """Background worker to collect metrics periodically"""
    while True:
        try:
            store_metrics_snapshot()
        except Exception as e:
            print("Error collecting metrics: {}".format(e))
        time.sleep(60)  # Collect every minute

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

    # Track HTTP metrics
    if hasattr(request, 'endpoint') and request.endpoint:
        http_requests_total.labels(
            method=request.method,
            endpoint=request.endpoint,
            status=response.status_code
        ).inc()

    return response

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    # Update system metrics
    system_cpu_percent.set(psutil.cpu_percent(interval=1))
    system_memory_percent.set(psutil.virtual_memory().percent)

    # Update disk usage metrics
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            system_disk_usage_percent.labels(mountpoint=partition.mountpoint).set(usage.percent)
        except:
            pass

    # Update container resource metrics
    for service, info in SERVICES.items():
        resource_data = get_container_resources(service)
        if resource_data:
            container_cpu_percent.labels(container=service).set(resource_data['cpu_percent'])
            container_memory_percent.labels(container=service).set(resource_data['memory_percent'])
            container_memory_usage.labels(container=service).set(resource_data['memory_usage'])
            container_network_rx.labels(container=service).set(resource_data['network_rx'])
            container_network_tx.labels(container=service).set(resource_data['network_tx'])

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

SERVICES = load_services()

# Start the metrics collection thread
metrics_thread = threading.Thread(target=metrics_collection_worker, daemon=True)
metrics_thread.start()

# Request tracing middleware
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        # Track request duration for monitoring endpoints
        if request.endpoint in ['index', 'view_resources', 'view_alerts', 'metrics']:
            http_request_duration.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(duration)
    return response

@app.route('/')
# @requires_auth
def index():
    statuses = {}
    client = get_docker_client()

    for service, info in SERVICES.items():
        # Check if service is optional and running
        if info.get('optional', False):
            if client:
                try:
                    containers = client.containers.list(filters={'name': service})
                    if not containers:
                        statuses[service] = {
                            'status': 'disabled',
                            'response_time': None,
                            'error': 'Service not enabled',
                            'name': info['name']
                        }
                        continue
                except:
                    pass

        # Check service health
        statuses[service] = check_service(info['url'], info['name'])
        statuses[service]['name'] = info['name']

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Stack Status Monitor</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background-color: #f5f5f5; box-sizing: border-box; }
            h1 { color: #333; text-align: center; margin: 10px 0; font-size: 1.5em; }
            .container { max-width: 1400px; margin: 0 auto; padding: 0 10px; }
            .dashboard-grid { display: grid; grid-template-columns: 1fr; gap: 15px; margin-bottom: 20px; }
            .chart-container { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .chart-container canvas { width: 100% !important; height: 250px !important; }
            .chart-title { font-size: 1.1em; font-weight: bold; margin-bottom: 10px; color: #333; }
            table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow-x: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: block; }
            th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; white-space: nowrap; }
            th { background-color: #2c3e50; color: white; font-weight: bold; position: sticky; top: 0; }
            .up { color: #27ae60; font-weight: bold; }
            .down { color: #e74c3c; font-weight: bold; }
            .disabled { color: #95a5a6; font-weight: bold; }
            .refresh { text-align: center; margin: 15px 0; }
            .refresh button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .refresh button:hover { background: #2980b9; }
            .logs-link { color: #3498db; text-decoration: none; }
            .logs-link:hover { text-decoration: underline; }
            .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
            .status-up { background-color: #27ae60; }
            .status-down { background-color: #e74c3c; }
            .status-disabled { background-color: #95a5a6; }
            .response-time { font-size: 0.85em; color: #666; }
            .nav-buttons { text-align: center; margin-bottom: 15px; display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
            .nav-buttons a { background: #e67e22; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 14px; display: inline-block; }
            .nav-buttons a:hover { background: #d35400; }
            .metrics-link { background: #9b59b6 !important; }
            .metrics-link:hover { background: #8e44ad !important; }

            /* Responsive breakpoints */
            @media (min-width: 768px) {
                body { padding: 20px; }
                h1 { font-size: 2em; margin: 20px 0; }
                .container { padding: 0 20px; }
                .dashboard-grid { grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
                .chart-container { padding: 20px; }
                .chart-title { font-size: 1.2em; margin-bottom: 15px; }
                th, td { padding: 12px; }
                .status-indicator { width: 12px; height: 12px; margin-right: 8px; }
                .response-time { font-size: 0.9em; }
                .nav-buttons { gap: 10px; }
                .nav-buttons a { padding: 8px 16px; font-size: 16px; }
                .refresh { margin: 20px 0; }
            }

            @media (min-width: 1024px) {
                .dashboard-grid { grid-template-columns: 1fr 1fr; }
            }

            /* Mobile optimizations */
            @media (max-width: 480px) {
                body { padding: 5px; }
                h1 { font-size: 1.2em; }
                .chart-container { padding: 10px; }
                .chart-container canvas { height: 200px !important; }
                .chart-title { font-size: 1em; }
                th, td { padding: 6px 8px; font-size: 14px; }
                .nav-buttons a { padding: 5px 10px; font-size: 12px; }
                .refresh button { padding: 8px 16px; font-size: 14px; }
            }

            /* Table responsiveness */
            @media (max-width: 768px) {
                table { font-size: 14px; }
                th, td { padding: 6px 8px; }
                .response-time { display: block; margin-top: 4px; }
            }
        </style>
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <div class="container">
            <h1>AI Stack Services Status</h1>
            <div class="nav-buttons">
                <a href="/resources">📊 Resource Monitor</a>
                <a href="/metrics" class="metrics-link">📈 Prometheus Metrics</a>
                <a href="/alerts">🚨 Alert Dashboard</a>
                <a href="/trends">📉 Trends & History</a>
            </div>
            <div class="dashboard-grid">
                <div class="chart-container">
                    <div class="chart-title">Service Health Overview</div>
                    <canvas id="healthChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Response Times (ms)</div>
                    <canvas id="responseTimeChart"></canvas>
                </div>
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
                        <span class="status-indicator status-{{ 'up' if status.status == 'up' else 'down' if status.status == 'down' else 'disabled' }}"></span>
                        <span class="{{ status.status }}">{{ status.status.upper() }}</span>
                    </td>
                    <td class="response-time">{{ status.response_time or 'N/A' }}</td>
                    <td>
                        {% if status.status == 'disabled' %}
                        <span style="color: #95a5a6;">Service disabled</span>
                        {% else %}
                        <a href="/logs/{{ service }}" class="logs-link">View Logs</a> |
                        <a href="/resources" class="logs-link">View Resources</a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <script>
            // Prepare data for charts
            const serviceNames = {{ statuses.keys() | list | tojson }};
            const serviceStatuses = {{ [status.status for status in statuses.values()] | tojson }};
            const responseTimes = {{ [status.response_time or 0 for status in statuses.values()] | tojson }};

            // Health Chart
            const healthCtx = document.getElementById('healthChart').getContext('2d');
            const healthData = {
                labels: serviceNames,
                datasets: [{
                    label: 'Service Status',
                    data: serviceStatuses.map(status => status === 'up' ? 1 : status === 'down' ? 0 : 0.5),
                    backgroundColor: serviceStatuses.map(status =>
                        status === 'up' ? '#27ae60' : status === 'down' ? '#e74c3c' : '#95a5a6'
                    ),
                    borderColor: serviceStatuses.map(status =>
                        status === 'up' ? '#229954' : status === 'down' ? '#c0392b' : '#7f8c8d'
                    ),
                    borderWidth: 1
                }]
            };
            new Chart(healthCtx, {
                type: 'bar',
                data: healthData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1,
                            ticks: {
                                callback: function(value) {
                                    return value === 1 ? 'Up' : value === 0 ? 'Down' : 'Disabled';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });

            // Response Time Chart
            const responseCtx = document.getElementById('responseTimeChart').getContext('2d');
            const responseData = {
                labels: serviceNames,
                datasets: [{
                    label: 'Response Time (ms)',
                    data: responseTimes,
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 1
                }]
            };
            new Chart(responseCtx, {
                type: 'bar',
                data: responseData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        </script>
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

    # Get filter parameters
    filter_level = request.args.get('level', 'all')
    search_term = request.args.get('search', '').strip()
    lines = int(request.args.get('lines', 50))

    logs = get_container_logs(service_name, lines=lines)

    # Apply filters
    filtered_logs = []
    for log_line in logs:
        # Level filtering
        if filter_level != 'all':
            if filter_level.upper() not in log_line.upper():
                continue

        # Search filtering
        if search_term and search_term.lower() not in log_line.lower():
            continue

        filtered_logs.append(log_line)

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logs - {{ service_name }}</title>
        <style>
            body { font-family: 'Courier New', monospace; margin: 0; padding: 10px; background-color: #1e1e1e; color: #f8f8f2; box-sizing: border-box; }
            h1 { color: #66d9ef; margin-bottom: 15px; font-size: 1.5em; }
            .container { max-width: 1400px; margin: 0 auto; padding: 0 10px; }
            .log-container { background: #2d2d2d; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.3); max-height: 70vh; overflow-y: auto; }
            .log-line { margin: 2px 0; padding: 2px 0; border-bottom: 1px solid #444; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; }
            .log-line:nth-child(even) { background-color: #333; }
            .error { color: #f92672; }
            .warning { color: #fd971f; }
            .info { color: #a6e22e; }
            .debug { color: #75715e; }
            .back-link { color: #66d9ef; text-decoration: none; margin-bottom: 15px; display: inline-block; }
            .back-link:hover { text-decoration: underline; }
            .controls { background: #2d2d2d; padding: 15px; border-radius: 8px; margin-bottom: 15px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
            .control-group { display: flex; align-items: center; gap: 8px; }
            .control-group label { color: #f8f8f2; font-weight: bold; font-size: 14px; }
            .control-group select, .control-group input { background: #404040; color: #f8f8f2; border: 1px solid #666; border-radius: 4px; padding: 5px 10px; font-size: 14px; }
            .control-group input { width: 150px; }
            .refresh-btn { background: #49483e; color: #f8f8f2; border: 1px solid #75715e; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; }
            .refresh-btn:hover { background: #75715e; }
            .filter-btn { background: #66d9ef; color: #1e1e1e; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px; }
            .filter-btn:hover { background: #4dd0e1; }
            .log-count { color: #a6e22e; font-size: 0.85em; margin-bottom: 10px; }
            .log-stats { background: #333; padding: 10px; border-radius: 4px; margin-bottom: 15px; display: flex; gap: 15px; flex-wrap: wrap; }
            .stat-item { color: #f8f8f2; font-size: 14px; }
            .stat-label { color: #a6e22e; font-weight: bold; }

            /* Responsive breakpoints */
            @media (min-width: 768px) {
                body { padding: 20px; }
                h1 { font-size: 2em; margin-bottom: 20px; }
                .container { padding: 0 20px; }
                .log-container { padding: 20px; }
                .controls { padding: 20px; margin-bottom: 20px; gap: 15px; }
                .control-group input { width: 200px; }
                .log-line { font-size: 16px; }
                .log-stats { gap: 20px; }
            }

            /* Mobile optimizations */
            @media (max-width: 768px) {
                .controls { flex-direction: column; align-items: stretch; }
                .control-group { justify-content: space-between; }
                .control-group input { width: 120px; }
                .log-stats { flex-direction: column; gap: 8px; }
            }

            @media (max-width: 480px) {
                body { padding: 5px; }
                h1 { font-size: 1.2em; }
                .log-container { padding: 10px; max-height: 60vh; }
                .controls { padding: 10px; }
                .control-group { flex-direction: column; align-items: flex-start; gap: 4px; }
                .control-group input { width: 100%; }
                .control-group select { width: 100%; }
                .log-line { font-size: 12px; }
                .stat-item { font-size: 12px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>Logs: {{ service_name }} ({{ service_info.name }})</h1>

            <div class="controls">
                <div class="control-group">
                    <label for="level">Level:</label>
                    <select id="level" name="level">
                        <option value="all" {{ 'selected' if level == 'all' else '' }}>All</option>
                        <option value="error" {{ 'selected' if level == 'error' else '' }}>Errors</option>
                        <option value="warning" {{ 'selected' if level == 'warning' else '' }}>Warnings</option>
                        <option value="info" {{ 'selected' if level == 'info' else '' }}>Info</option>
                        <option value="debug" {{ 'selected' if level == 'debug' else '' }}>Debug</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="search">Search:</label>
                    <input type="text" id="search" name="search" value="{{ search_term }}" placeholder="Search logs...">
                </div>
                <div class="control-group">
                    <label for="lines">Lines:</label>
                    <select id="lines" name="lines">
                        <option value="50" {{ 'selected' if lines == 50 else '' }}>50</option>
                        <option value="100" {{ 'selected' if lines == 100 else '' }}>100</option>
                        <option value="200" {{ 'selected' if lines == 200 else '' }}>200</option>
                        <option value="500" {{ 'selected' if lines == 500 else '' }}>500</option>
                    </select>
                </div>
                <button onclick="applyFilters()" class="filter-btn">Apply Filters</button>
                <button onclick="location.reload()" class="refresh-btn">Refresh</button>
            </div>

            <div class="log-stats">
                <div class="stat-item">
                    <span class="stat-label">Total Lines:</span> {{ logs|length }}
                </div>
                <div class="stat-item">
                    <span class="stat-label">Filtered:</span> {{ filtered_logs|length }}
                </div>
                <div class="stat-item">
                    <span class="stat-label">Errors:</span> {{ filtered_logs | select('match', 'ERROR|error') | list | length }}
                </div>
                <div class="stat-item">
                    <span class="stat-label">Warnings:</span> {{ filtered_logs | select('match', 'WARN|warning') | list | length }}
                </div>
            </div>

            <div class="log-count">Showing {{ filtered_logs|length }} filtered log entries</div>
            <div class="log-container">
                {% for log_line in filtered_logs %}
                <div class="log-line{% if 'ERROR' in log_line or 'error' in log_line %} error{% elif 'WARN' in log_line or 'warning' in log_line %} warning{% elif 'INFO' in log_line %} info{% elif 'DEBUG' in log_line %} debug{% endif %}">{{ log_line }}</div>
                {% endfor %}
            </div>
        </div>

        <script>
            function applyFilters() {
                const level = document.getElementById('level').value;
                const search = document.getElementById('search').value;
                const lines = document.getElementById('lines').value;

                let url = `/logs/{{ service_name }}?level=${level}&lines=${lines}`;
                if (search) {
                    url += `&search=${encodeURIComponent(search)}`;
                }

                window.location.href = url;
            }

            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, service_name=service_name, service_info=service_info, logs=logs, filtered_logs=filtered_logs, level=filter_level, search_term=search_term, lines=lines)

@app.route('/resources')
@requires_auth
def view_resources():
    resources = {}
    for service, info in SERVICES.items():
        resource_data = get_container_resources(service)
        if resource_data:
            resources[service] = dict(resource_data)
            resources[service]['name'] = info['name']

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resource Monitor - AI Stack</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background-color: #f5f5f5; box-sizing: border-box; }
            h1 { color: #333; text-align: center; margin: 10px 0; font-size: 1.5em; }
            .container { max-width: 1400px; margin: 0 auto; padding: 0 10px; }
            table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow-x: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; display: block; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 0.9em; white-space: nowrap; }
            th { background-color: #2c3e50; color: white; font-weight: bold; position: sticky; top: 0; }
            .back-link { color: #3498db; text-decoration: none; margin-bottom: 15px; display: inline-block; }
            .back-link:hover { text-decoration: underline; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 15px; font-size: 16px; }
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

            /* Responsive breakpoints */
            @media (min-width: 768px) {
                body { padding: 20px; }
                h1 { font-size: 2em; margin: 20px 0; }
                .container { padding: 0 20px; }
                th, td { padding: 12px; font-size: 1em; }
            }

            /* Mobile optimizations */
            @media (max-width: 768px) {
                th, td { padding: 6px 8px; font-size: 14px; }
                .resource-value { font-size: 14px; }
                .resource-percent { font-size: 12px; }
                .metric-group { margin-bottom: 10px; }
            }

            @media (max-width: 480px) {
                body { padding: 5px; }
                h1 { font-size: 1.2em; }
                .refresh-btn { padding: 8px 16px; font-size: 14px; }
                th, td { padding: 4px 6px; font-size: 12px; }
                .resource-bar { height: 16px; }
            }
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

@app.route('/alerts')
@requires_auth
def view_alerts():
    alerts = []
    current_time = time.time()

    # Check service health alerts
    for service, info in SERVICES.items():
        # Skip optional services that aren't running
        if info.get('optional', False):
            client = get_docker_client()
            if client:
                try:
                    containers = client.containers.list(filters={'name': service})
                    if not containers:
                        continue
                except:
                    pass

        # Check service health
        status = check_service(info['url'], info['name'])
        if status['status'] == 'down':
            alerts.append({
                'type': 'error',
                'service': info['name'],
                'message': 'Service is down: {}'.format(status["error"]),
                'timestamp': current_time,
                'severity': 'critical'
            })

        # Check response time alerts (if service is up)
        if status['status'] == 'up' and status['response_time']:
            if status['response_time'] > 5000:  # 5 seconds
                alerts.append({
                    'type': 'warning',
                    'service': info['name'],
                    'message': 'High response time: {}ms'.format(status["response_time"]),
                    'timestamp': current_time,
                    'severity': 'warning'
                })

    # Check resource alerts
    for service, info in SERVICES.items():
        resource_data = get_container_resources(service)
        if resource_data:
            if resource_data['cpu_percent'] > 80:
                alerts.append({
                    'type': 'warning',
                    'service': info['name'],
                    'message': 'High CPU usage: {}%'.format(resource_data["cpu_percent"]),                    'timestamp': current_time,
                    'severity': 'warning'
                })

            if resource_data['memory_percent'] > 85:
                alerts.append({
                    'type': 'error',
                    'service': info['name'],
                    'message': 'High memory usage: {}%'.format(resource_data["memory_percent"]),                    'timestamp': current_time,
                    'severity': 'critical'
                })

    # Check system resource alerts
    system_cpu = psutil.cpu_percent(interval=1)
    system_memory = psutil.virtual_memory().percent

    if system_cpu > 90:
        alerts.append({
            'type': 'error',
            'service': 'System',
            'message': 'High system CPU usage: {}%'.format(system_cpu),
            'timestamp': current_time,
            'severity': 'critical'
        })

    if system_memory > 90:
        alerts.append({
            'type': 'error',
            'service': 'System',
            'message': 'High system memory usage: {}%'.format(system_memory),
            'timestamp': current_time,
            'severity': 'critical'
        })

    # Sort alerts by severity and timestamp
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    alerts.sort(key=lambda x: (severity_order.get(x['severity'], 3), -x['timestamp']))

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alert Dashboard - AI Stack</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background-color: #f5f5f5; box-sizing: border-box; }
            h1 { color: #333; text-align: center; margin: 10px 0; font-size: 1.5em; }
            .container { max-width: 1200px; margin: 0 auto; padding: 0 10px; }
            .back-link { color: #3498db; text-decoration: none; margin-bottom: 15px; display: inline-block; }
            .back-link:hover { text-decoration: underline; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 15px; font-size: 16px; }
            .refresh-btn:hover { background: #2980b9; }
            .alert-card { background: white; border-radius: 8px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 4px solid; }
            .alert-critical { border-left-color: #e74c3c; }
            .alert-warning { border-left-color: #f39c12; }
            .alert-info { border-left-color: #3498db; }
            .alert-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 10px; }
            .alert-service { font-weight: bold; font-size: 1.1em; }
            .alert-timestamp { color: #666; font-size: 0.9em; }
            .alert-message { color: #555; margin-bottom: 5px; }
            .alert-type { padding: 2px 8px; border-radius: 3px; color: white; font-size: 0.8em; font-weight: bold; }
            .alert-error { background-color: #e74c3c; }
            .alert-warning { background-color: #f39c12; }
            .alert-info { background-color: #3498db; }
            .no-alerts { text-align: center; padding: 40px; background: white; border-radius: 8px; margin-top: 20px; }
            .no-alerts h3 { color: #27ae60; }
            .alert-count { background: #2c3e50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
            .alert-count h2 { margin: 0; font-size: 2em; }
            .alert-count p { margin: 5px 0 0 0; opacity: 0.8; }

            /* Responsive breakpoints */
            @media (min-width: 768px) {
                body { padding: 20px; }
                h1 { font-size: 2em; margin: 20px 0; }
                .container { padding: 0 20px; }
                .alert-card { padding: 20px; }
                .alert-service { font-size: 1.2em; }
            }

            /* Mobile optimizations */
            @media (max-width: 768px) {
                .alert-header { flex-direction: column; align-items: flex-start; }
                .alert-service { font-size: 1em; }
                .alert-timestamp { align-self: flex-end; }
            }

            @media (max-width: 480px) {
                body { padding: 5px; }
                h1 { font-size: 1.2em; }
                .alert-card { padding: 10px; }
                .alert-count { padding: 10px; }
                .alert-count h2 { font-size: 1.5em; }
                .refresh-btn { padding: 8px 16px; font-size: 14px; }
            }
        </style>
        <meta http-equiv="refresh" content="60">
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>Alert Dashboard - AI Stack</h1>
            <button onclick="location.reload()" class="refresh-btn">Refresh Now</button>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 20px;">Auto-refresh every 60 seconds</p>

            <div class="alert-count">
                <h2>{{ alerts|length }}</h2>
                <p>Active Alerts</p>
            </div>

            {% if alerts %}
                {% for alert in alerts %}
                <div class="alert-card alert-{{ alert.severity }}">
                    <div class="alert-header">
                        <span class="alert-service">{{ alert.service }}</span>
                        <span class="alert-type alert-{{ alert.type }}">{{ alert.severity.upper() }}</span>
                    </div>
                    <div class="alert-message">{{ alert.message }}</div>
                    <div class="alert-timestamp">{{ alert.timestamp | strftime('%Y-%m-%d %H:%M:%S') }}</div>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-alerts">
                    <h3>✅ All Systems Operational</h3>
                    <p>No active alerts detected. All services are running normally.</p>
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, alerts=alerts)

@app.route('/trends')
@requires_auth
def view_trends():
    with history_lock:
        snapshots = METRICS_HISTORY.get('snapshots', [])

    if not snapshots:
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trends - AI Stack</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; text-align: center; }
                .back-link { color: #3498db; text-decoration: none; margin-bottom: 20px; display: inline-block; }
                .no-data { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-link">← Back to Dashboard</a>
                <div class="no-data">
                    <h2>📊 Metrics Trends</h2>
                    <p>Collecting historical data... Trends will be available after a few minutes of operation.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        return render_template_string(html)

    # Prepare data for charts
    timestamps = [s['timestamp'] for s in snapshots]
    time_labels = [time.strftime('%H:%M', time.localtime(ts)) for ts in timestamps]

    # System metrics
    system_cpu = [s['system']['cpu_percent'] for s in snapshots]
    system_memory = [s['system']['memory_percent'] for s in snapshots]

    # Service response times (average for up services)
    service_response_times = {}
    for service in SERVICES.keys():
        times = []
        for snapshot in snapshots:
            if service in snapshot['services']:
                rt = snapshot['services'][service]['response_time']
                if rt:
                    times.append(rt)
        if times:
            service_response_times[service] = times
        else:
            service_response_times[service] = [0] * len(snapshots)

    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trends - AI Stack</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background-color: #f5f5f5; box-sizing: border-box; }
            h1 { color: #333; text-align: center; margin: 10px 0; font-size: 1.5em; }
            .container { max-width: 1400px; margin: 0 auto; padding: 0 10px; }
            .back-link { color: #3498db; text-decoration: none; margin-bottom: 15px; display: inline-block; }
            .back-link:hover { text-decoration: underline; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 15px; font-size: 16px; }
            .refresh-btn:hover { background: #2980b9; }
            .chart-grid { display: grid; grid-template-columns: 1fr; gap: 15px; margin-bottom: 20px; }
            .chart-container { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .chart-container canvas { width: 100% !important; height: 250px !important; }
            .chart-title { font-size: 1.1em; font-weight: bold; margin-bottom: 10px; color: #333; text-align: center; }
            .service-charts { margin-top: 20px; }
            .service-chart { background: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .no-data { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }

            /* Responsive breakpoints */
            @media (min-width: 768px) {
                body { padding: 20px; }
                h1 { font-size: 2em; margin: 20px 0; }
                .container { padding: 0 20px; }
                .chart-grid { grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
                .chart-container { padding: 20px; }
                .chart-container canvas { height: 300px !important; }
                .chart-title { font-size: 1.2em; margin-bottom: 15px; }
                .service-charts { margin-top: 30px; }
                .service-chart { padding: 20px; margin-bottom: 20px; }
            }

            /* Mobile optimizations */
            @media (max-width: 480px) {
                body { padding: 5px; }
                h1 { font-size: 1.2em; }
                .chart-container { padding: 10px; }
                .chart-container canvas { height: 200px !important; }
                .chart-title { font-size: 1em; }
                .service-chart { padding: 10px; }
                .refresh-btn { padding: 8px 16px; font-size: 14px; }
            }
        </style>
        <meta http-equiv="refresh" content="300">
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Dashboard</a>
            <h1>Metrics Trends - AI Stack</h1>
            <button onclick="location.reload()" class="refresh-btn">Refresh Now</button>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 20px;">Auto-refresh every 5 minutes | Showing last {{ snapshots|length }} data points</p>

            <div class="chart-grid">
                <div class="chart-container">
                    <div class="chart-title">System CPU Usage (%)</div>
                    <canvas id="systemCpuChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">System Memory Usage (%)</div>
                    <canvas id="systemMemoryChart"></canvas>
                </div>
            </div>

            <div class="service-charts">
                <h2 style="text-align: center; color: #333;">Service Response Times</h2>
                {% for service, times in service_response_times.items() %}
                <div class="service-chart">
                    <div class="chart-title">{{ SERVICES[service].name }} Response Time (ms)</div>
                    <canvas id="serviceChart{{ loop.index }}"></canvas>
                </div>
                {% endfor %}
            </div>
        </div>

        <script>
            const timeLabels = {{ time_labels | tojson }};
            const systemCpuData = {{ system_cpu | tojson }};
            const systemMemoryData = {{ system_memory | tojson }};
            const serviceData = {{ service_response_times | tojson }};

            // System CPU Chart
            const systemCpuCtx = document.getElementById('systemCpuChart').getContext('2d');
            new Chart(systemCpuCtx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        label: 'CPU %',
                        data: systemCpuData,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });

            // System Memory Chart
            const systemMemoryCtx = document.getElementById('systemMemoryChart').getContext('2d');
            new Chart(systemMemoryCtx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        label: 'Memory %',
                        data: systemMemoryData,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });

            // Service Response Time Charts
            {% for service, times in service_response_times.items() %}
            const serviceCtx{{ loop.index }} = document.getElementById('serviceChart{{ loop.index }}').getContext('2d');
            new Chart(serviceCtx{{ loop.index }}, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: {{ times | tojson }},
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
            {% endfor %}
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, snapshots=snapshots, time_labels=time_labels, system_cpu=system_cpu, system_memory=system_memory, service_response_times=service_response_times, SERVICES=SERVICES)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)