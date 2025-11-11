# 🚀 AI Stack Deployment Guide

This guide provides comprehensive deployment instructions for the AI Stack in various environments and scenarios.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Local Development](#-local-development)
- [Production Deployment](#-production-deployment)
- [Cloud Deployment](#-cloud-deployment)
- [Docker Swarm](#-docker-swarm)
- [Kubernetes](#-kubernetes)
- [High Availability](#-high-availability)
- [Backup & Recovery](#-backup--recovery)
- [Monitoring Setup](#-monitoring-setup)
- [Troubleshooting](#-troubleshooting)

## ⚡ Quick Start

### 🚀 One-Line Installation (Fastest)

Get everything set up automatically with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/steelburn/ai-stack-build/main/install.sh | bash
```

This installer handles everything:
- ✅ System requirement checks
- 📥 Repository setup
- 🔧 Environment configuration
- 🔐 Secret generation
- 🐳 Service deployment
- 📊 Monitoring dashboard

**Installation Directory**: `~/ai-stack-build`

### 🛠️ Traditional Setup

For manual installation or custom configurations:

#### One-Command Setup
```bash
# Clone repository
git clone <repository-url>
cd ai-stack-build

# Automated setup (recommended)
make setup

# Start services
make up

# Access monitoring dashboard
open https://localhost/monitoring/
```

#### Manual Setup
```bash
# 1. Install dependencies
./setup.sh

# 2. Generate secrets
./generate-secrets.sh
./generate-docker-secrets.sh
./generate-ssl.sh

# 3. Start services
docker compose up -d
```

**Environment Validation:**
The setup script automatically validates that all required environment variables are present before starting services. If any variables are missing, you'll see an error message with instructions to check your `.env` file.

```bash
# Check environment configuration
make env-check
```

### Database Admin Setup (Optional)

```bash
# Enable database management
echo "ENABLE_DATABASE_ADMIN=true" >> .env
echo "ADMINER_USERNAME=dbadmin" >> .env
echo "ADMINER_PASSWORD=secure-password" >> .env

# Start with database admin
make up-db-admin

# Access at: https://localhost/adminer/
```

# 4. Check status
docker-compose ps
```

## 💻 Local Development

### Prerequisites

- **OS**: Linux/macOS/Windows (WSL2)
- **CPU**: 4+ cores
- **RAM**: 16GB+ recommended
- **Disk**: 50GB+ free space
- **Docker**: 24.0+
- **Docker Compose**: 2.20+

### Development Setup

```bash
# 1. Clone and setup
git clone <repository-url>
cd ai-stack-build
cp .env.example .env

# 2. Configure for development
echo "COMPOSE_PROJECT_NAME=ai-stack-dev" >> .env
echo "MONITORING_USERNAME=dev" >> .env
echo "MONITORING_PASSWORD=dev123" >> .env

# 3. Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 4. View logs
docker-compose logs -f monitoring
```

### Development Overrides (`docker-compose.dev.yml`)

```yaml
version: '3.8'

services:
  monitoring:
    environment:
      - FLASK_ENV=development
      - DEBUG=1
    volumes:
      - ./monitoring:/app
      - /app/node_modules
    command: ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080", "--reload"]

  nginx:
    volumes:
      - ./nginx/nginx.dev.conf:/etc/nginx/nginx.conf:ro
```

### Development Tools

```bash
# View all logs
make logs

# Restart specific service
make restart SERVICE=monitoring

# Enter container shell
docker exec -it ai-stack-monitoring-1 bash

# Run tests
docker exec ai-stack-monitoring-1 python -m pytest

# Clean development environment
make clean-dev
```

## 🏭 Production Deployment

### Server Requirements

- **OS**: Ubuntu 22.04 LTS / CentOS 8+ / RHEL 8+
- **CPU**: 8+ cores
- **RAM**: 32GB+ (64GB+ for multiple LLMs)
- **Disk**: 200GB+ SSD
- **Network**: 1Gbps+ connection

### Production Setup

```bash
# 1. Server preparation
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git ufw

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone repository
git clone <repository-url>
cd ai-stack-build

# 5. Production configuration
cp .env.example .env
nano .env  # Configure production settings

# 6. Generate production secrets
./generate-secrets.sh
./generate-docker-secrets.sh

# 7. Install SSL certificates (Let's Encrypt)
./generate-ssl.sh production yourdomain.com

# 8. Security hardening
sudo ./harden-security.sh

# 9. Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 10. Setup monitoring
sudo crontab -e
# Add: */5 * * * * cd /path/to/ai-stack-build && make backup
# Add: 0 2 * * * cd /path/to/ai-stack-build && make update
```

### Production Configuration

#### Environment Variables (`.env`)

```bash
# Production settings
COMPOSE_PROJECT_NAME=ai-stack-prod
DOMAIN=yourdomain.com
EMAIL=admin@yourdomain.com

# Security
MONITORING_USERNAME=admin
MONITORING_PASSWORD=your-secure-password-here

# SSL
SSL_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem

# Database
POSTGRES_PASSWORD=your-secure-db-password
REDIS_PASSWORD=your-secure-redis-password

# API Keys
LITELLM_MASTER_KEY=sk-prod-123456789
WEBUI_AUTH_PASSWORD=your-secure-webui-password

# Resources
OLLAMA_MAX_MEMORY=16GB
QDRANT_MEMORY_LIMIT=8GB
```

#### Production Overrides (`docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  nginx:
    environment:
      - DOMAIN=${DOMAIN}
    volumes:
      - ${SSL_CERT_PATH}:/etc/ssl/certs/cert.pem:ro
      - ${SSL_KEY_PATH}:/etc/ssl/private/key.pem:ro
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
      - "443:443"

  ollama:
    deploy:
      resources:
        limits:
          memory: ${OLLAMA_MAX_MEMORY}
        reservations:
          memory: 8GB

  qdrant:
    deploy:
      resources:
        limits:
          memory: ${QDRANT_MEMORY_LIMIT}
        reservations:
          memory: 4GB

  monitoring:
    environment:
      - FLASK_ENV=production
      - GUNICORN_WORKERS=4
      - GUNICORN_TIMEOUT=30
    command: ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
```

### SSL Certificate Setup

#### Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Manual Certificate

```bash
# Place certificates in nginx/ssl/
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
chmod 600 nginx/ssl/key.pem
```

## ☁️ Cloud Deployment

### AWS EC2

```bash
# 1. Launch EC2 instance
# - Ubuntu 22.04 LTS
# - t3.xlarge or better (16GB RAM, 4 vCPUs)
# - 200GB+ SSD storage
# - Security group: 22, 80, 443

# 2. Connect and setup
ssh ubuntu@your-instance-ip

# 3. Install dependencies
sudo apt update
sudo apt install -y docker.io docker-compose git

# 4. Clone and configure
git clone <repository-url>
cd ai-stack-build
cp .env.example .env

# 5. AWS-specific configuration
echo "DOMAIN=yourdomain.com" >> .env
echo "AWS_REGION=us-east-1" >> .env

# 6. Setup EBS volumes for data persistence
sudo mkfs -t ext4 /dev/xvdf  # Data volume
sudo mkdir /data
echo "/dev/xvdf /data ext4 defaults 0 0" | sudo tee -a /etc/fstab
sudo mount /dev/xvdf /data

# 7. Update docker-compose.yml volumes to use /data
sed -i 's|./data|/data|g' docker-compose.yml

# 8. Deploy
make setup
make up

# 9. Setup Route 53 DNS
# Point yourdomain.com to EC2 instance IP
```

### Google Cloud Platform

```bash
# 1. Create VM instance
# - Ubuntu 22.04 LTS
# - e2-standard-8 (32GB RAM, 8 vCPUs)
# - 200GB SSD persistent disk

# 2. Setup firewall
gcloud compute firewall-rules create ai-stack \
  --allow tcp:80,tcp:443,tcp:22 \
  --source-ranges 0.0.0.0/0

# 3. Deploy (similar to AWS steps)
# ... (same as AWS deployment)

# 4. Setup Cloud DNS
gcloud dns record-sets create yourdomain.com \
  --rrdatas=INSTANCE_IP \
  --type=A \
  --zone=your-zone
```

### DigitalOcean

```bash
# 1. Create Droplet
# - Ubuntu 22.04 LTS
# - 16GB RAM, 4 vCPUs minimum
# - 200GB SSD

# 2. Add domain in control panel
# Point yourdomain.com to Droplet IP

# 3. Deploy (same steps as AWS)
```

### Azure VM

```bash
# 1. Create VM
# - Ubuntu 22.04 LTS
# - Standard_D8s_v3 (32GB RAM, 8 vCPUs)
# - 200GB Premium SSD

# 2. Configure NSG (Network Security Group)
az network nsg rule create \
  --resource-group your-group \
  --nsg-name your-nsg \
  --name AllowHTTP \
  --priority 100 \
  --destination-port-ranges 80 443 \
  --access Allow \
  --protocol Tcp

# 3. Deploy (same steps)
```

## 🐳 Docker Swarm

### Swarm Setup

```bash
# 1. Initialize swarm
docker swarm init

# 2. Create overlay network
docker network create --driver overlay ai-stack-network

# 3. Deploy stack
docker stack deploy -c docker-compose.swarm.yml ai-stack

# 4. Scale services
docker service scale ai-stack_ollama=2
docker service scale ai-stack_litellm=3

# 5. Check status
docker stack ps ai-stack
docker service ls
```

### Swarm Configuration (`docker-compose.swarm.yml`)

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    networks:
      - ai-stack-network
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
      placement:
        constraints:
          - node.role == manager

  ollama:
    image: ollama/ollama:latest
    networks:
      - ai-stack-network
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
      restart_policy:
        condition: on-failure

  # ... other services with deploy configs
```

## ☸️ Kubernetes

### K8s Deployment

```bash
# 1. Install kubectl and helm
# 2. Setup cluster (minikube, EKS, GKE, etc.)

# 3. Create namespace
kubectl create namespace ai-stack

# 4. Apply configurations
kubectl apply -f k8s/

# 5. Check status
kubectl get pods -n ai-stack
kubectl get services -n ai-stack

# 6. Setup ingress
kubectl apply -f k8s/ingress.yml

# 7. Get service URLs
kubectl get ingress -n ai-stack
```

### Kubernetes Manifests Structure

```
k8s/
├── namespace.yml
├── configmaps/
│   ├── nginx-config.yml
│   └── app-config.yml
├── secrets/
│   ├── db-secrets.yml
│   └── api-keys.yml
├── services/
│   ├── nginx.yml
│   ├── monitoring.yml
│   ├── ollama.yml
│   └── ...
├── ingress.yml
├── persistent-volumes.yml
└── kustomization.yml
```

### Example Service Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: ai-stack
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        resources:
          limits:
            memory: "16Gi"
            cpu: "4000m"
          requests:
            memory: "8Gi"
            cpu: "2000m"
        volumeMounts:
        - name: ollama-storage
          mountPath: /root/.ollama
      volumes:
      - name: ollama-storage
        persistentVolumeClaim:
          claimName: ollama-pvc
```

## 🏗️ High Availability

### Multi-Node Setup

```bash
# 1. Setup load balancer (nginx/haproxy)
# 2. Configure shared storage (NFS/EFS)
# 3. Deploy with replicas
docker-compose -f docker-compose.ha.yml up -d

# 4. Setup monitoring
# Prometheus + Grafana for metrics
# AlertManager for notifications
```

### HA Configuration

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - monitoring
      - dify-web
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure

  monitoring:
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
      update_config:
        parallelism: 1
        delay: 10s

  redis:
    deploy:
      replicas: 3  # Redis cluster
      restart_policy:
        condition: on-failure
```

### Database HA

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_DB: dify
    secrets:
      - db_password
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    deploy:
      replicas: 2
      update_config:
        parallelism: 0  # Rolling update
```

## 💾 Backup & Recovery

### Automated Backups

```bash
# Setup cron jobs
sudo crontab -e

# Daily database backup
0 2 * * * docker exec ai-stack-db-1 pg_dump -U postgres dify > /backups/db-$(date +\%Y\%m\%d).sql

# Weekly full backup
0 3 * * 0 docker run --rm -v ai-stack_pgdata:/data -v $(pwd)/backups:/backups alpine tar czf /backups/full-$(date +\%Y\%m\%d).tar.gz -C /data .

# Model backups (monthly)
0 4 1 * * docker run --rm -v ai-stack_ollama_data:/data -v $(pwd)/backups:/backups alpine tar czf /backups/models-$(date +\%Y\%m\%d).tar.gz -C /data .
```

### Manual Backup

```bash
# Stop services for consistent backup
docker-compose stop

# Backup databases
docker exec ai-stack-db-1 pg_dump -U postgres dify > backup.sql
docker exec ai-stack-redis-1 redis-cli --rdb /backup/dump.rdb

# Backup volumes
docker run --rm -v ai-stack_pgdata:/data -v $(pwd):/backup alpine tar czf /backup/pgdata.tar.gz -C /data .
docker run --rm -v ai-stack_ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/models.tar.gz -C /data .

# Restart services
docker-compose start
```

### Recovery

```bash
# 1. Stop services
docker-compose down

# 2. Restore volumes
docker run --rm -v ai-stack_pgdata:/data -v $(pwd):/backup alpine tar xzf /backup/pgdata.tar.gz -C /data

# 3. Restore database
docker-compose up -d db
docker exec -i ai-stack-db-1 psql -U postgres dify < backup.sql

# 4. Start all services
docker-compose up -d

# 5. Verify
docker-compose ps
curl https://localhost/monitoring/
```

## 📊 Monitoring Setup

### External Monitoring

```bash
# 1. Setup Prometheus
docker run -d -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

# 2. Setup Grafana
docker run -d -p 3000:3000 grafana/grafana

# 3. Add data sources
# - Prometheus: http://prometheus:9090
# - Docker: unix:///var/run/docker.sock

# 4. Import dashboards
# - Docker monitoring dashboard
# - AI Stack custom dashboard
```

### Log Aggregation

```bash
# Setup ELK stack
docker-compose -f docker-compose.monitoring.yml up -d

# Configure filebeat
filebeat setup -e \
  -E output.logstash.enabled=false \
  -E output.elasticsearch.hosts=['elasticsearch:9200'] \
  -E setup.kibana.host=kibana:5601
```

### Alerting

```bash
# Setup AlertManager
docker run -d -p 9093:9093 \
  -v $(pwd)/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager

# Configure alerts for:
# - Service down
# - High CPU/memory usage
# - Disk space low
# - Database connection issues
```

## 🔧 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs [service-name]

# Check resource usage
docker stats

# Check configuration
docker-compose config

# Validate secrets
ls -la secrets/
cat secrets/monitoring_username
```

### Performance Issues

```bash
# Monitor resource usage
docker stats ai-stack

# Check service health
curl -k https://localhost/monitoring/

# Profile application
docker exec ai-stack-monitoring-1 python -m cProfile app.py

# Database performance
docker exec ai-stack-db-1 psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### Network Issues

```bash
# Check network connectivity
docker network ls
docker network inspect ai-stack

# Test service communication
docker exec ai-stack-monitoring-1 ping dify-api

# Check firewall rules
sudo iptables -L
sudo ufw status
```

### SSL/TLS Issues

```bash
# Test certificate
openssl s_client -connect localhost:443 -servername localhost

# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Renew Let's Encrypt
sudo certbot renew
docker-compose restart nginx
```

### Database Issues

```bash
# Check database status
docker exec ai-stack-db-1 pg_isready -U postgres

# View database logs
docker-compose logs db

# Connect to database
docker exec -it ai-stack-db-1 psql -U postgres -d dify

# Check disk usage
docker exec ai-stack-db-1 du -sh /var/lib/postgresql/data
```

### Memory Issues

```bash
# Check memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Adjust memory limits
# Edit docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G

# Restart services
docker-compose up -d
```

### Update Procedures

```bash
# Update all images
docker-compose pull

# Update specific service
docker-compose pull monitoring
docker-compose up -d monitoring

# Rolling update (zero downtime)
docker-compose up -d --scale monitoring=2
docker-compose up -d --scale monitoring=1

# Check update status
docker-compose ps
docker-compose logs --tail=50 monitoring
```

---

## 📞 Support

### Getting Help

1. **Check Documentation**: README.md, API_DOCUMENTATION.md
2. **Review Logs**: `make logs SERVICE=service-name`
3. **Health Check**: Visit monitoring dashboard
4. **Community**: GitHub Issues, Discussions

### Common Support Commands

```bash
# System information
uname -a
docker --version
docker-compose --version
free -h
df -h

# Service status
docker-compose ps
docker stats

# Recent logs
docker-compose logs --tail=100
docker-compose logs --since 1h

# Configuration validation
docker-compose config
```

### Emergency Procedures

```bash
# Quick restart all services
docker-compose restart

# Force recreate
docker-compose up -d --force-recreate

# Nuclear option (last resort)
docker-compose down -v
docker system prune -a --volumes
# Then redeploy from scratch
```

---

**Happy Deploying! 🚀**</content>
<parameter name="filePath">/home/steelburn/Development/ai-stack-build/DEPLOYMENT_GUIDE.md