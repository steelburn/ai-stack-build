#!/bin/bash

# AI Stack Setup Script

# Error logging setup (same as installer)
LOG_FILE="${HOME}/ai-stack-install.log"
exec 2>>"$LOG_FILE"  # Redirect stderr to log file

# Error handling
error_handler() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Setup failed at line $LINENO with exit code $? - Check log file: $LOG_FILE" >> "$LOG_FILE"
    exit 1
}
trap error_handler ERR

echo "🚀 Setting up AI Stack..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Setup script started" >> "$LOG_FILE"

# Function to validate required environment variables
validate_environment() {
    echo "🔍 Validating environment configuration..."
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Validating environment variables" >> "$LOG_FILE"

    local missing_vars=()

    # Check for .env file and create from template if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo "📋 Creating .env file from template..."
            cp .env.example .env
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Created .env file from .env.example" >> "$LOG_FILE"
        else
            echo "❌ .env file not found and .env.example template is missing."
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Both .env and .env.example files not found" >> "$LOG_FILE"
            exit 1
        fi
    fi

    # Required environment variables
    local required_vars=(
        "DB_HOST"
        "DB_PORT"
        "DB_USERNAME"
        "DB_PASSWORD"
        "DB_DATABASE"
        "REDIS_HOST"
        "REDIS_PORT"
        "REDIS_PASSWORD"
        "VECTOR_STORE"
        "QDRANT_URL"
        "QDRANT_API_KEY"
        "STORAGE_TYPE"
        "STORAGE_LOCAL_PATH"
    )

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ Missing required environment variables:"
        printf '  - %s\n' "${missing_vars[@]}"
        echo ""
        echo "Please check your .env file and ensure all required variables are set."
        echo "You can copy from .env.example: cp .env.example .env"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Missing environment variables: ${missing_vars[*]}" >> "$LOG_FILE"
        exit 1
    fi

    echo "✅ Environment validation passed!"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Environment validation passed" >> "$LOG_FILE"
}

# Function to check if a port is in use
check_port() {
    local port=$1

    # Try lsof first (most reliable)
    if command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0  # Port is in use
        fi
    # Fallback to netstat
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            return 0  # Port is in use
        fi
    # Fallback to ss
    elif command -v ss >/dev/null 2>&1; then
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            return 0  # Port is in use
        fi
    # Last resort - try to bind to the port
    else
        if timeout 1 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
            return 0  # Port is in use
        fi
    fi

    return 1  # Port is free
}

# Function to find an available port starting from a base port
find_available_port() {
    local base_port=$1
    local port=$base_port
    local max_attempts=100
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if ! check_port $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
        attempt=$((attempt + 1))
    done

    echo "ERROR: Could not find available port starting from $base_port" >&2
    return 1
}

# Function to update port in docker-compose.yml
update_docker_compose_port() {
    local service=$1
    local old_port=$2
    local new_port=$3

    if [ -f "docker-compose.yml" ]; then
        sed -i "s/- \"$old_port:/- \"$new_port:/g" docker-compose.yml
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Updated $service port from $old_port to $new_port in docker-compose.yml" >> "$LOG_FILE"
    fi
}

# Function to update port in nginx config
update_nginx_port() {
    local service=$1
    local old_port=$2
    local new_port=$3

    if [ -f "nginx/nginx.conf" ]; then
        sed -i "s/$service:$old_port/$service:$new_port/g" nginx/nginx.conf
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Updated $service port from $old_port to $new_port in nginx.conf" >> "$LOG_FILE"
    fi
}

# Validate environment before proceeding
validate_environment

# Port conflict resolution
echo "🔍 Checking for port conflicts..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Checking for port conflicts" >> "$LOG_FILE"

# Check and resolve LiteLLM port (4000)
if check_port 4000; then
    echo "⚠️  Port 4000 (LiteLLM) is already in use. Finding alternative..."
    NEW_LITELLM_PORT=$(find_available_port 4001)
    if [ $? -eq 0 ]; then
        update_docker_compose_port "litellm" "4000:4000" "${NEW_LITELLM_PORT}:4000"
        update_nginx_port "litellm" "4000" "$NEW_LITELLM_PORT"
        echo "✅ LiteLLM port changed to $NEW_LITELLM_PORT"
    fi
else
    echo "✅ Port 4000 (LiteLLM) is available"
fi

# Check and resolve Supabase port (54322)
if check_port 54322; then
    echo "⚠️  Port 54322 (Supabase) is already in use. Finding alternative..."
    NEW_SUPABASE_PORT=$(find_available_port 54323)
    if [ $? -eq 0 ]; then
        update_docker_compose_port "supabase" "54322:5432" "${NEW_SUPABASE_PORT}:5432"
        echo "✅ Supabase port changed to $NEW_SUPABASE_PORT"
    fi
