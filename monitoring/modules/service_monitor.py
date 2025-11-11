# -*- coding: utf-8 -*-
"""
Service monitoring and health checking utilities.
"""
import time
import os
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Create dummy psutil module
    class psutil:
        @staticmethod
        def cpu_percent(interval=1):
            return 0.0
        @staticmethod
        def virtual_memory():
            class Memory:
                percent = 0.0
            return Memory()

import threading
try:
    from prometheus_client import Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def set(self, value):
            pass

from .config import SERVICES, SERVICE_STATES, LAST_NGINX_RELOAD, NGINX_RELOAD_COOLDOWN, METRICS_HISTORY, HISTORY_MAX_POINTS
from .metrics import history_lock
from .docker_utils import get_docker_client

# Prometheus Metrics
service_up = Gauge('ai_stack_service_up', 'Service health status (1=up, 0=down)', ['service'])
service_response_time = Gauge('ai_stack_service_response_time_ms', 'Service response time in milliseconds', ['service'])

def check_service(url, name):
    """Check service health by making HTTP request"""
    try:
        import requests
    except ImportError:
        return {'status': 'down', 'response_time': None, 'error': 'requests module not available'}
    
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
            from .docker_utils import get_container_resources
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

def metrics_collection_worker():
    """Background worker to collect metrics periodically"""
    while True:
        try:
            store_metrics_snapshot()
        except Exception as e:
            print("Error collecting metrics: {}".format(e))
        time.sleep(60)  # Collect every minute

def check_auth(username, password):
    """Check basic authentication credentials"""
    expected_username = os.getenv('MONITORING_USERNAME') or read_secret_file('/run/secrets/monitoring_username')
    expected_password = os.getenv('MONITORING_PASSWORD') or read_secret_file('/run/secrets/monitoring_password')
    return username == expected_username and password == expected_password

def read_secret_file(filepath):
    """Read secret from file"""
    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except:
        return None