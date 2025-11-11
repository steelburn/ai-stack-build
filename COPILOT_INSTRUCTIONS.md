# 🤖 AI Stack Build - Copilot Instructions

## 📋 Overview

The AI Stack Build is a comprehensive, production-ready containerized AI services platform featuring advanced monitoring, security, and deployment capabilities. This project orchestrates multiple AI services including Dify, Ollama, LiteLLM, OpenWebUI, N8N, Flowise, and others, providing a complete AI development and deployment environment.

### 🎯 Key Components
- **15+ AI Services**: Complete AI ecosystem from LLM hosting to workflow automation
- **Enterprise Security**: SSL/TLS encryption, HTTP Basic Auth, Docker secrets, network segmentation
- **Advanced Monitoring**: Real-time health checks, resource monitoring, and comprehensive dashboards
- **Production Ready**: Automated deployment, backup/recovery, and security hardening
- **Developer Friendly**: One-command setup with extensive documentation

### 🏗️ Architecture Highlights
- **Nginx Reverse Proxy**: SSL termination, load balancing, and security headers
- **Monitoring Dashboard**: Flask-based health monitoring with web interface
- **Vector Database**: Qdrant for AI memory and similarity search
- **Multi-Database**: PostgreSQL primary + Redis caching
- **Service Mesh**: Docker networks with proper isolation

## 🤖 AI Services Quick Reference

### Core AI Services
| Service | URL | Purpose | Key Commands |
|---------|-----|---------|--------------|
| **Dify** | `https://localhost/dify` | AI App Platform | API management, workflow orchestration |
| **Ollama** | `https://localhost/ollama` | Local LLM Server | Model hosting, GPU acceleration |
| **LiteLLM** | `https://localhost/litellm` | LLM Router | Multi-provider API unification |
| **OpenWebUI** | `https://localhost/openwebui` | LLM Frontend | Modern chat interface |
| **OpenMemory** | `https://localhost/openmemory` | AI Memory | Persistent context management |
| **N8N** | `https://localhost/n8n` | Workflow Automation | AI workflow orchestration |
| **Flowise** | `https://localhost/flowise` | AI Builder | Visual workflow creation |

### AI Service Management
```bash
# Check AI service status
make status | grep -E "(dify|ollama|litellm|openwebui|n8n|flowise)"

# View AI service logs
docker compose logs ollama
docker compose logs litellm
docker compose logs dify-web

# Restart AI services
docker compose restart ollama litellm dify-web

# Pull latest AI models (Ollama)
docker compose exec ollama ollama pull llama2
docker compose exec ollama ollama pull codellama
```

### Model Management (Ollama)
```bash
# List available models
docker compose exec ollama ollama list

# Pull specific models
docker compose exec ollama ollama pull llama2:7b
docker compose exec ollama ollama pull codellama:7b

# Remove unused models
docker compose exec ollama ollama rm unused-model

# Check GPU usage
docker compose exec ollama nvidia-smi
```

## 🚀 Quick Start Checklist

### Pre-Deployment
- [ ] Verify system requirements (8GB+ RAM, 4+ CPU cores, 100GB+ storage)
- [ ] Install Docker 20.10+ and Docker Compose V2
- [ ] Clone repository: `git clone https://github.com/steelburn/ai-stack-build.git`
- [ ] Change to project directory: `cd ai-stack-build`

### Deployment Steps
- [ ] Generate secrets: `./generate-secrets.sh`
- [ ] Generate Docker secrets: `./generate-docker-secrets.sh`
- [ ] Generate SSL certificates: `./generate-ssl.sh`
- [ ] Copy environment file: `cp .env.example .env`
- [ ] Edit `.env` with your configuration
- [ ] Start services: `make up`
- [ ] Verify deployment: `make health`

### Post-Deployment
- [ ] Access monitoring: `https://localhost/monitoring`
- [ ] Check service status: `make status`
- [ ] Review logs: `make logs-tail`
- [ ] Test key services manually

## 🛠️ Essential Commands

