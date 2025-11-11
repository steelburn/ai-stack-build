# ⚙️ AI Stack Configuration Reference

This document provides comprehensive reference for all configuration options, environment variables, and settings available in the AI Stack deployment.

## 📋 Table of Contents

- [Environment Variables](#-environment-variables)
- [Service Configuration](#-service-configuration)
- [Security Settings](#-security-settings)
- [Resource Limits](#-resource-limits)
- [Network Configuration](#-network-configuration)
- [Monitoring Settings](#-monitoring-settings)
- [Database Configuration](#-database-configuration)
- [SSL/TLS Settings](#-ssltls-settings)
- [Backup Configuration](#-backup-configuration)
- [Docker Configuration](#-docker-configuration)

## 🔧 Environment Variables

### General Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPOSE_PROJECT_NAME` | `ai-stack` | Docker Compose project name |
| `DOMAIN` | `localhost` | Domain name for SSL certificates |
| `EMAIL` | - | Email for Let's Encrypt certificates |
| `TZ` | `UTC` | Timezone for containers |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | PostgreSQL superuser |
| `POSTGRES_PASSWORD` | `difyai123456` | PostgreSQL password (use secrets in production) |
| `POSTGRES_DB` | `dify` | Default database name |
| `DB_HOST` | `db` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_USERNAME` | `postgres` | Database username |
| `DB_PASSWORD` | `difyai123456` | Database password |
| `DB_DATABASE` | `dify` | Database name |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `redis` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | `difyai123456` | Redis password |

### Vector Database (Qdrant)

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant API URL |
| `VECTOR_STORE` | `qdrant` | Vector store type |
| `QDRANT_API_KEY` | `difyai123456` | Qdrant API key |

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama API host |
| `OLLAMA_WEBUI_SECRET_KEY` | `your-secret-key` | Ollama WebUI secret key |
| `OLLAMA_MAX_MEMORY` | - | Maximum memory for Ollama (e.g., "16GB") |
| `OLLAMA_NUM_GPU` | - | Number of GPUs to use |
| `OLLAMA_GPU_LAYERS` | - | GPU layers for model loading |

### LiteLLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_MASTER_KEY` | `sk-1234` | Master API key for LiteLLM |
| `LITELLM_SALT_KEY` | `salt-key-1234` | Salt key for encryption |
| `DATABASE_URL` | `postgresql://...` | Database connection URL |
| `LITELLM_PORT` | `4000` | LiteLLM service port |

### OpenMemory Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENMEMORY_VECTOR_STORE` | `qdrant` | Vector store for memory |
| `OPENMEMORY_QDRANT_URL` | `http://qdrant:6333` | Qdrant URL for OpenMemory |
| `OPENMEMORY_QDRANT_API_KEY` | `difyai123456` | Qdrant API key for OpenMemory |
| `OPENMEMORY_DATABASE_URL` | `postgresql://...` | Database URL for OpenMemory |
| `OPENAI_API_KEY` | - | OpenAI API key (if using OpenAI) |

### N8N Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `N8N_ENCRYPTION_KEY` | - | Encryption key for sensitive data |
| `N8N_BASIC_AUTH_ACTIVE` | `true` | Enable basic authentication |
| `N8N_BASIC_AUTH_USER` | `admin` | Basic auth username |
| `N8N_BASIC_AUTH_PASSWORD` | `password` | Basic auth password |
| `N8N_PORT` | `5678` | N8N service port |

### Flowise Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLOWISE_USERNAME` | `admin` | Admin username |
| `FLOWISE_PASSWORD` | `password` | Admin password |
| `FLOWISE_SECRETKEY` | - | Secret key for encryption |
| `FLOWISE_PORT` | `3001` | Flowise service port |

### Supabase Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPABASE_ANON_KEY` | - | Anonymous user key |
| `SUPABASE_SERVICE_ROLE_KEY` | - | Service role key |
| `SUPABASE_URL` | `http://supabase:8000` | Supabase URL |
| `SUPABASE_JWT_SECRET` | - | JWT secret for authentication |

### OpenWebUI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENWEBUI_SECRET_KEY` | - | Secret key for sessions |
| `WEBUI_AUTH` | `true` | Enable authentication |
| `WEBUI_AUTH_USERNAME` | - | Admin username |
| `WEBUI_AUTH_PASSWORD` | - | Admin password |
| `WEBUI_PORT` | `3002` | OpenWebUI service port |

### Dify Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CONSOLE_API_URL` | `http://localhost:3000` | Console API URL |
| `CONSOLE_WEB_URL` | `http://localhost:3000` | Console web URL |
| `SERVICE_API_URL` | `http://api:5001` | Service API URL |
| `APP_API_URL` | `http://api:5001` | App API URL |
| `APP_WEB_URL` | `http://localhost:3000` | App web URL |
| `FILES_URL` | `http://localhost:3000` | Files service URL |
| `INTERNAL_FILES_URL` | `http://api:5001` | Internal files URL |
| `LOG_LEVEL` | `INFO` | Logging level |
| `VECTOR_STORE` | `qdrant` | Vector database type |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant service URL |
| `QDRANT_API_KEY` | `difyai123456` | Qdrant API key |
| `STORAGE_TYPE` | `local` | Storage backend type (local/filesystem) |
| `STORAGE_LOCAL_PATH` | `/app/api/storage` | Local storage path for file uploads |
| `SECRET_KEY` | - | Flask secret key |
| `CODE_EXECUTION_ENDPOINT` | - | Code execution endpoint |

### Monitoring Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITORING_USERNAME` | - | Monitoring dashboard username |
| `MONITORING_PASSWORD` | - | Monitoring dashboard password |
| `SERVICES_CONFIG` | - | Path to services config JSON |
| `FLASK_ENV` | `production` | Flask environment |
| `GUNICORN_WORKERS` | `4` | Number of Gunicorn workers |
| `GUNICORN_TIMEOUT` | `30` | Gunicorn timeout |

### Database Admin Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DATABASE_ADMIN` | `false` | Enable Adminer database management |
| `ADMINER_USERNAME` | `admin` | Adminer HTTP Basic Auth username |
| `ADMINER_PASSWORD` | `password` | Adminer HTTP Basic Auth password |
| `ADMINER_DEFAULT_SERVER` | `db` | Default database server |
| `ADMINER_DEFAULT_USER` | `${POSTGRES_USER}` | Default database username |
| `ADMINER_DEFAULT_PASSWORD` | `${POSTGRES_PASSWORD}` | Default database password |
| `ADMINER_DEFAULT_DB` | `${POSTGRES_DB}` | Default database name |
| `ADMINER_DESIGN` | `nette` | Adminer UI theme |

## 🛠️ Service Configuration

### JSON Configuration File

The monitoring dashboard supports flexible service configuration via JSON:

```json
{
  "service-name": {
    "url": "http://service:port/health",
    "name": "Display Name"
  }
}
```

**Default Services Configuration:**
```json
{
  "dify-api": {
    "url": "http://dify-api:8080/health",
    "name": "Dify API"
  },
  "dify-web": {
    "url": "http://dify-web:3000/health",
    "name": "Dify Web"
  },
  "dify-worker": {
    "url": "http://dify-worker:8080/health",
    "name": "Dify Worker"
  },
  "ollama": {
    "url": "http://ollama:11434/api/version",
    "name": "Ollama"
  },
  "litellm": {
    "url": "http://litellm:4000/health",
    "name": "LiteLLM"
  },
  "openmemory": {
    "url": "http://openmemory:8765/docs",
    "name": "OpenMemory"
  },
  "n8n": {
    "url": "http://n8n:5678/healthz",
    "name": "N8N"
  },
  "flowise": {
    "url": "http://flowise:3000/api/v1/health",
    "name": "Flowise"
  },
  "openwebui": {
    "url": "http://openwebui:8080/health",
    "name": "OpenWebUI"
  },
  "qdrant": {
    "url": "http://qdrant:6333/health",
    "name": "Qdrant"
  }
}
```

### Environment Variable Configuration

```bash
# Add custom services
SERVICE_1_NAME=My Custom Service
SERVICE_1_URL=http://my-service:8080/health
SERVICE_2_NAME=Another Service
SERVICE_2_URL=http://another-service:3000/api/health
```

## 🔒 Security Settings

### Authentication Methods

| Service | Method | Configuration |
|---------|--------|---------------|
| Monitoring | HTTP Basic | `MONITORING_USERNAME/PASSWORD` |
| OpenWebUI | Built-in | `WEBUI_AUTH_USERNAME/PASSWORD` |
| N8N | HTTP Basic | `N8N_BASIC_AUTH_USER/PASSWORD` |
| Flowise | Built-in | `FLOWISE_USERNAME/PASSWORD` |
| LiteLLM | API Key | `LITELLM_MASTER_KEY` |

### SSL/TLS Configuration

```bash
# Self-signed certificates (development)
SSL_CERT_PATH=./nginx/ssl/cert.pem
SSL_KEY_PATH=./nginx/ssl/key.pem

# Let's Encrypt (production)
DOMAIN=yourdomain.com
EMAIL=admin@yourdomain.com
```

### Firewall Configuration

The `harden-security.sh` script configures iptables with these rules:

```bash
# Allow SSH
-A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
-A INPUT -p tcp --dport 80 -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT

# Allow Docker networks
-A INPUT -i docker0 -j ACCEPT
-A INPUT -i br-+ -j ACCEPT

# Rate limiting
-A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
-A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# Drop everything else
-A INPUT -j DROP
```

### Secret Management

Docker secrets are stored in `./secrets/` directory:

```
secrets/
├── db_password
├── redis_password
├── monitoring_username
├── monitoring_password
├── litellm_master_key
└── ...
```

## 📊 Resource Limits

### Docker Resource Configuration

```yaml
# docker-compose.yml resource limits
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '4.0'
        reservations:
          memory: 8G
          cpus: '2.0'

  qdrant:
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '2.0'
        reservations:
          memory: 4G
          cpus: '1.0'
```

### Environment Variables for Resources

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MAX_MEMORY` | - | Maximum memory for Ollama |
| `QDRANT_MEMORY_LIMIT` | - | Memory limit for Qdrant |
| `LITELLM_MAX_WORKERS` | - | Maximum workers for LiteLLM |
| `GUNICORN_WORKERS` | `4` | Gunicorn workers for monitoring |

## 🌐 Network Configuration

### Docker Networks

```yaml
# Default network configuration
networks:
  ai-stack:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Port Mappings

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Nginx | 80, 443 | 80, 443 | HTTP/HTTPS |
| Dify API | 8080 | - | HTTP |
| Dify Web | 3000 | - | HTTP |
| Ollama | 11434 | - | HTTP |
| LiteLLM | 4000 | - | HTTP |
| N8N | 5678 | - | HTTP |
| Flowise | 3001 | - | HTTP |
| OpenWebUI | 3002 | - | HTTP |
| Qdrant | 6333 | - | HTTP |
| OpenMemory | 8000 | - | HTTP |
| Supabase | 8000 | - | HTTP |
| Monitoring | 8080 | 8080 | HTTP |

### Nginx Configuration

```nginx
# Main nginx configuration
upstream ai-stack {
    server dify-web:3000;
    server openwebui:3002;
}

server {
    listen 80;
    server_name localhost;

    # SSL redirect
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting
    limit_req zone=api burst=10 nodelay;

    location / {
        proxy_pass http://ai-stack;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 Monitoring Settings

### Health Check Configuration

```yaml
# Service health checks
services:
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d dify"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
```

### Monitoring Dashboard Settings

```bash
# Monitoring configuration
SERVICES_CONFIG=/app/services-config.json
FLASK_ENV=production
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=30

# Auto-refresh intervals
HEALTH_CHECK_INTERVAL=30  # seconds
RESOURCE_CHECK_INTERVAL=10  # seconds
LOG_REFRESH_INTERVAL=30  # seconds
```

### Log Configuration

```yaml
# Docker logging configuration
x-logging: &default-logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
    labels: "security"
```

## 💾 Backup Configuration

### Automated Backup Settings

```bash
# Backup configuration
BACKUP_DIR=./backup
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION=gzip

# Database backup
DB_BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
DB_BACKUP_RETENTION=7

# Model backup
MODEL_BACKUP_SCHEDULE="0 3 * * 0"  # Weekly on Sunday
MODEL_BACKUP_RETENTION=4

# Full system backup
FULL_BACKUP_SCHEDULE="0 4 1 * *"  # Monthly
FULL_BACKUP_RETENTION=12
```

### Volume Backup Configuration

```bash
# Volumes to backup
BACKUP_VOLUMES="
ai-stack_db_data
ai-stack_redis_data
ai-stack_qdrant_data
ai-stack_ollama_data
"

# Exclude patterns
BACKUP_EXCLUDE="
*.log
*.tmp
cache/*
tmp/*
"
```

## 🐳 Docker Configuration

### Docker Compose Overrides

#### Development Override (`docker-compose.dev.yml`)

```yaml
version: '3.8'

services:
  monitoring:
    environment:
      - FLASK_ENV=development
      - DEBUG=1
    volumes:
      - ./monitoring:/app
    command: ["flask", "run", "--host=0.0.0.0", "--port=8080", "--reload"]

  nginx:
    volumes:
      - ./nginx/nginx.dev.conf:/etc/nginx/nginx.conf
```

#### Production Override (`docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  nginx:
    environment:
      - DOMAIN=${DOMAIN}
    volumes:
      - ${SSL_CERT_PATH}:/etc/ssl/certs/cert.pem:ro
      - ${SSL_KEY_PATH}:/etc/ssl/private/key.pem:ro
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  monitoring:
    environment:
      - FLASK_ENV=production
    command: ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
```

### Docker Build Configuration

#### Custom Dockerfile Example

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8080

CMD ["python", "app.py"]
```

### Docker Security Options

```yaml
# Security-enhanced service configuration
services:
  monitoring:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    volumes:
      - ./monitoring:/app:ro
      - /tmp
      - /var/run/docker.sock:ro

  nginx:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /var/cache/nginx
      - /var/run
```

## 🔧 Advanced Configuration

### Custom Nginx Configuration

```nginx
# Custom nginx configuration for advanced routing
upstream dify_backend {
    server dify-api:8080;
}

upstream ollama_backend {
    server ollama:11434;
}

server {
    listen 443 ssl;
    server_name ai.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/wildcard.pem;
    ssl_certificate_key /etc/ssl/private/wildcard.key;

    # API routing
    location /api/dify/ {
        proxy_pass http://dify_backend/;
        proxy_set_header Host $host;
    }

    location /api/ollama/ {
        proxy_pass http://ollama_backend/;
        proxy_set_header Host $host;
    }

    # Web interface
    location / {
        proxy_pass http://dify-web:3000;
    }
}
```

### Environment-Specific Configurations

```bash
# Development environment
cp .env.example .env.dev
echo "COMPOSE_PROJECT_NAME=ai-stack-dev" >> .env.dev
echo "DEBUG=1" >> .env.dev

# Staging environment
cp .env.example .env.staging
echo "COMPOSE_PROJECT_NAME=ai-stack-staging" >> .env.staging
echo "DOMAIN=staging.yourdomain.com" >> .env.staging

# Production environment
cp .env.example .env.prod
echo "COMPOSE_PROJECT_NAME=ai-stack-prod" >> .env.prod
echo "DOMAIN=yourdomain.com" >> .env.prod
```

### Multi-Environment Deployment

```bash
# Development
docker-compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d

# Staging
docker-compose --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml up -d

# Production
docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [PostgreSQL Configuration](https://postgresql.org/docs/)
- [Redis Configuration](https://redis.io/documentation)
- [Ollama Documentation](https://github.com/jmorganca/ollama)
- [Dify Documentation](https://docs.dify.ai)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

For service-specific configuration options, refer to the individual service documentation linked above.</content>
<parameter name="filePath">/home/steelburn/Development/ai-stack-build/CONFIGURATION_REFERENCE.md