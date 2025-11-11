# -*- coding: utf-8 -*-
"""
Docker utilities for container monitoring and management.
"""
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    # Create dummy docker client
    class docker:
        class from_env:
            @staticmethod
            def __call__():
                return None

def get_docker_client():
    """Get Docker client for log monitoring"""
    if not DOCKER_AVAILABLE:
        print("Docker module not available")
        return None
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