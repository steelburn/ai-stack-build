from flask import Flask, render_template, request, jsonify
import psycopg2
import os
import json
from dotenv import load_dotenv
import docker

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Load environment variables
load_dotenv()

# Initialize Docker client using API
docker_socket_path = '/var/run/docker.sock'
docker_available = os.path.exists(docker_socket_path) and os.access(docker_socket_path, os.R_OK)

if docker_available:
    try:
        # Use Docker client with Unix socket
        docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        # Test the connection
        docker_client.ping()
    except Exception as e:
        print(f"Docker client initialization failed: {e}")
        docker_client = None
        docker_available = False
else:
    docker_client = None

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        database=os.getenv('POSTGRES_DB', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        port=os.getenv('POSTGRES_PORT', '5432')
    )

@app.route('/')
def index():
    print("Index route called")
    return render_template('index.html')

@app.route('/api/services')
def get_services():
    if not docker_available:
        return jsonify({'error': 'Docker socket not available'}), 503
    
    try:
        # Get list of containers using Docker client
        containers = docker_client.containers.list(all=True)
        services = []
        for container in containers:
            services.append({
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else container.image.id
            })
        return jsonify(services)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/restart/<service_name>', methods=['POST'])
def restart_service(service_name):
    if not docker_available:
        return jsonify({'status': 'error', 'message': 'Docker socket not available'})
    
    try:
        # Restart container using Docker client
        container = docker_client.containers.get(service_name)
        container.restart()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/nginx/reload', methods=['POST'])
def reload_nginx():
    if not docker_available:
        return jsonify({'status': 'error', 'message': 'Docker socket not available'})
    
    try:
        # Execute nginx reload command using Docker client
        container = docker_client.containers.get('ai-stack-nginx-1')
        result = container.exec_run('nginx -s reload')
        if result.exit_code == 0:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': result.output.decode()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/config/files')
def list_config_files():
    config_files = [
        {'path': 'nginx/nginx.conf', 'description': 'Nginx reverse proxy configuration'},
        {'path': 'docker-compose.yml', 'description': 'Docker services configuration'},
        {'path': '.env', 'description': 'Environment variables'},
        {'path': 'secrets/', 'description': 'Secret files directory'},
        {'path': 'config/postgres-init/init-databases.sql', 'description': 'Database initialization'}
    ]
    return jsonify(config_files)

@app.route('/api/config/file/<path:file_path>')
def get_config_file(file_path):
    try:
        full_path = os.path.join('/workspace', file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read()
            return jsonify({'content': content, 'path': file_path})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/file/<path:file_path>', methods=['POST'])
def update_config_file(file_path):
    try:
        data = request.json
        content = data.get('content', '')
        
        full_path = os.path.join('/workspace', file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/database/query', methods=['POST'])
def execute_db_query():
    try:
        data = request.json
        query = data.get('query', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if query.strip().upper().startswith('SELECT'):
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()
            return jsonify({'results': results, 'columns': columns})
        else:
            cursor.execute(query)
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'status': 'success', 'affected_rows': cursor.rowcount})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)