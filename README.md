# 🚀 AI Stack Deployment

A comprehensive, production-ready Docker Compose setup for deploying a full AI application stack with enterprise-grade security, monitoring, and observability features.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Docker Compose](https://img.shields.io/badge/docker%20compose-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Security](https://img.shields.io/badge/security-hardened-red.svg)](https://github.com/topics/security)
[![Monitoring](https://img.shields.io/badge/monitoring-comprehensive-blue.svg)](https://github.com/topics/monitoring)

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Services Included](#-services-included)
- [Security Features](#-security-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Monitoring & Observability](#-monitoring--observability)
- [Service Access](#-service-access)
- [Security Configuration](#-security-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Overview

This project provides a complete, secure, and monitored AI application stack deployment featuring:

- **15+ AI Services**: From LLM hosting to workflow automation
- **Enterprise Security**: Authentication, encryption, network segmentation
- **Comprehensive Monitoring**: Health checks, resource monitoring, log aggregation
- **Production Ready**: SSL/TLS, secrets management, backup strategies
- **Easy Deployment**: Single-command setup with automated security hardening

Perfect for developers, researchers, and organizations looking to deploy AI applications with enterprise-grade reliability and security.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 Nginx Reverse Proxy (SSL/TLS)              │
│                    ┌─────────────────────────────────────┐       │
│                    │         Monitoring Dashboard        │       │
│                    │    (Health + Resources + Logs)     │       │
│                    └─────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
          ┌─────────▼─────────┐ ┌───▼───┐ ┌────────▼─────────┐
          │   AI Applications │ │Vector │ │   AI Services    │
          │                   │ │  DB   │ │                 │
          │ • Dify (API/Web)  │ │Qdrant │ │ • Ollama        │
          │ • N8N Workflow    │ │       │ │ • LiteLLM       │
          │ • Flowise Builder │ └───────┘ │ • OpenWebUI     │
          │ • Supabase        │           │ • Mem0 Memory   │
          └───────────────────┘           └─────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │       Infrastructure          │
                    │                               │
                    │ • PostgreSQL Database        │
                    │ • Redis Cache                │
                    │ • Docker Secrets             │
                    │ • Network Segmentation       │
                    └───────────────────────────────┘
```

## 🛠️ Services Included

### 🤖 AI Core Services
- **[Dify](https://dify.ai)**: Open-source LLM application development platform
- **[Ollama](https://ollama.ai)**: Local LLM runner with model management
- **[Ollama WebUI](https://github.com/ollama-webui/ollama-webui)**: Web interface for Ollama model management
- **[LiteLLM](https://litellm.ai)**: LLM API proxy and load balancer
- **[OpenWebUI](https://openwebui.com)**: Modern web interface for LLMs
- **[Mem0](https://mem0.ai)**: AI memory and context management

### 🔄 Workflow & Automation
- **[N8N](https://n8n.io)**: Workflow automation and integration platform
- **[Flowise](https://flowise.ai)**: Low-code AI workflow builder

### 🗄️ Data & Storage
- **[Qdrant](https://qdrant.tech)**: High-performance vector database
- **[PostgreSQL](https://postgresql.org)**: Relational database
- **[Redis](https://redis.io)**: Cache and session store
- **[Supabase](https://supabase.com)**: Open-source Firebase alternative
- **[Adminer](https://www.adminer.org)**: Web-based database management (optional)

### 📊 Monitoring & Security
- **Monitoring Dashboard**: Comprehensive health, resource, and log monitoring
- **Nginx Reverse Proxy**: SSL/TLS termination and load balancing
- **Security Hardening**: Firewall rules, secret management, encryption

## 🔒 Security Features

### 🛡️ Authentication & Authorization
- **Multi-level Authentication**: HTTP Basic Auth for all web interfaces
- **Secure Credentials**: Cryptographically generated passwords and API keys
- **Session Management**: Secure session handling with Redis

### 🌐 Network Security
- **Reverse Proxy**: Nginx with SSL/TLS termination
- **Security Headers**: XSS, CSRF, HSTS, Content-Type protection
- **Rate Limiting**: API rate limiting and brute force protection
- **Network Segmentation**: Isolated Docker networks
- **Firewall Rules**: Host-level iptables with service-specific restrictions

### 🔐 Secret Management
- **Docker Secrets**: Encrypted secret files for sensitive data
- **Environment Isolation**: Secrets not exposed in environment variables
- **Automated Generation**: Cryptographically secure random credentials

### 🔒 Encryption & TLS
- **HTTPS Everywhere**: SSL/TLS for all web interfaces
- **Database Encryption**: PostgreSQL with secure authentication
- **Redis Encryption**: Password-protected Redis connections
- **Self-signed Certificates**: Development-ready (replace with CA certs for production)

### � Monitoring & Observability
- **Security Logging**: Comprehensive audit logs with rotation
- **Health Monitoring**: Real-time service health checks with visual dashboards
- **Resource Monitoring**: CPU, memory, network, and disk usage tracking
- **Log Aggregation**: Centralized container log viewing with filtering
- **Access Logging**: Detailed security audit trails
- **Prometheus Metrics**: Standard metrics endpoint for external monitoring
- **Alerting System**: Automated alerts for service failures and high resource usage
- **Historical Trends**: Metrics history and trend analysis with charts
- **Request Tracing**: Performance monitoring and request duration tracking

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, Debian 10+)
- **CPU**: 4+ cores recommended
- **RAM**: 16GB+ recommended (32GB+ for multiple LLMs)
- **Disk**: 100GB+ SSD storage
- **Network**: Stable internet connection

### Software Requirements
- **Docker Engine**: 20.10+ (installed automatically if missing)
- **Docker Compose**: 2.0+ (installed automatically if missing)
- **sudo access**: Required for security hardening

### Optional but Recommended
- **SSL Certificates**: CA-signed certificates for production
- **External Storage**: For data persistence and backups
- **Monitoring Tools**: External monitoring integration

## 🚀 Quick Start

### 1. Clone or Download
```bash
git clone <repository-url>
cd ai-stack-build
```

### 2. Automated Setup
```bash
# One-command setup (recommended)
make setup

# Or run manually
./setup.sh
```

### 3. Generate Security Credentials
```bash
# Generate secure secrets (highly recommended)
./generate-secrets.sh
./generate-docker-secrets.sh

# Generate SSL certificates
./generate-ssl.sh
```

### 4. Apply Security Hardening (Optional)
```bash
sudo ./harden-security.sh
```

### 5. Start the Stack
```bash
make up
# Or: docker-compose up -d
```

### 6. Access Services
- **Monitoring Dashboard**: https://localhost/monitoring/
- **Resource Monitor**: https://localhost/monitoring/resources
- **Alert Dashboard**: https://localhost/monitoring/alerts
- **Metrics Trends**: https://localhost/monitoring/trends
- **Prometheus Metrics**: https://localhost/monitoring/metrics
- **Dify**: https://localhost/dify/
- **OpenWebUI**: https://localhost/openwebui/
- **N8N**: https://localhost/n8n/

## ⚙️ Configuration

### Environment Variables

All configuration is centralized in `.env` file. Copy the example:

```bash
cp .env.example .env
# Edit .env with your preferred settings
```

#### Key Configuration Sections:

```bash
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-db-password
POSTGRES_DB=dify

# Redis Configuration
REDIS_PASSWORD=your-secure-redis-password

# AI Service Authentication
WEBUI_AUTH_USERNAME=admin
WEBUI_AUTH_PASSWORD=your-secure-password

# Monitoring Credentials
MONITORING_USERNAME=admin
MONITORING_PASSWORD=your-monitoring-password

# SSL/TLS (for production)
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### Service-Specific Configuration

#### Ollama Models
```bash
# Pull common models after startup
docker exec -it ai-stack-ollama-1 ollama pull llama3.2
docker exec -it ai-stack-ollama-1 ollama pull codellama
```

#### LiteLLM Configuration
- Access dashboard: http://localhost:4000/ui
- Configure model routing and load balancing
- Set up API keys and rate limits

#### N8N Workflows
- Default credentials: admin / password (change in .env)
- Access: https://localhost/n8n/
- Import/export workflows via UI

#### Flowise Workflows
- Default credentials: admin / password (change in .env)
- Access: https://localhost/flowise/
- Build AI workflows visually

## 📊 Monitoring & Observability

### 🏥 Health Monitoring

The monitoring dashboard provides real-time health status for all services:

- **Service Status**: Up/Down indicators with response times
- **Health Checks**: Automated endpoint monitoring
- **Auto-refresh**: Updates every 30 seconds
- **Error Details**: Specific error messages and diagnostics

**Access**: https://localhost/monitoring/ (requires authentication)

### 📈 Resource Monitoring

Comprehensive resource usage tracking:

- **CPU Usage**: Real-time CPU utilization with visual indicators
- **Memory Usage**: RAM usage with limits and percentages
- **Network I/O**: RX/TX byte counts
- **Disk I/O**: Read/write operations
- **Container Status**: Running/stopped/exited states

**Access**: https://localhost/monitoring/resources/

### 📋 Log Monitoring

Centralized container log viewing:

- **Real-time Logs**: Live container log streaming
- **Log Filtering**: Search and filter capabilities
- **Syntax Highlighting**: Color-coded log levels (ERROR, WARN, INFO, DEBUG)
- **Log History**: Configurable log retention
- **Per-Service Logs**: Individual service log access

**Access**: Click "View Logs" for any service in the monitoring dashboard

### Flexible Service Configuration

The monitoring system supports multiple configuration methods:

#### JSON Configuration (Recommended)
```json
{
  "my-service": {
    "url": "http://my-service:8080/health",
    "name": "My Custom Service"
  }
}
```

#### Environment Variables
```bash
SERVICE_1_NAME=My Service
SERVICE_1_URL=http://my-service:8080/health
SERVICE_2_NAME=Another Service
SERVICE_2_URL=http://another-service:3000/health
```

#### Currently Monitored Services
- Dify API, Web, and Worker
- Ollama, LiteLLM, OpenWebUI
- N8N, Flowise, Mem0
- Qdrant, PostgreSQL, Redis

## 🌐 Service Access

### 🔒 Secure Web Interfaces (via Nginx Reverse Proxy - SSL/TLS Protected)
| Service | URL | Authentication | Notes |
|---------|-----|----------------|--------|
| **Monitoring Dashboard** | https://localhost/monitoring/ | HTTP Basic Auth | Service health & resources |
| **Dify** | https://localhost/dify/ | Via Dify | LLM application platform |
| **OpenWebUI** | https://localhost/openwebui/ | Built-in Auth | Web interface for LLMs |
| **Ollama WebUI** | https://localhost/ollama-webui/ | None | Model management interface |
| **N8N** | https://localhost/n8n/ | HTTP Basic Auth | Workflow automation |
| **Flowise** | https://localhost/flowise/ | Built-in Auth | AI workflow builder |
| **LiteLLM Dashboard** | https://localhost/litellm/ui/ | API Key | LLM proxy management |
| **Database Admin (Adminer)** | https://localhost/adminer/ | HTTP Basic Auth | PostgreSQL management (when enabled) |

### 🔑 Secure API Endpoints (via Nginx Reverse Proxy)
| Service | Endpoint | Authentication |
|---------|----------|----------------|
| **Ollama API** | https://localhost/ollama/api/generate | None |
| **LiteLLM API** | https://localhost/litellm/chat/completions | API Key |
| **Mem0 API** | https://localhost/mem0/v1/memories/ | None |

### 🏠 Internal Services (Docker Network Only)
| Service | Purpose | Access |
|---------|---------|--------|
| **Qdrant** | Vector Database | Internal services only |
| **PostgreSQL** | Primary Database | Internal services only |
| **Redis** | Cache & Sessions | Internal services only |
| **Supabase** | Alternative Database | Internal services only |

> **Security Note**: All user-facing services are protected behind the Nginx reverse proxy with SSL/TLS encryption, rate limiting, and security headers. Direct port access has been removed for security.

## 🔐 Security Configuration

### Important Security Steps

1. **Change Default Credentials**
   ```bash
   # Edit .env file
   MONITORING_USERNAME=your-admin-user
   MONITORING_PASSWORD=your-secure-password
   WEBUI_AUTH_USERNAME=your-user
   WEBUI_AUTH_PASSWORD=your-secure-password
   ```

2. **SSL Certificates for Production**
   ```bash
   # Replace self-signed certificates
   cp your-ca-cert.pem nginx/ssl/cert.pem
   cp your-private-key.pem nginx/ssl/key.pem
   ```

3. **Review Firewall Rules**
   ```bash
   sudo iptables -L  # Check current rules
   # Customize harden-security.sh if needed
   ```

4. **Secret Management**
   ```bash
   ./generate-secrets.sh  # Regenerate secrets
   ./generate-docker-secrets.sh  # Update Docker secrets
   ```

### Security Scripts

- `generate-secrets.sh`: Generate cryptographically secure passwords
- `generate-docker-secrets.sh`: Create Docker secret files
- `generate-ssl.sh`: Generate self-signed SSL certificates
- `harden-security.sh`: Apply host-level security hardening

### Authentication Matrix

| Service | Auth Type | Config Location |
|---------|-----------|-----------------|
| Monitoring | HTTP Basic | `.env` (MONITORING_*) |
| OpenWebUI | Built-in | `.env` (WEBUI_AUTH_*) |
| N8N | HTTP Basic | `.env` (N8N_BASIC_*) |
| Flowise | Built-in | `.env` (FLOWISE_*) |
| LiteLLM | API Key | `.env` (LITELLM_MASTER_KEY) |
| Database Admin (Adminer) | HTTP Basic | `.env` (ADMINER_*) |

### 🗄️ Database Administration

The stack includes optional web-based database management via Adminer. This feature is **disabled by default** for security reasons.

#### Enabling Database Admin

1. **Set Environment Variables**
   ```bash
   # Edit .env file
   ENABLE_DATABASE_ADMIN=true
   ADMINER_USERNAME=your-db-admin-user
   ADMINER_PASSWORD=your-secure-db-admin-password
   ```

2. **Start with Database Admin Profile**
   ```bash
   # Start all services including database admin
   docker-compose --profile db-admin up -d

   # Or use the Makefile
   make up-db-admin
   ```

3. **Access Database Admin**
   - URL: `https://localhost/adminer/`
   - **Authentication Required**: Use the `ADMINER_USERNAME` and `ADMINER_PASSWORD` you configured
   - **Auto-Connection**: Adminer will automatically connect to the PostgreSQL database with your configured credentials
   - System: PostgreSQL (pre-selected)
   - Server: `db` (pre-filled)
   - Username: Your `POSTGRES_USER` (pre-filled)
   - Password: Your `POSTGRES_PASSWORD` (pre-filled)
   - Database: Your `POSTGRES_DB` (pre-filled)

#### Security Considerations

- **Database admin is only accessible when explicitly enabled**
- **HTTP Basic Authentication required** for all access
- **Pre-configured connection** eliminates manual entry of credentials
- **Only enable in development/staging environments**
- **Use strong passwords** for both Adminer auth and database access
- **Monitor access logs** when enabled

## 🛠️ Makefile Commands

```bash
make help          # Show all available commands
make setup         # Complete automated setup
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make logs          # View all logs
make status        # Show service status
make clean         # Stop and remove containers/volumes
make pull-models   # Pull common Ollama models
make backup        # Backup data volumes
make restore       # Restore from backup
make update        # Update all images
make security      # Run security hardening
```

## 🔧 Troubleshooting

### Service Status Checks
```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose ps monitoring

# View service logs
docker-compose logs monitoring
make logs SERVICE=monitoring
```

### Common Issues

#### SSL Certificate Warnings
- **Cause**: Self-signed certificates in development
- **Solution**: Add to browser exceptions or use CA certificates
- **Production**: Replace with proper SSL certificates

#### Authentication Failures
```bash
# Check credentials in .env
grep -E "(USERNAME|PASSWORD)" .env

# Verify secret files
ls -la secrets/
cat secrets/monitoring_username
```

#### Service Unreachable
```bash
# Check network connectivity
docker-compose exec monitoring ping dify-api

# Verify service health
curl -k https://localhost/dify/
```

#### Resource Issues
```bash
# Check system resources
free -h
df -h
docker system df

# Monitor container resources
docker stats
```

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec db pg_isready -U postgres -d dify

# View database logs
docker-compose logs db
```

### Performance Optimization

#### Memory Issues
```bash
# Increase Docker memory limit
# Edit /etc/docker/daemon.json
{
  "default-shard-size": "1GB",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

#### Storage Issues
```bash
# Clean up Docker
docker system prune -a --volumes

# Monitor disk usage
du -sh /var/lib/docker/volumes/
```

### Backup and Recovery

#### Data Backup
```bash
# Backup all volumes
make backup

# Manual backup
docker run --rm -v ai-stack_db_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/db-$(date +%Y%m%d).tar.gz -C /data .
```

#### Data Restore
```bash
# Restore from backup
make restore BACKUP=db-20241201.tar.gz
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

### Development Setup
```bash
# Fork and clone
git clone https://github.com/your-username/ai-stack-build.git
cd ai-stack-build

# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
make test
make up

# Submit pull request
git push origin feature/your-feature
```

### Code Standards
- Use descriptive commit messages
- Update documentation for new features
- Test security implications of changes
- Follow Docker best practices
- Include health checks for new services

### Reporting Issues
- Use GitHub Issues for bugs and feature requests
- Include system information and logs
- Describe steps to reproduce
- Suggest potential solutions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Dify](https://dify.ai) - LLM application platform
- [Ollama](https://ollama.ai) - Local LLM hosting
- [LiteLLM](https://litellm.ai) - LLM API management
- [Qdrant](https://qdrant.tech) - Vector database
- [N8N](https://n8n.io) - Workflow automation
- [Flowise](https://flowise.ai) - AI workflow builder
- [OpenWebUI](https://openwebui.com) - LLM web interface

## 📞 Support

- **Documentation**: This README and inline comments
- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Security**: Report security issues privately

---

**Happy AI Building! 🤖✨**