#!/bin/bash

# AI Stack Configuration Service Deployment Script
# This script deploys the config service to a remote server

set -e

echo "🚀 Deploying AI Stack Configuration Service to remote server..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're running on the correct server
if [[ "$(hostname -I | awk '{print $1}')" != "192.168.88.120" ]]; then
    print_warning "This script is designed to run on 192.168.88.120"
    print_warning "Current IP: $(hostname -I | awk '{print $1}')"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Navigate to the project directory (adjust path as needed)
PROJECT_DIR="/home/steelburn/Development/ai-stack-build"
if [[ ! -d "$PROJECT_DIR" ]]; then
    print_error "Project directory not found: $PROJECT_DIR"
    print_error "Please ensure the ai-stack-build repository is cloned to the correct location."
    exit 1
fi

cd "$PROJECT_DIR"

print_status "Building and starting the configuration service..."

# Stop any existing config-service container
docker-compose stop config-service || true
docker-compose rm -f config-service || true

# Build and start the config service
docker-compose build config-service
docker-compose up -d config-service

# Wait for the service to be healthy
print_status "Waiting for config service to start..."
sleep 10

# Check if the service is running
if docker-compose ps config-service | grep -q "Up"; then
    print_status "✅ Configuration service is running!"
    print_status "🌐 Access the service at: http://192.168.88.120:8083"
    print_status "📊 Service status:"
    docker-compose ps config-service
else
    print_error "❌ Configuration service failed to start"
    print_error "Checking logs:"
    docker-compose logs config-service
    exit 1
fi

# Test the service
print_status "Testing service endpoints..."
if curl -s http://localhost:8083 > /dev/null; then
    print_status "✅ Web interface is accessible"
else
    print_warning "⚠️  Web interface may not be accessible from localhost"
    print_status "Try accessing from another machine: http://192.168.88.120:8083"
fi

print_status "🎉 Deployment completed successfully!"
print_status ""
print_status "Available endpoints:"
print_status "  • Web Interface: http://192.168.88.120:8083"
print_status "  • API Services: http://192.168.88.120:8083/api/services"
print_status "  • Config Files: http://192.168.88.120:8083/api/config/files"
print_status ""
print_status "To view logs: docker-compose logs -f config-service"
print_status "To restart: docker-compose restart config-service"