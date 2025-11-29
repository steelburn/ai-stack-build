from flask import Flask, render_template, request, jsonify
import docker
import psycopg2
import os
import json
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Docker client
import docker
docker_client = docker.APIClient(base_url='unix:///var/run/docker.sock')

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'db'),
        database=os.getenv('POSTGRES_DB', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'password')
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/services')
def get_services():
    containers = docker_client.containers()
    return jsonify([{
        'id': s['Id'],
        'name': s['Names'][0] if s['Names'] else 'unknown',
        'status': s['Status'],
        'image': s['Image']
    } for s in containers])

@app.route('/api/restart/<service_name>', methods=['POST'])
def restart_service(service_name):
    try:
        docker_client.restart(service_name)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/config/<service_name>')
def get_config(service_name):
    # Placeholder for getting service config
    # This would read from config files or env
    return jsonify({'config': f'Config for {service_name}'})

@app.route('/api/config/<service_name>', methods=['POST'])
def update_config(service_name):
    data = request.json
    # Placeholder for updating config
    # This would write to files or db
    return jsonify({'status': 'updated'})

@app.route('/api/nginx/reload', methods=['POST'])
def reload_nginx():
    try:
        exec_result = docker_client.exec_create('ai-stack-nginx-1', 'nginx -s reload')
        docker_client.exec_start(exec_result)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)