### Core Operations
```bash
# Start all services
make up

# Start with database admin (optional)
make up-db-admin

# Stop all services
make down

# Restart all services
make restart

# Check service health
make health

# View service status
make status

# View recent logs
make logs-tail

# View all logs
make logs
```

### Maintenance Commands
```bash
# Create full backup
make backup

# Restore from backup
make restore FILE=backup/system_backup.tar.gz

# Clean up resources
make clean

# Run diagnostics
make diagnose

# Check environment
make env-check

# Validate ports
make check-ports
```

### Development Commands
```bash
# Setup development environment
make setup

# Run tests (if available)
make test

# View version information
make version

# Get help
make help
```

## 🔍 Troubleshooting Protocol

### Step 1: Quick Diagnosis
```bash
# Always start with these commands
make diagnose
make status
docker-compose ps
docker system df
```

### Step 2: Check Logs
```bash
# View all service logs
make logs-tail

# Check specific service logs
docker compose logs monitoring
docker compose logs nginx
docker compose logs db
```

### Step 3: Verify Configuration
```bash
# Check environment variables
cat .env | grep -v "^#" | grep -v "^$"

# Verify secrets exist
ls -la secrets/

# Check Docker Compose configuration
docker compose config --quiet && echo "Config OK" || echo "Config ERROR"
```

### Step 4: Test Individual Services
```bash
# Test monitoring dashboard
curl -k https://localhost/monitoring/health

# Test database connectivity
docker compose exec db pg_isready -U postgres -d dify

# Test Redis connectivity
docker compose exec redis redis-cli ping

# Test service APIs
curl -k https://localhost/dify/health
curl -k https://localhost/ollama/api/version
```

### Step 5: Resource Check
```bash
# Check system resources
free -h
df -h
docker system df

# Check container resources
docker stats --no-stream

# Check for OOM kills
dmesg | grep -i "oom\|kill"
```

## 🚨 Common Issues & Solutions

### AI Service Issues

#### Ollama Model Loading Problems
**Symptoms:** Models fail to load, "model not found" errors

**Solutions:**
```bash
# Check available models
docker compose exec ollama ollama list

# Pull required models
docker compose exec ollama ollama pull llama2
docker compose exec ollama ollama pull mistral

# Check GPU memory
docker compose exec ollama nvidia-smi

# Restart Ollama service
docker compose restart ollama
```

#### LiteLLM API Key Issues
**Symptoms:** LLM API calls fail with authentication errors

**Solutions:**
```bash
# Check API key configuration
cat secrets/litellm_master_key

# Verify environment variables
grep LITELLM_MASTER_KEY .env

# Restart LiteLLM service
docker compose restart litellm

# Test API connectivity
curl -X POST https://localhost/litellm/chat/completions \
  -H "Authorization: Bearer $(cat secrets/litellm_master_key)" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

#### Dify Application Errors
**Symptoms:** Dify web interface not loading, API errors

**Solutions:**
```bash
# Check Dify service status
docker compose ps dify-web

# View Dify logs
docker compose logs dify-web

# Verify database connectivity
docker compose exec db pg_isready -U postgres -d dify

# Restart Dify services
docker compose restart dify-web dify-api
```

#### Vector Database (Qdrant) Issues
**Symptoms:** Similarity search failures, memory errors

**Solutions:**
```bash
# Check Qdrant status
curl -k https://localhost/qdrant/health

# View Qdrant logs
docker compose logs qdrant

# Verify API key
cat secrets/qdrant_api_key

# Check disk space for vector storage
df -h | grep qdrant
```

### Services Won't Start
**Symptoms:** `docker-compose ps` shows services in "starting" or "unhealthy" state

**Solutions:**
1. Check resource limits: `free -h`
2. Review logs: `make logs-tail`
3. Verify port conflicts: `make check-ports`
4. Check Docker daemon: `docker system info`

### Cannot Access Services
**Symptoms:** Services running but not accessible via browser/API

**Solutions:**
1. Check Nginx configuration: `docker-compose exec nginx nginx -t`
2. Verify SSL certificates: `make ssl-check`
3. Test internal connectivity: `docker-compose exec monitoring curl http://dify-web:3000`
4. Check firewall rules: `sudo ufw status`

