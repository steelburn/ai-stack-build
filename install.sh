#!/bin/bash

# AI Stack Build - One-line installer
# Version: 1.1.0
# Usage: curl -fsSL https://raw.githubusercontent.com/steelburn/ai-stack-build/main/install.sh | bash

set -e

# Error logging setup
LOG_FILE="${HOME}/ai-stack-install.log"
exec 2>>"$LOG_FILE"  # Redirect stderr to log file

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/steelburn/ai-stack-build.git"
REPO_NAME="ai-stack-build"
INSTALL_DIR="${HOME}/${REPO_NAME}"

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

# Error handling
trap 'log_error "Installer failed at line $LINENO with exit code $?"; log_info "Check log file: $LOG_FILE"; exit 1' ERR

# Log script start
log_info "=== AI Stack Build Installer Started ==="
log_info "Log file: $LOG_FILE"

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "This installer is designed for Linux systems only."
        exit 1
    fi

    # Check if running as root (not recommended for Docker)
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended. Please run as a regular user."
    fi

    # Check for required commands
    local missing_deps=()

    if ! command_exists git; then
        missing_deps+=("git")
    fi

    if ! command_exists curl; then
        missing_deps+=("curl")
    fi

    if ! command_exists docker; then
        missing_deps+=("docker")
    fi

    if ! command_exists make; then
        missing_deps+=("make")
    fi

    if ! command_exists openssl; then
        missing_deps+=("openssl")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install them using your package manager:"
        log_info "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y ${missing_deps[*]}"
        log_info "  CentOS/RHEL: sudo yum install -y ${missing_deps[*]}"
        log_info "  macOS: brew install ${missing_deps[*]}"
        exit 1
    fi

    log_success "All system requirements met!"
}

# Install Docker if not present (optional)
install_docker() {
    if ! command_exists docker; then
        log_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh

        # Add user to docker group (if not root)
        if [[ $EUID -ne 0 ]]; then
            sudo usermod -aG docker $USER
            log_warning "Added $USER to docker group. You may need to log out and back in for this to take effect."
        fi

        log_success "Docker installed successfully!"
    else
        log_info "Docker is already installed."
    fi
}

# Clone or update repository
setup_repository() {
    log_info "Setting up AI Stack Build repository..."

    if [ -d "$INSTALL_DIR" ]; then
        log_warning "Directory $INSTALL_DIR already exists. Updating..."
        cd "$INSTALL_DIR"
        git pull origin main
    else
        log_info "Cloning repository to $INSTALL_DIR..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi

    log_success "Repository ready!"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."

    if [ ! -f "nginx/ssl/nginx-selfsigned.crt" ] || [ ! -f "nginx/ssl/nginx-selfsigned.key" ]; then
        if [ -f "generate-ssl.sh" ]; then
            log_info "Generating self-signed SSL certificates..."
            ./generate-ssl.sh
            log_success "SSL certificates generated!"
        else
            log_warning "generate-ssl.sh not found. SSL certificates may need to be created manually."
        fi
    else
        log_info "SSL certificates already exist."
    fi
}

# Generate secrets
generate_secrets() {
    log_info "Generating secrets..."

    if [ -f "generate-secrets.sh" ]; then
        # Check if secrets already exist
        if [ -d "secrets" ] && [ "$(ls -A secrets)" ]; then
            log_warning "Secrets directory already exists and is not empty. Skipping secret generation."
            log_info "If you want to regenerate secrets, remove the secrets directory first."
        else
            log_info "Running secret generation script..."
            ./generate-secrets.sh
            log_success "Secrets generated!"
        fi
    else
        log_warning "generate-secrets.sh not found. You may need to generate secrets manually."
    fi
}

# Ensure memory overcommit is enabled for Redis
enable_memory_overcommit() {
    log_info "Configuring memory overcommit for Redis..."

    # Check current overcommit setting
    local current_setting
    current_setting=$(sysctl vm.overcommit_memory | awk '{print $3}')

    if [ "$current_setting" -ne 1 ]; then
        log_info "Enabling memory overcommit (current setting: $current_setting)..."
        sudo sysctl -w vm.overcommit_memory=1

        # Make the change persistent
        if ! grep -q '^vm.overcommit_memory=1' /etc/sysctl.conf; then
            echo 'vm.overcommit_memory=1' | sudo tee -a /etc/sysctl.conf
            log_success "Memory overcommit enabled and set to persist across reboots."
        else
            log_success "Memory overcommit enabled."
        fi
    else
        log_info "Memory overcommit is already enabled (current setting: $current_setting)."
    fi
}

# Setup Docker services
setup_services() {
    log_info "Setting up Docker services..."

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Run setup
    if [ -f "setup.sh" ]; then
        log_info "Running setup script..."
        ./setup.sh
    else
        log_warning "setup.sh not found. You may need to set up services manually."
    fi

    log_success "Services setup complete!"
}

# Start services
start_services() {
    log_info "Starting AI Stack Build services..."

    # Try to pull images first to detect missing/private images
    check_and_pull_images

    if command_exists make; then
        make up
        log_success "Services started! Use 'make status' to check status."
    else
        log_warning "Make not found. Please start services manually with: docker compose up -d"
    fi
}

