# Configuration Service Remote Deployment Guide

## Overview
This guide explains how to deploy and test the AI Stack Configuration Service on the remote server at `192.168.88.120`.

## Prerequisites
- SSH access to `192.168.88.120`
- Docker and docker-compose installed on the remote server
- The ai-stack-build repository cloned on the remote server

## Deployment Steps

### 1. Transfer Files to Remote Server
```bash
# From your local machine, copy the deployment files
scp deploy-config-service.sh steelburn@192.168.88.120:~/Development/ai-stack-build/
scp test-config-service.sh steelburn@192.168.88.120:~/Development/ai-stack-build/

# Or if you have the entire repo, you can rsync the config-service directory
rsync -avz config-service/ steelburn@192.168.88.120:~/Development/ai-stack-build/config-service/
```

### 2. SSH to Remote Server
```bash
ssh steelburn@192.168.88.120
cd ~/Development/ai-stack-build
```

### 3. Deploy the Configuration Service
```bash
# Run the deployment script
./deploy-config-service.sh
```

### 4. Test the Deployment
```bash
# Run the test script to verify everything is working
./test-config-service.sh
```

## Access the Service

Once deployed, the configuration service will be available at:
- **Web Interface**: http://192.168.88.120:8083
- **API Endpoints**:
  - Services: http://192.168.88.120:8083/api/services
  - Config Files: http://192.168.88.120:8083/api/config/files
  - Database Query: http://192.168.88.120:8083/api/database/query

## Troubleshooting

### Service Not Starting
```bash
# Check logs
docker-compose logs config-service

# Check if port 8083 is available
netstat -tlnp | grep 8083

# Restart the service
docker-compose restart config-service
```

### Permission Issues
```bash
# Check Docker socket permissions
ls -la /var/run/docker.sock

# If needed, add user to docker group
sudo usermod -aG docker $USER
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check database logs
docker-compose logs db
```

## Available Features

The configuration service provides:

1. **Service Management**: View, start, stop, and restart Docker services
2. **Configuration File Editing**: Edit nginx.conf, docker-compose.yml, .env, and other config files
3. **Database Queries**: Execute SQL queries against the PostgreSQL database
4. **Nginx Reload**: Reload nginx configuration without restarting

## Development Testing

For ongoing development and testing:

1. Make changes locally
2. Transfer updated files to remote server
3. Run deployment script: `./deploy-config-service.sh`
4. Run tests: `./test-config-service.sh`
5. Access web interface to verify changes

## Logs and Monitoring

```bash
# View service logs
docker-compose logs -f config-service

# View all logs
docker-compose logs -f

# Check resource usage
docker stats
```