### Database Connection Issues
**Symptoms:** Services fail with database connection errors

**Solutions:**
1. Check database status: `docker-compose ps db`
2. Verify credentials: `cat secrets/db_password`
3. Test connectivity: `docker-compose exec db pg_isready -U postgres`
4. Check database logs: `docker-compose logs db`

### High Resource Usage
**Symptoms:** System slowdown, services crashing

**Solutions:**
1. Monitor usage: `docker stats`
2. Adjust memory limits in `docker-compose.yml`
3. Reduce concurrent requests
4. Optimize database queries

### SSL Certificate Issues
**Symptoms:** Browser shows certificate warnings

**Solutions:**
1. Check certificate validity: `openssl x509 -in nginx/ssl/cert.pem -checkend 86400`
2. Regenerate certificates: `./generate-ssl.sh`
3. Reload Nginx: `docker-compose exec nginx nginx -s reload`

## ⚡ Performance Optimization

### AI Workload Tuning

#### GPU Optimization (Ollama)
```bash
# Check GPU availability
docker compose exec ollama nvidia-smi

# Configure GPU layers in .env
echo "OLLAMA_GPU_LAYERS=35" >> .env  # Adjust based on VRAM
echo "OLLAMA_NUM_GPU=1" >> .env

# Monitor GPU usage during inference
docker compose exec ollama nvidia-smi --query-gpu=utilization.gpu,utilization.memory --format=csv
```

#### Memory Management
```bash
# Set Ollama memory limits
echo "OLLAMA_MAX_MEMORY=16GB" >> .env

# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Adjust container memory limits in docker-compose.yml
# Increase limits for AI services:
#   ollama:
#     deploy:
#       resources:
#         limits:
#           memory: 32G
#         reservations:
#           memory: 16G
```

#### Vector Database Optimization
```bash
# Qdrant performance tuning
echo "QDRANT__SERVICE__MAX_OPTIMIZATION_THREADS=4" >> .env

# Monitor vector search performance
curl -k "https://localhost/qdrant/collections/{collection_name}/points/search" \
  -H "api-key: $(cat secrets/qdrant_api_key)" \
  -d '{"vector": [0.1, 0.2, ...], "limit": 10}'
```

### System Performance Tuning

#### Docker Resource Limits
```bash
# View current resource usage
docker system df
docker stats

# Adjust compose resource limits
# Add to docker-compose.yml services:
# services:
#   ollama:
#     deploy:
#       resources:
#         limits:
#           cpus: '4.0'
#           memory: 32G
#         reservations:
#           cpus: '2.0'
#           memory: 16G
```

#### Network Optimization
```bash
# Check network performance
docker network ls
docker network inspect ai-stack_ai-stack

# Optimize Nginx for AI workloads
# Adjust worker processes and connections in nginx.conf
echo "worker_processes auto;" >> nginx/nginx.conf
echo "worker_connections 1024;" >> nginx/nginx.conf
```

#### Database Performance
```bash
# PostgreSQL tuning for AI workloads
echo "POSTGRES_SHARED_BUFFERS=2GB" >> .env
echo "POSTGRES_EFFECTIVE_CACHE_SIZE=6GB" >> .env

# Monitor database performance
docker compose exec db psql -U postgres -d dify -c "SELECT * FROM pg_stat_activity;"

# Redis optimization
echo "REDIS_MAXMEMORY=4gb" >> .env
echo "REDIS_MAXMEMORY_POLICY=allkeys-lru" >> .env
```

### Monitoring Performance Metrics

#### Key Performance Indicators
- **Response Time**: API response times < 2 seconds for most endpoints
- **GPU Utilization**: 70-90% during inference, < 10% idle
- **Memory Usage**: Stay under 85% of allocated limits
- **Vector Search**: < 100ms for typical similarity searches
- **Database Queries**: < 50ms average response time

