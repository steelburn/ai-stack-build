# -*- coding: utf-8 -*-
"""
Flask routes and middleware for the monitoring service.
"""
import time
import os
from functools import wraps
from flask import Flask, render_template, request, Response
import psutil

from .config import SERVICES
from .docker_utils import get_docker_client, get_container_logs, get_container_resources, format_bytes
from .service_monitor import check_service, check_auth
from .metrics import (
    system_cpu_percent, system_memory_percent, system_disk_usage_percent,
    container_cpu_percent, container_memory_percent, container_memory_usage,
    container_network_rx, container_network_tx, http_requests_total,
    http_request_duration, generate_latest, CONTENT_TYPE_LATEST,
    METRICS_HISTORY, history_lock
)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # Enable CORS for all origins (commented out as in original)
    # CORS(app, resources={
    #     r"/*": {
    #         "origins": "*",
    #         "methods": ["GET", "POST", "OPTIONS"],
    #         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    #         "expose_headers": ["X-Custom-Header"],
    #         "supports_credentials": False
    #     }
    # })

    # Authentication decorator (commented out)
    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return Response(
                    'Authentication required', 401,
                    {'WWW-Authenticate': 'Basic realm="Monitoring Dashboard"'}
                )
            return f(*args, **kwargs)
        return decorated

    # Request tracing middleware
    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            # Track request duration for monitoring endpoints
            if request.endpoint in ['index', 'resources', 'view_alerts', 'metrics']:
                http_request_duration.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(duration)

        # Add security headers
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
                        'message': 'High CPU usage: {}%'.format(resource_data["cpu_percent"]),
                        'timestamp': current_time,
                        'severity': 'warning'
                    })

                if resource_data['memory_percent'] > 85:
                    alerts.append({
                        'type': 'error',
                        'service': info['name'],
                        'message': 'High memory usage: {}%'.format(resource_data["memory_percent"]),
                        'timestamp': current_time,
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

    return app