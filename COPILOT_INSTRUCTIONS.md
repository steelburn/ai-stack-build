# 🤖 AI Stack Build - Copilot Instructions

## 📋 Overview

This document provides comprehensive instructions for deploying, maintaining, and troubleshooting the AI Stack Build project. Use this as your primary reference for all operations.

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

### Health Checks
- **Dashboard**: `https://localhost/monitoring`
- **API Health**: `https://localhost/monitoring/health`
- **Service Status**: `make status`
- **Resource Usage**: `https://localhost/monitoring/resources`

### Log Management
- **View logs**: `make logs-tail`
- **Service logs**: `docker-compose logs <service-name>`
- **Log rotation**: Configured in `docker-compose.yml`
- **Persistent logs**: Stored in Docker volumes

### Performance Monitoring
- **Container stats**: `docker stats`
- **System resources**: `htop` or `top`
- **Network usage**: `nload` or `iftop`
- **Disk usage**: `df -h` and `docker system df`

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