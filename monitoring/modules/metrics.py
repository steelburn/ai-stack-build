# -*- coding: utf-8 -*-
"""
Prometheus metrics setup and configuration.
"""
import threading

try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for when prometheus is not available
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def set(self, value):
            pass

    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def inc(self):
            pass

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def observe(self, value):
            pass

    def generate_latest():
        return b"# Prometheus metrics not available"

    CONTENT_TYPE_LATEST = 'text/plain; version=0.0.4; charset=utf-8'

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