else
    echo "✅ Port 54322 (Supabase) is available"
fi

# Check and resolve Nginx HTTP port (8080)
if check_port 8080; then
    echo "⚠️  Port 8080 (Nginx HTTP) is already in use. Finding alternative..."
    NEW_NGINX_HTTP_PORT=$(find_available_port 8081)
    if [ $? -eq 0 ]; then
        update_docker_compose_port "nginx" "8080:80" "${NEW_NGINX_HTTP_PORT}:80"
        echo "✅ Nginx HTTP port changed to $NEW_NGINX_HTTP_PORT"
    fi
else
    echo "✅ Port 8080 (Nginx HTTP) is available"
fi

# Check and resolve Nginx HTTPS port (443)
if check_port 443; then
    echo "⚠️  Port 443 (Nginx HTTPS) is already in use. Finding alternative..."
    NEW_NGINX_HTTPS_PORT=$(find_available_port 8443)
    if [ $? -eq 0 ]; then
        update_docker_compose_port "nginx" "443:443" "${NEW_NGINX_HTTPS_PORT}:443"
        echo "✅ Nginx HTTPS port changed to $NEW_NGINX_HTTPS_PORT"
    fi
else
    echo "✅ Port 443 (Nginx HTTPS) is available"
fi

echo "✅ Port conflict resolution complete"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Docker not found. Installing Docker Engine..."
    # Install Docker silently
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh > /dev/null 2>&1

    # Add user to docker group
    sudo usermod -aG docker $(whoami) > /dev/null 2>&1

    # Start and enable Docker service
    sudo systemctl enable docker > /dev/null 2>&1
    sudo systemctl start docker > /dev/null 2>&1

    echo "✅ Docker installed successfully"
    echo "⚠️  Please log out and back in for Docker group changes to take effect"
else
    echo "✅ Docker is already installed"
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose V2 not found. Installing..."
    # Docker Compose V2 is included with Docker Engine now
    echo "Docker Compose should be available with Docker Engine. Please restart your terminal session."
    exit 1
else
    echo "✅ Docker Compose is available"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p config
mkdir -p volumes

# .env file is now created in validate_environment() if needed
echo "✅ .env file ready"

# Pull images
echo "📦 Pulling Docker images..."
docker compose pull

echo "✅ Setup complete!"
echo ""
echo "🌐 Access your services:"

# Get actual ports from docker-compose.yml
LITELLM_PORT=$(grep -A1 "litellm:" docker-compose.yml | grep "ports:" -A1 | grep -o '"[0-9]*:4000"' | cut -d'"' -f2 | cut -d':' -f1 || echo "4000")
SUPABASE_PORT=$(grep -A1 "supabase:" docker-compose.yml | grep "ports:" -A1 | grep -o '"[0-9]*:5432"' | cut -d'"' -f2 | cut -d':' -f1 || echo "54322")
NGINX_HTTP_PORT=$(grep -A2 "nginx:" docker-compose.yml | grep "ports:" -A2 | grep '"8080:80"' | cut -d'"' -f2 | cut -d':' -f1 || echo "8080")
NGINX_HTTPS_PORT=$(grep -A2 "nginx:" docker-compose.yml | grep "ports:" -A2 | grep '"443:443"' | cut -d'"' -f2 | cut -d':' -f1 || echo "443")

echo "  Dify:        https://localhost:$NGINX_HTTPS_PORT/dify"
echo "  N8N:         https://localhost:$NGINX_HTTPS_PORT/n8n"
echo "  Flowise:     https://localhost:$NGINX_HTTPS_PORT/flowise"
echo "  OpenWebUI:   https://localhost:$NGINX_HTTPS_PORT/openwebui"
echo "  LiteLLM:     https://localhost:$NGINX_HTTPS_PORT/litellm"
echo "  Monitoring:  https://localhost:$NGINX_HTTPS_PORT/monitoring"
echo "  Adminer:     https://localhost:$NGINX_HTTPS_PORT/adminer"
echo ""
echo "  Direct access (if needed):"
echo "  LiteLLM API: http://localhost:$LITELLM_PORT"
echo "  Supabase:    localhost:$SUPABASE_PORT"
echo ""
echo "📝 Useful commands:"
echo "  - View status:    make status"
echo "  - View logs:      make logs"
echo "  - Stop services:  make down"
echo "  - Pull models:    make pull-models"
echo "  - Show help:      make help"
echo ""
echo "📝 Remember to:"
echo "  - Change default passwords in .env"
echo "  - Pull models in Ollama: make pull-models"
echo "  - Check logs: make logs"