#### Performance Monitoring Commands
```bash
# Real-time performance monitoring
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.NetIO}}"

# AI service performance
curl -k https://localhost/monitoring/api/performance

# Database performance
docker compose exec db psql -U postgres -c "SELECT * FROM pg_stat_user_tables;"

# Network performance
iftop -i docker0
```

## 🤖 AI Service Configuration

### Ollama Configuration
```bash
# Environment variables in .env
OLLAMA_HOST=http://ollama:11434
OLLAMA_MAX_MEMORY=16GB
OLLAMA_NUM_GPU=1
OLLAMA_GPU_LAYERS=35

# Model management
docker compose exec ollama ollama pull llama2:7b
docker compose exec ollama ollama pull codellama:7b
docker compose exec ollama ollama pull mistral:7b

# Custom model file (optional)
echo "FROM llama2:7b" > Modelfile
echo "PARAMETER temperature 0.7" >> Modelfile
docker compose exec ollama ollama create custom-model -f /tmp/Modelfile
```

### LiteLLM Configuration
```bash
# API key management
LITELLM_MASTER_KEY=your-secure-master-key
LITELLM_SALT_KEY=your-secure-salt-key

# Provider configuration
# Add to .env for multiple providers:
echo "OPENAI_API_KEY=sk-..." >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
echo "GOOGLE_API_KEY=..." >> .env

# Test provider connectivity
curl -X POST https://localhost/litellm/chat/completions \
  -H "Authorization: Bearer $(cat secrets/litellm_master_key)" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Dify Configuration
```bash
# Database connection
DIFY_DB_HOST=db
DIFY_DB_PORT=5432
DIFY_DB_USERNAME=postgres
DIFY_DB_PASSWORD_FILE=/run/secrets/db_password
DIFY_DB_DATABASE=dify

# Vector store configuration
VECTOR_STORE=qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY_FILE=/run/secrets/qdrant_api_key

# Redis configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD_FILE=/run/secrets/redis_password
```

### N8N & Flowise Setup
```bash
# N8N credentials
N8N_ENCRYPTION_KEY=your-encryption-key
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password

# Flowise configuration
FLOWISE_SECRETKEY=your-flowise-secret
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=secure-password

# Initial setup URLs:
# N8N: https://localhost/n8n
# Flowise: https://localhost/flowise
```

### OpenMemory Configuration
```bash
# Vector store settings
OPENMEMORY_VECTOR_STORE=qdrant
OPENMEMORY_QDRANT_URL=http://qdrant:6333
OPENMEMORY_QDRANT_API_KEY_FILE=/run/secrets/qdrant_api_key

# Database for metadata
OPENMEMORY_DATABASE_URL=postgresql://postgres:$(cat secrets/db_password)@db:5432/dify

# Optional OpenAI integration
OPENAI_API_KEY=sk-your-openai-key
```

## 🚀 Deployment Strategies

### Development Deployment
```bash
# Quick development setup
make setup
cp .env.example .env
# Edit .env for development
make up
```

### Production Deployment
```bash
# Full production setup
make setup
cp .env.example .env
# Edit .env for production settings
# Configure SSL certificates
# Set up monitoring and alerts
make up
make health
```

### Cloud Deployment

#### AWS EC2 Setup
```bash
# Provision EC2 instance (t3.xlarge or better for AI workloads)
# Ubuntu 22.04 LTS, 16GB+ RAM, GPU instance for AI

# Install prerequisites
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh

# Clone and deploy
git clone https://github.com/steelburn/ai-stack-build.git
cd ai-stack-build
make setup

# Configure for production
cp .env.example .env
# Edit .env with production values
# Set DOMAIN=your-domain.com
# Configure SSL certificates

# Security hardening
make harden-security

# Start services
make up
```

#### Google Cloud Platform
```bash
# Create VM instance
# e2-standard-8 (32GB RAM) or better
# Ubuntu 22.04 LTS

# GPU-enabled instance for AI workloads:
# g2-standard-8 (A100 GPU)

# Install GPU drivers (if using GPU)
# Follow GCP GPU setup guide

