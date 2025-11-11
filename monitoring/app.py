# -*- coding: utf-8 -*-
"""
AI Stack Monitoring Service - Main Application
"""
import os
import threading

from modules.config import SERVICES
from modules.service_monitor import metrics_collection_worker
from modules.routes import create_app

# Create Flask application
app = create_app()

# Start the metrics collection thread
metrics_thread = threading.Thread(target=metrics_collection_worker, daemon=True)
metrics_thread.start()

if __name__ == '__main__':
    # Initialize upstream configuration files
    upstream_dir = '/etc/nginx/upstreams'
    os.makedirs(upstream_dir, exist_ok=True)

    # Create initial dummy upstream configurations
    upstreams = ['dify', 'n8n', 'flowise', 'openwebui', 'litellm', 'monitoring', 'openmemory', 'ollama', 'ollama-webui', 'adminer']
    for upstream in upstreams:
        config_file = os.path.join(upstream_dir, '{}.conf'.format(upstream))
        # Special case for monitoring - it should always be available
        if upstream == 'monitoring':
            server = 'monitoring:8080'
        else:
            server = '127.0.0.1:1'
        with open(config_file, 'w') as f:
            f.write('upstream {} {{\n    server {};\n}}\n'.format(upstream, server))
        print("Created initial upstream config: {}".format(config_file))

    app.run(host='0.0.0.0', port=8080)

# Global service state tracking for nginx reload
SERVICE_STATES = {}  # Track previous service states
NGINX_RELOAD_COOLDOWN = 30  # Minimum seconds between nginx reloads
LAST_NGINX_RELOAD = 0

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Enable CORS for all origins
# CORS(app, resources={
#     r"/*": {
#         "origins": "*",
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
#         "expose_headers": ["X-Custom-Header"],
#         "supports_credentials": False
#     }
# })

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

def reload_nginx():
    """Send reload signal to nginx container"""
    global LAST_NGINX_RELOAD

    # Check cooldown to prevent excessive reloads
    current_time = time.time()
    if current_time - LAST_NGINX_RELOAD < NGINX_RELOAD_COOLDOWN:
        print("Nginx reload skipped - cooldown active")
        return False

    try:
        client = get_docker_client()
        if not client:
            print("Cannot reload nginx - Docker client unavailable")
            return False

        # Find nginx container
        containers = client.containers.list(filters={'name': 'nginx'})
        if not containers:
            print("Nginx container not found")
            return False

        nginx_container = containers[0]

        # Send reload signal (HUP signal)
        nginx_container.kill(signal='HUP')
        LAST_NGINX_RELOAD = current_time
        print("Nginx reload signal sent successfully")
        return True

    except Exception as e:
        print("Error reloading nginx: {}".format(e))
        return False

def update_nginx_upstream(service_name):
    """Update nginx upstream configuration for a service"""
    try:
        # Define service to upstream mappings
        service_upstream_map = {
            'dify-api': ('dify', 'dify-api:8080'),
            'dify-web': ('dify', 'dify-web:3000'),
            'n8n': ('n8n', 'n8n:5678'),
            'flowise': ('flowise', 'flowise:3000'),
            'openwebui': ('openwebui', 'openwebui:8080'),
            'litellm': ('litellm', 'litellm:4000'),
            'openmemory': ('openmemory', 'openmemory:8765'),
            'ollama': ('ollama', 'ollama:11434'),
            'ollama-webui': ('ollama-webui', 'ollama-webui:8080'),
            'adminer': ('adminer', 'adminer:8080'),
        }

        if service_name not in service_upstream_map:
            print("No upstream mapping for service: {}".format(service_name))
            return False

        upstream_name, server_address = service_upstream_map[service_name]

        # Create upstream config file
        upstream_dir = '/etc/nginx/upstreams'
        os.makedirs(upstream_dir, exist_ok=True)

        upstream_config = """upstream {} {{
    server {};
}}
""".format(upstream_name, server_address)

        config_file = os.path.join(upstream_dir, '{}.conf'.format(upstream_name))
        with open(config_file, 'w') as f:
            f.write(upstream_config)

        print("Updated nginx upstream config for {}: {}".format(service_name, config_file))
        return True

    except Exception as e:
        print("Error updating nginx upstream for {}: {}".format(service_name, e))
        return False

def check_service_state_change(service_name, current_status):
    """Check if service state changed from down to up and trigger nginx reload if needed"""
    global SERVICE_STATES

    previous_status = SERVICE_STATES.get(service_name, 'unknown')

    # Track current state
    SERVICE_STATES[service_name] = current_status

    # If service transitioned from down/unknown to up, update nginx upstream and reload
    if previous_status in ['down', 'unknown'] and current_status == 'up':
        print("Service '{}' transitioned from {} to up - updating nginx upstream and reloading".format(service_name, previous_status))
        update_nginx_upstream(service_name)
        reload_nginx()

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

            # Check for state changes and trigger nginx reload if needed
            check_service_state_change(service, status['status'])

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
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Expose-Headers'] = 'X-Custom-Header'

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
    return app.send_static_file('index.html')

@app.route('/api/status')
def api_status():
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

    return {'services': statuses}

@app.route('/logs/<service_name>')
# @requires_auth
def view_logs(service_name):
    return app.send_static_file('logs.html')

@app.route('/api/logs/<service_name>')
# @requires_auth
def api_logs(service_name):
    if service_name not in SERVICES:
        return {'error': 'Service not found'}, 404

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

    return {'logs': filtered_logs}

@app.route('/resources')
# @requires_auth
def resources():
    resources = {}
    for service, info in SERVICES.items():
        resource_data = get_container_resources(service)
        if resource_data:
            resources[service] = dict(resource_data)
            resources[service]['name'] = info['name']

    return render_template('resources.html', resources=resources, format_bytes=format_bytes)

@app.route('/alerts')
# @requires_auth
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

    # Format timestamps for display
    for alert in alerts:
        alert['formatted_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert['timestamp']))

    return render_template('alerts.html', alerts=alerts)

@app.route('/trends')
# @requires_auth
def view_trends():
    with history_lock:
        snapshots = METRICS_HISTORY.get('snapshots', [])

    if not snapshots:
        return render_template('trends.html', snapshots=None)

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

    return render_template('trends.html', snapshots=snapshots, time_labels=time_labels, system_cpu=system_cpu, system_memory=system_memory, service_response_times=service_response_times, SERVICES=SERVICES)

if __name__ == '__main__':
    # Initialize upstream configuration files
    upstream_dir = '/etc/nginx/upstreams'
    os.makedirs(upstream_dir, exist_ok=True)
    
    # Create initial dummy upstream configurations
    upstreams = ['dify', 'n8n', 'flowise', 'openwebui', 'litellm', 'monitoring', 'openmemory', 'ollama', 'ollama-webui', 'adminer']
    for upstream in upstreams:
        config_file = os.path.join(upstream_dir, '{}.conf'.format(upstream))
        # Special case for monitoring - it should always be available
        if upstream == 'monitoring':
            server = 'monitoring:8080'
        else:
            server = '127.0.0.1:1'
        with open(config_file, 'w') as f:
            f.write('upstream {} {{\n    server {};\n}}\n'.format(upstream, server))
        print("Created initial upstream config: {}".format(config_file))
    
    app.run(host='0.0.0.0', port=8080)