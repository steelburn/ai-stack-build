# 🔧 AI Stack Troubleshooting Guide

This guide provides solutions for common issues encountered when deploying and running the AI Stack.

## 📋 Table of Contents

- [Quick Diagnosis](#-quick-diagnosis)
- [Service Startup Issues](#-service-startup-issues)
- [Network & Connectivity](#-network--connectivity)
- [Performance Problems](#-performance-problems)
- [Security Issues](#-security-issues)
- [Database Problems](#-database-problems)
- [Monitoring Issues](#-monitoring-issues)
- [Resource Issues](#-resource-issues)
- [SSL/TLS Problems](#-ssltls-problems)
- [Backup & Recovery](#-backup--recovery)

## 🔍 Quick Diagnosis

### System Health Check

```bash
# Run comprehensive diagnostic
make diagnose

# Check service status
make status

# View recent logs
make logs-tail

# Test monitoring dashboard
make health
```

### Environment Validation

```bash
# Check configuration
make env-check

# Validate Docker setup
make version

# Check port availability
make check-ports
```

## 🚀 Service Startup Issues

### Services Won't Start

**Symptoms:**
- `docker-compose ps` shows services in "starting" or "unhealthy" state
- Services exit immediately after starting

**Solutions:**

1. **Check Resource Limits**
   ```bash
   # Check available memory
   free -h

   # Check Docker resource limits
   docker system df

   # Reduce memory limits in docker-compose.yml
   services:
     ollama:
       deploy:
         resources:
           limits:
             memory: 8G  # Reduce from 16G
   ```

2. **Check Port Conflicts**
   ```bash
   # Find what's using ports
   sudo lsof -i :80
   sudo lsof -i :443
   sudo lsof -i :8080

   # Change ports in docker-compose.yml
   services:
     nginx:
       ports:
         - "8080:80"  # Change from 80
         - "8443:443" # Change from 443
   ```

3. **Check Docker Logs**
   ```bash
   # View service-specific logs
   docker-compose logs monitoring
   docker-compose logs db

   # View logs with timestamps
   docker-compose logs --timestamps --tail=50 monitoring
   ```

### Database Connection Issues

**Symptoms:**
- Services fail to connect to PostgreSQL/Redis
- "Connection refused" errors in logs

**Solutions:**

1. **Check Database Health**
   ```bash
   # Test database connectivity
   docker-compose exec db pg_isready -U postgres -d dify

   # Check database logs
   docker-compose logs db
   ```

2. **Verify Credentials**
   ```bash
   # Check environment variables
   grep -E "(POSTGRES|REDIS)" .env

   # Verify secret files
   cat secrets/db_password
   ```

3. **Restart Database**
   ```bash
   # Restart database service
   docker-compose restart db

   # Wait for health check
   docker-compose ps db
   ```

### Dependency Issues

**Symptoms:**
- Services fail with "module not found" or "command not found"
- Build failures during `docker-compose up`

**Solutions:**

1. **Rebuild Images**
   ```bash
   # Force rebuild
   docker-compose build --no-cache monitoring

   # Or rebuild all
   docker-compose build --no-cache
   ```

2. **Check Base Images**
   ```bash
   # Pull latest base images
   docker pull python:3.9-slim
   docker pull node:18-alpine
   docker pull postgres:15-alpine
   ```

3. **Clear Docker Cache**
   ```bash
   # Clean build cache
   docker builder prune -f

   # Clean system
   docker system prune -f
   ```

## 🌐 Network & Connectivity Issues

### Cannot Access Services

**Symptoms:**
- Services are running but not accessible
- "Connection refused" when accessing URLs

**Solutions:**

1. **Check Nginx Configuration**
   ```bash
   # Test nginx configuration
   docker-compose exec nginx nginx -t

   # Reload nginx
   docker-compose exec nginx nginx -s reload

   # Check nginx logs
   docker-compose logs nginx
   ```

2. **Verify Port Mapping**
   ```bash
   # Check port mappings
   docker-compose ps

   # Test local ports
   curl http://localhost:8080
   curl -k https://localhost:8080
   ```

3. **Check Firewall Rules**
   ```bash
   # Check iptables rules
   sudo iptables -L

   # Temporarily disable firewall
   sudo ufw disable

   # Test access, then re-enable
   sudo ufw enable
   ```

### Internal Service Communication

**Symptoms:**
- Services can't communicate with each other
- "Connection refused" between containers

**Solutions:**

1. **Check Docker Networks**
   ```bash
   # List networks
   docker network ls

   # Inspect network
   docker network inspect ai-stack

   # Check container IPs
   docker inspect ai-stack-monitoring-1 | grep IPAddress
   ```

2. **Test Internal Connectivity**
   ```bash
   # Test from one container to another
   docker-compose exec monitoring ping db
   docker-compose exec monitoring curl http://db:5432
   ```

3. **Restart Network**
   ```bash
   # Restart all services
   docker-compose down
   docker-compose up -d

   # Or recreate network
   docker-compose down
   docker network rm ai-stack
   docker-compose up -d
   ```

## ⚡ Performance Problems

### High CPU Usage

**Symptoms:**
- Services consuming excessive CPU
- System slowdown

**Solutions:**

1. **Limit CPU Resources**
   ```yaml
   # Add to docker-compose.yml
   services:
     ollama:
       deploy:
         resources:
           limits:
             cpus: '2.0'
           reservations:
             cpus: '1.0'
   ```

2. **Optimize Service Configuration**
   ```bash
   # Reduce Gunicorn workers
   GUNICORN_WORKERS=2

   # Disable debug mode
   FLASK_ENV=production
   ```

3. **Monitor CPU Usage**
   ```bash
   # Check container CPU
   docker stats

   # Profile Python application
   docker-compose exec monitoring python -m cProfile app.py
   ```

### Memory Issues

**Symptoms:**
- Out of memory errors
- Services being killed by OOM killer

**Solutions:**

1. **Increase Memory Limits**
   ```yaml
   services:
     ollama:
       deploy:
         resources:
           limits:
             memory: 12G
           reservations:
             memory: 8G
   ```

2. **Monitor Memory Usage**
   ```bash
   # Check memory usage
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

   # Check system memory
   free -h
   ```

3. **Optimize Memory Usage**
   ```bash
   # Reduce batch sizes
   # Limit concurrent requests
   # Use memory-efficient models
   ```

### Slow Response Times

**Symptoms:**
- Services responding slowly
- High latency in monitoring dashboard

**Solutions:**

1. **Check Resource Utilization**
   ```bash
   # Monitor system resources
   htop
   iotop
   nload
   ```

2. **Optimize Database Queries**
   ```bash
   # Check slow queries
   docker-compose exec db psql -U postgres -d dify -c "SELECT * FROM pg_stat_activity;"

   # Add database indexes
   docker-compose exec db psql -U postgres -d dify -c "CREATE INDEX CONCURRENTLY idx_name ON table_name (column_name);"
   ```

3. **Enable Caching**
   ```bash
   # Configure Redis caching
   # Enable application-level caching
   # Use CDN for static assets
   ```

## 🔒 Security Issues

### Authentication Failures

**Symptoms:**
- Cannot log into services
- "Invalid credentials" errors

**Solutions:**

1. **Verify Credentials**
   ```bash
   # Check environment variables
   grep -E "(USERNAME|PASSWORD)" .env

   # Check secret files
   ls -la secrets/
   cat secrets/monitoring_username
   ```

2. **Reset Passwords**
   ```bash
   # Regenerate secrets
   ./generate-secrets.sh
   ./generate-docker-secrets.sh

   # Restart services
   docker-compose restart
   ```

3. **Check Authentication Configuration**
   ```bash
   # Verify service configuration
   docker-compose exec monitoring env | grep MONITORING
   ```

### SSL/TLS Certificate Issues

**Symptoms:**
- Browser shows certificate warnings
- HTTPS connections failing

**Solutions:**

1. **Check Certificate Files**
   ```bash
   # Verify certificate files exist
   ls -la nginx/ssl/

   # Check certificate validity
   openssl x509 -in nginx/ssl/cert.pem -text -noout | grep -E "(Issuer|Subject|Not Before|Not After)"
   ```

2. **Regenerate Certificates**
   ```bash
   # Generate new self-signed certificates
   ./generate-ssl.sh

   # Or use Let's Encrypt
   ./generate-ssl.sh production yourdomain.com
   ```

3. **Reload Nginx**
   ```bash
   docker-compose exec nginx nginx -s reload
   ```

### Firewall Blocking Access

**Symptoms:**
- Cannot access services from external IPs
- "Connection refused" from outside

**Solutions:**

1. **Check Firewall Rules**
   ```bash
   # Check UFW status
   sudo ufw status

   # Check iptables
   sudo iptables -L
   ```

2. **Allow Required Ports**
   ```bash
   # Allow HTTP/HTTPS
   sudo ufw allow 80
   sudo ufw allow 443

   # Or reset firewall
   sudo ./harden-security.sh
   ```

3. **Check Cloud Security Groups**
   ```bash
   # AWS Security Groups
   aws ec2 describe-security-groups

   # GCP Firewall Rules
   gcloud compute firewall-rules list

   # Azure NSG
   az network nsg rule list
   ```

## 💾 Database Problems

### Database Connection Refused

**Symptoms:**
- Services cannot connect to database
- "Connection refused" errors

**Solutions:**

1. **Check Database Status**
   ```bash
   # Test database connectivity
   docker-compose exec db pg_isready -U postgres

   # Check database logs
   docker-compose logs db
   ```

2. **Verify Connection String**
   ```bash
   # Check environment variables
   grep DATABASE_URL .env

   # Test connection manually
   docker-compose exec db psql -U postgres -d dify -c "SELECT version();"
   ```

3. **Restart Database**
   ```bash
   docker-compose restart db
   sleep 10
   docker-compose ps db
   ```

### Data Corruption

**Symptoms:**
- Database errors
- Inconsistent data
- Services crashing

**Solutions:**

1. **Check Database Integrity**
   ```bash
   # Run integrity checks
   docker-compose exec db psql -U postgres -d dify -c "SELECT * FROM pg_stat_database;"

   # Vacuum database
   docker-compose exec db psql -U postgres -d dify -c "VACUUM ANALYZE;"
   ```

2. **Restore from Backup**
   ```bash
   # Stop services
   docker-compose down

   # Restore database
   make restore FILE=backup/db_backup.tar.gz VOLUME=db_data

   # Restart services
   docker-compose up -d
   ```

3. **Rebuild Database**
   ```bash
   # Drop and recreate database
   docker-compose exec db psql -U postgres -c "DROP DATABASE dify;"
   docker-compose exec db psql -U postgres -c "CREATE DATABASE dify;"

   # Run migrations
   docker-compose exec dify-api python manage.py db upgrade
   ```

## 📊 Monitoring Issues

### Monitoring Dashboard Not Working

**Symptoms:**
- Cannot access monitoring dashboard
- Services show as down when they're running

**Solutions:**

1. **Check Monitoring Service**
   ```bash
   # Check service status
   docker-compose ps monitoring

   # View monitoring logs
   docker-compose logs monitoring
   ```

2. **Test Health Endpoints**
   ```bash
   # Test individual services
   curl http://localhost:8080/health  # Should return service list
   curl http://localhost:8080/resources  # Should return resource data
   ```

3. **Check Configuration**
   ```bash
   # Verify services config
   docker-compose exec monitoring cat /app/services-config.json

   # Check environment
   docker-compose exec monitoring env | grep MONITORING
   ```

### Resource Monitoring Not Working

**Symptoms:**
- Resource usage shows as N/A
- Docker socket access errors

**Solutions:**

1. **Check Docker Socket Access**
   ```bash
   # Verify socket mount
   docker-compose exec monitoring ls -la /var/run/docker.sock

   # Test socket access
   docker-compose exec monitoring docker ps
   ```

2. **Check Permissions**
   ```bash
   # Check socket permissions
   ls -la /var/run/docker.sock

   # Add user to docker group (if needed)
   sudo usermod -aG docker $USER
   ```

3. **Restart Monitoring Service**
   ```bash
   docker-compose restart monitoring
   ```

## 📈 Resource Issues

### Disk Space Problems

**Symptoms:**
- Services failing due to no space
- Docker daemon errors

**Solutions:**

1. **Check Disk Usage**
   ```bash
   # Check system disk
   df -h

   # Check Docker disk usage
   docker system df -v
   ```

2. **Clean Up Docker**
   ```bash
   # Remove unused containers
   docker container prune -f

   # Remove unused images
   docker image prune -f

   # Remove unused volumes
   docker volume prune -f

   # Full cleanup
   docker system prune -a --volumes -f
   ```

3. **Move Docker Data Directory**
   ```bash
   # Stop Docker
   sudo systemctl stop docker

   # Move data directory
   sudo mv /var/lib/docker /mnt/docker-data
   sudo ln -s /mnt/docker-data /var/lib/docker

   # Start Docker
   sudo systemctl start docker
   ```

### GPU Issues (if applicable)

**Symptoms:**
- GPU not detected by services
- CUDA errors

**Solutions:**

1. **Check GPU Access**
   ```bash
   # Check NVIDIA GPU
   nvidia-smi

   # Check Docker GPU support
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

2. **Configure GPU in Compose**
   ```yaml
   services:
     ollama:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

## 🔐 SSL/TLS Problems

### Certificate Expiration

**Symptoms:**
- Browser shows certificate expired
- HTTPS connections failing

**Solutions:**

1. **Check Certificate Validity**
   ```bash
   # Check expiration date
   openssl x509 -in nginx/ssl/cert.pem -text | grep "Not After"

   # Check days until expiry
   openssl x509 -in nginx/ssl/cert.pem -checkend 86400
   ```

2. **Renew Certificates**
   ```bash
   # For Let's Encrypt
   sudo certbot renew

   # For self-signed
   ./generate-ssl.sh

   # Reload nginx
   docker-compose exec nginx nginx -s reload
   ```

### Mixed Content Issues

**Symptoms:**
- Some resources loading over HTTP
- Browser security warnings

**Solutions:**

1. **Check Nginx Configuration**
   ```bash
   # Verify all locations use HTTPS
   docker-compose exec nginx cat /etc/nginx/nginx.conf

   # Add HSTS header
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   ```

2. **Update Internal URLs**
   ```bash
   # Update environment variables to use HTTPS
   CONSOLE_WEB_URL=https://yourdomain.com
   APP_WEB_URL=https://yourdomain.com
   ```

## 💾 Backup & Recovery Issues

### Backup Failures

**Symptoms:**
- Backup commands failing
- Incomplete backups

**Solutions:**

1. **Check Disk Space**
   ```bash
   # Ensure enough space for backups
   df -h ./backup
   ```

2. **Verify Volume Access**
   ```bash
   # Test volume access
   docker run --rm -v ai-stack_db_data:/data alpine ls -la /data
   ```

3. **Check Backup Permissions**
   ```bash
   # Ensure backup directory is writable
   ls -la backup/
   chmod 755 backup/
   ```

### Recovery Problems

**Symptoms:**
- Cannot restore from backup
- Services fail after restore

**Solutions:**

1. **Verify Backup Integrity**
   ```bash
   # Check backup file
   ls -la backup/
   file backup/db_backup.tar.gz

   # Test extraction
   mkdir test_restore && cd test_restore
   tar -tzf ../backup/db_backup.tar.gz | head -10
   ```

2. **Clean Restore Process**
   ```bash
   # Stop all services
   docker-compose down

   # Remove old volumes
   docker volume rm ai-stack_db_data

   # Restore and restart
   make restore FILE=backup/db_backup.tar.gz VOLUME=db_data
   docker-compose up -d
   ```

3. **Post-Restore Checks**
   ```bash
   # Verify data integrity
   docker-compose exec db pg_isready -U postgres
   docker-compose logs db | tail -20
   ```

## 🚨 Emergency Procedures

### Complete System Reset

```bash
# Last resort - complete rebuild
docker-compose down -v --remove-orphans
docker system prune -a --volumes -f
rm -rf backup/*
make setup
make up
```

### Emergency Access

```bash
# Bypass authentication (temporary - monitoring only)
docker compose exec monitoring sed -i 's/@requires_auth//' app.py
docker compose restart monitoring

# Direct database access (internal only)
docker compose exec db psql -U postgres -d dify

# Service access through reverse proxy
# All services accessible via: https://localhost/{service}/
# Example: https://localhost/monitoring/, https://localhost/dify/, etc.
```

### Log Preservation

```bash
# Save logs before reset
docker compose logs > emergency_logs_$(date +%Y%m%d_%H%M%S).txt
docker compose logs --tail=1000 > recent_logs.txt

# Save configuration
cp .env emergency_env_backup
cp docker-compose.yml emergency_compose_backup
```

---

## 📞 Getting Help

### Quick Support Checklist

- [ ] Run `make diagnose`
- [ ] Check `docker-compose ps`
- [ ] Review `docker-compose logs --tail=50`
- [ ] Verify `.env` configuration
- [ ] Check system resources with `free -h && df -h`
- [ ] Test basic connectivity with `curl -k https://localhost/monitoring/`

### Support Information to Provide

When asking for help, include:

1. **System Information**
   ```bash
   uname -a
   docker --version
   docker-compose --version
   free -h
   df -h
   ```

2. **Service Status**
   ```bash
   docker-compose ps
   docker-compose logs --tail=20
   ```

3. **Configuration**
   ```bash
   head -20 .env
   ls -la secrets/
   ```

4. **Error Messages**
   - Exact error messages
   - When the error occurs
   - Steps to reproduce

### Community Resources

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share solutions
- **Documentation**: Check README.md and API docs
- **Logs**: Include relevant log excerpts

Remember: Most issues can be resolved by checking logs, verifying configuration, and ensuring adequate system resources!</content>
<parameter name="filePath">/home/steelburn/Development/ai-stack-build/TROUBLESHOOTING_GUIDE.md