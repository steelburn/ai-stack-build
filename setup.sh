#!/bin/bash

# AI Stack Setup Script

# =============================================================================
# INLINE COMMON FUNCTIONS (for compatibility with curl-based installation)
# =============================================================================

# Error logging setup
LOG_FILE="${HOME}/ai-stack-install.log"
exec 2>>"$LOG_FILE"  # Redirect stderr to log file

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$timestamp] [INFO] $1" >> "$LOG_FILE"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$timestamp] [SUCCESS] $1" >> "$LOG_FILE"
}

log_warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$timestamp] [WARNING] $1" >> "$LOG_FILE"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERROR]${NC} $1" >&2
    echo "[$timestamp] [ERROR] $1" >> "$LOG_FILE"
}

# Simple logging functions (without colors, for scripts that don't need them)
log_simple() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Error handling
error_handler() {
    local exit_code=$?
    log_error "Script failed at line $LINENO with exit code $exit_code - Check log file: $LOG_FILE"
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Setup error handling with trap
setup_error_handling() {
    set -e
    trap error_handler ERR
}

# =============================================================================
# END INLINE COMMON FUNCTIONS
# =============================================================================

# Try to source common library (for local development)
if [[ -f "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh" ]]; then
    source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
fi

# Setup error handling
setup_error_handling

log_info "Setup script started"

# Function to validate required environment variables
validate_environment() {
    log_info "🔍 Validating environment configuration..."

    local missing_vars=()

    # Check for .env file and create from template if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_info "📋 Creating .env file from template..."
            cp .env.example .env
            log_simple "INFO" "Created .env file from .env.example"
        else
            log_error ".env file not found and .env.example template is missing."
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
        log_error "Missing required environment variables:"
        printf '  - %s\n' "${missing_vars[@]}"
        echo ""
        echo "Please check your .env file and ensure all required variables are set."
        echo "You can copy from .env.example: cp .env.example .env"
        exit 1
    fi

    log_success "Environment validation passed!"
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

# Prompt for public domain configuration
echo "🌐 Configuring public domain..."
echo "This will be used for proper URL configuration in production."
echo "For development, you can use 'https://localhost'"
echo "For production, use your actual domain like 'https://yourdomain.com'"
echo ""

# Check if PUBLIC_DOMAIN is already set
if [ -f ".env" ] && grep -q "^PUBLIC_DOMAIN=" .env; then
    current_domain=$(grep "^PUBLIC_DOMAIN=" .env | cut -d'=' -f2)
    echo "Current public domain: $current_domain"
    read -p "Do you want to change it? [y/N]: " change_domain
    if [[ "$change_domain" =~ ^[Yy]$ ]]; then
        read -p "Enter your public domain (e.g., https://yourdomain.com): " PUBLIC_DOMAIN
    else
        PUBLIC_DOMAIN="$current_domain"
    fi
else
    read -p "Enter your public domain (e.g., https://yourdomain.com or https://localhost for development): " PUBLIC_DOMAIN
fi

# Validate the domain format
if [[ ! "$PUBLIC_DOMAIN" =~ ^https?:// ]]; then
    log_warning "Invalid domain format. Must start with http:// or https://"
    log_info "Using default: https://localhost"
    PUBLIC_DOMAIN="https://localhost"
fi

# Update .env file with PUBLIC_DOMAIN
if [ -f ".env" ]; then
    if grep -q "^PUBLIC_DOMAIN=" .env; then
        sed -i "s|^PUBLIC_DOMAIN=.*$|PUBLIC_DOMAIN=${PUBLIC_DOMAIN}|" .env
    else
        echo "PUBLIC_DOMAIN=${PUBLIC_DOMAIN}" >> .env
    fi
else
    echo "PUBLIC_DOMAIN=${PUBLIC_DOMAIN}" > .env
fi

log_success "Public domain set to: $PUBLIC_DOMAIN"

# Source the .env file to get current values
if [ -f ".env" ]; then
    source .env
fi

# Port assignments and conflict resolution
log_info "🔌 Assigning available ports for services..."

# Define service ports with defaults
declare -A service_ports=(
    ["MONITORING_PORT"]="5000"
    ["OLLAMA_WEBUI_PORT"]="8081"
    ["LITELLM_PORT"]="4000"
    ["N8N_PORT"]="5678"
    ["FLOWISE_PORT"]="3000"
    ["SUPABASE_PORT"]="54322"
    ["OPENWEBUI_PORT"]="8082"
    ["DIFY_WEB_PORT"]="3001"
    ["DIFY_API_PORT"]="5001"
    ["ADMINER_PORT"]="8083"
    ["NGINX_HTTP_PORT"]="8080"
    ["RABBITMQ_PORT"]="5672"
    ["RABBITMQ_MANAGEMENT_PORT"]="15672"
    ["DOCKETY_PORT"]="8090"
)

# Function to update .env file
update_env_port() {
    local var_name=$1
    local new_value=$2
    if [ -f ".env" ]; then
        sed -i "s/^${var_name}=.*$/${var_name}=${new_value}/" .env
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Updated ${var_name} to ${new_value} in .env" >> "$LOG_FILE"
    fi
}

# Check and assign ports
for var in "${!service_ports[@]}"; do
    default_port=${service_ports[$var]}
    current_port=${!var:-$default_port}
    
    if check_port "$current_port"; then
        log_warning "Port $current_port (${var}) is already in use. Finding alternative..."
        new_port=$(find_available_port $((current_port + 1)))
        if [ $? -eq 0 ]; then
            update_env_port "$var" "$new_port"
            log_success "${var} port changed to $new_port"
        else
            log_error "Could not find available port for ${var}"
        fi
    else
        log_info "Port $current_port (${var}) is available"
        # Ensure it's set in .env
        if ! grep -q "^${var}=" .env; then
            echo "${var}=${current_port}" >> .env
        fi
    fi
done

# Special check for Nginx HTTPS (443)
if check_port 443; then
    log_warning "Port 443 (Nginx HTTPS) is already in use. Finding alternative..."
    NEW_NGINX_HTTPS_PORT=$(find_available_port 8443)
    if [ $? -eq 0 ]; then
        update_docker_compose_port "nginx" "443:443" "${NEW_NGINX_HTTPS_PORT}:443"
        log_success "Nginx HTTPS port changed to $NEW_NGINX_HTTPS_PORT"
    fi
else
    log_info "Port 443 (Nginx HTTPS) is available"
fi

log_success "Port conflict resolution complete"

# Check if Docker is installed
if ! command_exists docker; then
    log_info "🐳 Docker not found. Installing Docker Engine..."
    # Install Docker silently
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh > /dev/null 2>&1

    # Add user to docker group
    sudo usermod -aG docker $(whoami) > /dev/null 2>&1

    # Start and enable Docker service
    sudo systemctl enable docker > /dev/null 2>&1
    sudo systemctl start docker > /dev/null 2>&1

    log_success "Docker installed successfully"
    log_warning "Please log out and back in for Docker group changes to take effect"
else
    log_info "✅ Docker is already installed"
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose V2 not found. Installing..."
    # Docker Compose V2 is included with Docker Engine now
    log_info "Docker Compose should be available with Docker Engine. Please restart your terminal session."
    exit 1
else
    log_info "✅ Docker Compose is available"
fi

# Create necessary directories
log_info "📁 Creating directories..."
mkdir -p config
mkdir -p volumes

# .env file is now created in validate_environment() if needed
log_success ".env file ready"

# Pull images
log_info "📦 Pulling Docker images..."
docker compose pull

# Ensure Docker Compose build is run (use Docker Compose V2 syntax)
log_info "🚀 Building Docker images..."
docker compose build

# Ensure memory overcommit is enabled for Redis
sudo sysctl -w vm.overcommit_memory=1

# Make the change persistent
if ! grep -q '^vm.overcommit_memory=1' /etc/sysctl.conf; then
  echo 'vm.overcommit_memory=1' | sudo tee -a /etc/sysctl.conf
fi

log_success "Setup complete!"
echo ""
echo "🌐 Access your services:"

# Get actual ports from docker-compose.yml
LITELLM_PORT=$(grep -A1 "litellm:" docker-compose.yml | grep "ports:" -A1 | grep -o '"[0-9]*:4000"' | cut -d'"' -f2 | cut -d':' -f1 || echo "4000")
SUPABASE_PORT=$(grep -A1 "supabase:" docker-compose.yml | grep "ports:" -A1 | grep -o '"[0-9]*:5432"' | cut -d'"' -f2 | cut -d':' -f1 || echo "54322")
NGINX_HTTP_PORT=$(grep -A2 "nginx:" docker-compose.yml | grep "ports:" -A2 | grep '"8080:80"' | cut -d'"' -f2 | cut -d':' -f1 || echo "8080")
NGINX_HTTPS_PORT=$(grep -A2 "nginx:" docker-compose.yml | grep "ports:" -A2 | grep '"443:443"' | cut -d'"' -f2 | cut -d':' -f1 || echo "443")

# Get PUBLIC_DOMAIN from .env file
PUBLIC_DOMAIN=$(grep "^PUBLIC_DOMAIN=" .env | cut -d'=' -f2 || echo "https://localhost")

echo "  Dify:        $PUBLIC_DOMAIN/dify"
echo "  N8N:         $PUBLIC_DOMAIN/n8n"
echo "  Flowise:     $PUBLIC_DOMAIN/flowise"
echo "  OpenWebUI:   $PUBLIC_DOMAIN/openwebui"
echo "  LiteLLM:     $PUBLIC_DOMAIN/litellm"
echo "  Monitoring:  $PUBLIC_DOMAIN/monitoring"
echo "  Adminer:     $PUBLIC_DOMAIN/adminer"
echo "  Dockety:     $PUBLIC_DOMAIN/dockety"
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