# Ensure Docker Compose build is run
ensure_docker_compose_build() {
    log_info "Building Docker images..."

    if [ -f "docker-compose.yml" ]; then
        docker-compose build
        log_success "Docker images built successfully!"
    else
        log_warning "docker-compose.yml not found; skipping Docker image build."
    fi
}

# Check images defined in docker-compose.yml and attempt to pull them.
# If pull fails for any image, prompt the user to docker login or provide an override.
check_and_pull_images() {
    COMPOSE_FILE="docker-compose.yml"
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_warning "$COMPOSE_FILE not found; skipping image pull checks."
        return
    fi

    log_info "Checking images referenced in $COMPOSE_FILE..."
    mapfile -t images < <(grep -E "^\s*image:\s*" "$COMPOSE_FILE" | sed -E 's/^\s*image:\s*//') || true
    if [ ${#images[@]} -eq 0 ]; then
        log_info "No images found in compose file (build-only services)."
        return
    fi

    local failed=()

    for img in "${images[@]}"; do
        # skip empty and local build names
        img_trimmed=$(echo "$img" | tr -d '"')
        if [ -z "$img_trimmed" ]; then
            continue
        fi
        # Skip local build references (not an image)
        if echo "$img_trimmed" | grep -q "^\./"; then
            continue
        fi

        log_info "Attempting to pull image: $img_trimmed"
        if ! docker pull "$img_trimmed" >/dev/null 2>&1; then
            log_warning "Failed to pull image: $img_trimmed"
            failed+=("$img_trimmed")
        else
            log_info "Pulled: $img_trimmed"
        fi
    done

    if [ ${#failed[@]} -ne 0 ]; then
        echo
        log_error "The following images failed to pull: ${failed[*]}"
        echo
        log_info "Common causes: private registry requiring authentication, image removed, or mis-typed image name."
        echo
        log_info "Options:"
        echo "  1) Run 'docker login' with credentials for the registry and re-run the installer."
        echo "  2) Provide an image override via environment variables before running installer, e.g.:"
        echo "       PROBLEMATIC_IMAGE=your-public/alternative:latest curl -fsSL <url> | bash"
        echo "  3) Remove/disable optional services in docker-compose.yml that reference private images."
        echo
        read -p "Would you like to attempt 'docker login' now? [y/N]: " resp
        resp=${resp:-N}
        if [[ "$resp" =~ ^[Yy]$ ]]; then
            log_info "Starting 'docker login'..."
            docker login || { log_error "docker login failed."; exit 1; }
            log_info "Re-attempting to pull failed images..."
            for img in "${failed[@]}"; do
                docker pull "$img" || { log_error "Still cannot pull $img after login. Aborting."; exit 1; }
            done
            log_success "All previously failed images pulled successfully after login."
        else
            log_error "Image pull failures detected. Installer cannot continue until the images are available or overrides are provided."
            exit 1
        fi
    fi
}

# Show completion message
show_completion() {
    log_success "AI Stack Build installation completed!"

    # Get actual ports from docker-compose.yml
    NGINX_HTTPS_PORT=$(grep -A2 "nginx:" docker-compose.yml | grep "ports:" -A2 | grep '"443:443"' | cut -d'"' -f2 | cut -d':' -f1 2>/dev/null || echo "443")

    echo
    echo "Next steps:"
    echo "  1. Edit the .env file with your configuration"
    echo "  2. Run 'make status' to check service status"
    echo "  3. Access the monitoring dashboard at: https://localhost:$NGINX_HTTPS_PORT/monitoring"
    echo "  4. Run 'make logs' to view service logs"
    echo
    echo "Useful commands:"
    echo "  make up        - Start all services"
    echo "  make down      - Stop all services"
    echo "  make restart   - Restart all services"
    echo "  make status    - Show service status"
    echo "  make logs      - Show service logs"
    echo "  make health    - Run health checks"
    echo
    echo "Troubleshooting:"
    echo "  Log file: $LOG_FILE"
    echo "  Run 'tail -f $LOG_FILE' to monitor installation logs"
    echo "  Run 'cat $LOG_FILE' to view complete installation log"
    echo
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Installation log: $LOG_FILE"
}

# Main installation function
main() {
    echo
    log_info "🚀 AI Stack Build - One-line Installer"
    log_info "====================================="
    echo

    log_info "Starting installation process..."

    log_info "Step 1: Checking system requirements..."
    check_requirements

    log_info "Step 2: Setting up repository..."
    setup_repository

    log_info "Step 3: Setting up SSL certificates..."
    setup_ssl

    log_info "Step 4: Setting up services..."
    setup_services

    log_info "Step 5: Generating secrets..."
    generate_secrets

    log_info "Step 6: Enabling memory overcommit for Redis..."
    enable_memory_overcommit

    log_info "Step 7: Starting services..."
    start_services

    log_info "Step 8: Building Docker images..."
    ensure_docker_compose_build

    log_info "Step 9: Installation complete!"
    show_completion

    echo
    log_success "🎉 Installation complete! Welcome to AI Stack Build!"
    log_info "=== AI Stack Build Installer Completed Successfully ==="
}

# Run main function
main "$@"