# Deploy stack
git clone https://github.com/steelburn/ai-stack-build.git
cd ai-stack-build
make setup
make up
```

#### Azure VM Setup
```bash
# Create Ubuntu VM
# Standard_D8s_v3 or better (32GB RAM)
# GPU: NCas_T4_v3 for AI workloads

# Install prerequisites
curl -fsSL https://get.docker.com | sh

# Deploy
git clone https://github.com/steelburn/ai-stack-build.git
cd ai-stack-build
make setup
make up
```

### High Availability Setup

#### Load Balancing
```bash
# Deploy multiple instances behind load balancer
# Use Nginx upstream or cloud load balancer

# Example nginx.conf upstream configuration:
upstream ai-stack {
    server ai-stack-1:443;
    server ai-stack-2:443;
    server ai-stack-3:443;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass https://ai-stack;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Database Clustering
```bash
# PostgreSQL primary-replica setup
# Configure streaming replication
# Use PgBouncer for connection pooling

# Redis clustering (optional)
# Configure Redis Cluster for high availability
# Use Redis Sentinel for automatic failover
```

### Docker Swarm Deployment
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml ai-stack

# Scale services
docker service scale ai-stack_ollama=2
docker service scale ai-stack_litellm=3

# Monitor swarm
docker service ls
docker stack ps ai-stack
```

### Kubernetes Deployment
```bash
# Convert docker-compose to k8s manifests
kompose convert -f docker-compose.yml

# Apply manifests
kubectl apply -f .

# Configure ingress
kubectl apply -f ingress.yml

# Set up persistent volumes
kubectl apply -f persistent-volumes.yml

# Monitor with kubectl
kubectl get pods
kubectl logs deployment/ollama
```

## 🎯 Best Practices

### AI Development
- **Model Selection**: Choose appropriate model sizes based on hardware capabilities
- **GPU Utilization**: Monitor GPU usage and adjust batch sizes accordingly
- **Memory Management**: Set proper memory limits for AI services
- **API Rate Limiting**: Implement rate limiting for LLM APIs to prevent abuse
- **Model Caching**: Use Redis for caching frequent model responses

### Production Operations
- **Regular Backups**: Schedule automated backups of databases and configurations
- **Security Updates**: Keep Docker images and system packages updated
- **Monitoring Alerts**: Configure alerts for critical service failures
- **Resource Scaling**: Monitor usage patterns and scale resources as needed
- **Log Rotation**: Implement log rotation to prevent disk space issues

### Security Best Practices
- **Secret Rotation**: Regularly rotate API keys and passwords
- **Network Security**: Use firewall rules and network segmentation
- **SSL Certificates**: Use valid certificates and monitor expiration
- **Access Control**: Implement proper authentication and authorization
- **Audit Logging**: Enable comprehensive logging for security monitoring

### Performance Optimization
- **Resource Allocation**: Allocate appropriate CPU/memory for each service
- **Database Tuning**: Optimize database configuration for AI workloads
- **Caching Strategy**: Implement effective caching for improved performance
- **Load Balancing**: Distribute load across multiple service instances
- **Monitoring**: Continuously monitor performance metrics

### Maintenance Schedule
- **Daily**: Check service health and resource usage
- **Weekly**: Review logs for errors and security issues
- **Monthly**: Update Docker images and rotate secrets
- **Quarterly**: Review and optimize resource allocation
- **Annually**: Complete security audit and infrastructure review

## 📚 Documentation Reference

### Primary Documentation
- **PROJECT_OVERVIEW.md**: Comprehensive project architecture and features
- **README.md**: Quick start guide and service overview
- **DEPLOYMENT_GUIDE.md**: Detailed deployment instructions for various environments
- **CONFIGURATION_REFERENCE.md**: Complete configuration options and environment variables
- **API_DOCUMENTATION.md**: Monitoring API reference and endpoints
- **TROUBLESHOOTING_GUIDE.md**: Problem solving guide with common issues

### Key Configuration Files
- **docker-compose.yml**: Service definitions and orchestration
- **Makefile**: Automation commands and shortcuts
- **.env.example**: Environment variable template
- **services-config.json**: Monitoring dashboard configuration
- **nginx/nginx.conf**: Reverse proxy configuration
- **setup.sh**: Automated setup script

## 📞 Support & Escalation

### Self-Service Troubleshooting
1. Check this document first for relevant sections
2. Run `make diagnose` for automated system analysis
3. Review service-specific logs with `docker compose logs <service>`
4. Check monitoring dashboard at `https://localhost/monitoring`
5. Consult TROUBLESHOOTING_GUIDE.md for detailed solutions

### When to Escalate
- **Critical Production Issues**: Complete system outages affecting users
- **Security Incidents**: Suspected breaches or unauthorized access
- **Data Loss**: Database corruption or missing backups
- **Performance Degradation**: Sustained high latency or resource exhaustion
- **Unknown Errors**: Issues not covered in documentation

### Emergency Procedures
```bash
# Quick system restart
make restart

# Emergency backup
make backup

# Service isolation (if one service is problematic)
docker compose stop <problematic-service>

# Full system reset (last resort)
make down
docker system prune -f
make setup
make up
```

### Community Support
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share solutions
- **Documentation**: Contribute improvements to guides

---

**Remember**: For AI-specific issues, always check service logs first. Most problems can be resolved with proper configuration and resource allocation.

*Last updated: November 2025 | AI Stack Build v2.0*
```
```

## 🔧 Configuration Management

### Environment Variables
- **Never commit `.env` file** - it contains sensitive data
- **Always use `.env.example` as template**
- **Regenerate secrets** for production: `./generate-secrets.sh`
- **Update secrets** after changing passwords: `./generate-docker-secrets.sh`

### Service Configuration
- **Modify `docker-compose.yml`** for service changes
- **Update `services-config.json`** for monitoring dashboard
- **Test configuration** before deploying: `docker-compose config --quiet`
- **Backup configuration** before major changes

### SSL Certificates
- **Development**: Use self-signed certificates
- **Production**: Use Let's Encrypt or CA certificates
- **Certificate path**: `nginx/ssl/cert.pem` and `nginx/ssl/key.pem`
- **Reload after changes**: `docker-compose exec nginx nginx -s reload`

## 📊 Monitoring & Observability

### Health Dashboard (`https://localhost/monitoring`)

The monitoring dashboard provides comprehensive system visibility:

#### 🏥 Health Overview
- **Service Status**: Real-time health indicators for all 15+ services
- **Resource Metrics**: CPU, memory, disk, and network usage
- **Container Health**: Individual container status and health checks
- **System Load**: Overall system performance metrics

#### 📈 Available Dashboard Pages
- **`/monitoring/`**: Main dashboard with service grid
- **`/monitoring/health`**: JSON API health endpoint
- **`/monitoring/resources`**: Detailed resource usage charts
- **`/monitoring/logs`**: Live log streaming interface
- **`/monitoring/alerts`**: Configurable alert thresholds
- **`/monitoring/trends`**: Historical performance trends

#### 🔍 Monitoring API Endpoints
```bash
# Health check (JSON response)
curl -k https://localhost/monitoring/health

# Service status
curl -k https://localhost/monitoring/api/services

# Resource usage
curl -k https://localhost/monitoring/api/resources

# Container logs
curl -k https://localhost/monitoring/api/logs/{service-name}
```

### Advanced Monitoring Commands
```bash
# Detailed service health
make health

# Resource usage summary
docker stats --no-stream

# Container logs with filtering
docker compose logs --tail=100 monitoring
docker compose logs --tail=50 nginx

# System resource monitoring
htop
nvidia-smi  # GPU monitoring

# Network monitoring
docker network ls
docker network inspect ai-stack_ai-stack
```

### Alert Configuration
The monitoring system supports configurable alerts for:
- Service health failures
- High resource usage (>80% CPU/Memory)
- Disk space warnings
- Network connectivity issues
- SSL certificate expiration

Configure alerts in `services-config.json` and restart the monitoring service.

## �️ Database Administration

### Enabling Database Admin
```bash
# Set environment variables
echo "ENABLE_DATABASE_ADMIN=true" >> .env
echo "ADMINER_USERNAME=dbadmin" >> .env
echo "ADMINER_PASSWORD=secure-password" >> .env

# Start with database admin
make up-db-admin

# Access Adminer
open https://localhost/adminer/
```

### Database Operations
```bash
# Direct database access (emergency only)
docker compose exec db psql -U postgres -d dify

# Backup database
make backup-db

# Restore database
make restore-db FILE=backup/db_backup.sql

# Check database health
docker compose exec db pg_isready -U postgres -d dify
```

### Adminer Features
- **Auto-connect**: Pre-filled database credentials
- **HTTP Basic Auth**: Required for access
- **Web-based**: No client installation needed
- **Multi-database**: Supports PostgreSQL, MySQL, etc.
- **Security**: Rate-limited and SSL-protected

## �🔒 Security Operations

### Regular Maintenance
```bash
# Update Docker images
docker compose pull

# Rotate secrets
./generate-secrets.sh
./generate-docker-secrets.sh

# Update SSL certificates
./generate-ssl.sh

# Security audit
make diagnose
```

### Security Checklist
- [ ] Secrets are rotated regularly
- [ ] SSL certificates are valid
- [ ] Firewall rules are correct
- [ ] User passwords are strong
- [ ] Docker daemon is secured
- [ ] Logs don't contain sensitive data

### Incident Response
1. **Isolate affected services**: `docker compose stop <service>`
2. **Check logs**: `docker compose logs <service>`
3. **Restore from backup**: `make restore FILE=backup/recent_backup.tar.gz`
4. **Investigate root cause**
5. **Apply fix and restart**: `make up`

## 🚀 Deployment Strategies

### Development Deployment
```bash
# Quick development setup
make setup
cp .env.example .env
# Edit .env for development
make up
```

### Production Deployment
```bash
# Full production setup
make setup
cp .env.example .env
# Edit .env for production settings
# Configure SSL certificates
# Set up monitoring and alerts
make up
make health
```

### Cloud Deployment
```bash
# AWS/GCP/Azure setup
# Provision VM with required specs
# Configure security groups/firewall
# Set up domain and DNS
# Deploy using production steps
# Configure load balancer if needed
```

## 📚 Documentation Reference

### Primary Documentation
- **README.md**: Project overview and quick start
- **DEPLOYMENT_GUIDE.md**: Detailed deployment instructions
- **CONFIGURATION_REFERENCE.md**: All configuration options
- **API_DOCUMENTATION.md**: Monitoring API reference
- **TROUBLESHOOTING_GUIDE.md**: Problem solving guide

### Key Files
- **docker-compose.yml**: Service definitions and configuration
- **.env.example**: Environment variable template
- **Makefile**: Automation commands
- **services-config.json**: Monitoring dashboard configuration

## 🎯 Best Practices

### Development
- Always test changes locally first
- Use `make setup` for consistent environment
- Keep `.env` out of version control
- Test with `make health` before committing

### Production
- Use production SSL certificates
- Enable monitoring and alerting
- Regular backup schedule
- Keep secrets rotated
- Monitor resource usage

### Maintenance
- Regular log review
- Security updates
- Performance monitoring
- Backup verification
- Documentation updates

## 📞 Support & Escalation

### Self-Service Troubleshooting
1. Check this document first
2. Run `make diagnose`
3. Review logs with `make logs-tail`
4. Check TROUBLESHOOTING_GUIDE.md

### When to Escalate
- Multiple services failing simultaneously
- Database corruption
- Security incidents
- Performance issues affecting production
- Unknown errors in logs

### Emergency Procedures
```bash
# Quick restart
make restart

# Emergency backup
make backup

# Full system reset (last resort)
make down
docker system prune -f
make setup
make up
```

---

**Remember**: When in doubt, run `make diagnose` first. Most issues can be resolved with proper logging and configuration verification.

*Last updated: November 2025 | AI Stack Build*</content>
<parameter name="filePath">/home/steelburn/Development/ai-stack-build/COPILOT_INSTRUCTIONS.md