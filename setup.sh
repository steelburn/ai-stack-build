#!/bin/bash

# AI Stack Setup Script

echo "🚀 Setting up AI Stack..."

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

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file..."
    cp .env .env.backup 2>/dev/null || true
else
    echo "✅ .env file already exists"
fi

# Pull images
echo "📦 Pulling Docker images..."
docker compose pull

# Start services
echo "🏃 Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Service status:"
docker compose ps

echo "✅ Setup complete!"
echo ""
echo "🌐 Access your services:"
echo "  Dify:        http://localhost:3000"
echo "  N8N:         http://localhost:5678"
echo "  Flowise:     http://localhost:3001"
echo "  OpenWebUI:   http://localhost:3002"
echo "  LiteLLM:     http://localhost:4000"
echo "  Qdrant:      http://localhost:6333"
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