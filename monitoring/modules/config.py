# -*- coding: utf-8 -*-
"""
Configuration and constants for the AI Stack monitoring service.
"""
import os
import json

# -*- coding: utf-8 -*-
"""
Configuration and constants for the AI Stack monitoring service.
"""
import os
import json

# Global service state tracking for nginx reload
SERVICE_STATES = {}  # Track previous service states
NGINX_RELOAD_COOLDOWN = 30  # Minimum seconds between nginx reloads
LAST_NGINX_RELOAD = 0

# Import metrics history from metrics module
from .metrics import METRICS_HISTORY, HISTORY_MAX_POINTS

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

# Load services configuration
SERVICES = load_services()