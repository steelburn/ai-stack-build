.PHONY: help setup up down logs clean install-docker pull-models status security-setup generate-secrets harden-security update backup restore monitor shell exec scale test health stop start restart ps config pull push logs-tail backup-db backup-models

# Default target
help: ## Show this help message
	@echo "AI Stack Management Commands:"
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'

# === SETUP & INSTALLATION ===
setup: ## Run the complete setup process
	./setup.sh

configure-domain: ## Configure public domain for nginx reverse proxy
	@echo "🌐 Public Domain Configuration"
	@echo "================================"
	@echo "This will be used for proper URL configuration in production."
	@echo "For development, you can use 'https://localhost'"
	@echo "For production, use your actual domain like 'https://yourdomain.com'"
	@echo
	@if [ -f ".env" ] && grep -q "^PUBLIC_DOMAIN=" .env; then \
		echo "Current public domain: $$(grep "^PUBLIC_DOMAIN=" .env | cut -d'=' -f2)"; \
		read -p "Do you want to change it? [y/N]: " change_domain; \
		if [ "$$change_domain" = "y" ] || [ "$$change_domain" = "Y" ]; then \
			read -p "Enter your public domain (e.g., https://yourdomain.com): " PUBLIC_DOMAIN; \
		else \
			PUBLIC_DOMAIN=$$(grep "^PUBLIC_DOMAIN=" .env | cut -d'=' -f2); \
		fi; \
	else \
		read -p "Enter your public domain (e.g., https://yourdomain.com or https://localhost for development): " PUBLIC_DOMAIN; \
	fi; \
	if echo "$$PUBLIC_DOMAIN" | grep -q "^https\?://"; then \
		if grep -q "^PUBLIC_DOMAIN=" .env; then \
			sed -i "s|^PUBLIC_DOMAIN=.*$$|PUBLIC_DOMAIN=$${PUBLIC_DOMAIN}|" .env; \
		else \
			echo "PUBLIC_DOMAIN=$${PUBLIC_DOMAIN}" >> .env; \
		fi; \
		echo "✓ Public domain set to: $${PUBLIC_DOMAIN}"; \
	else \
		echo "✗ Invalid domain format. Must start with http:// or https://"; \
		echo "Using default: https://localhost"; \
		if grep -q "^PUBLIC_DOMAIN=" .env; then \
			sed -i "s|^PUBLIC_DOMAIN=.*$$|PUBLIC_DOMAIN=https://localhost|" .env; \
		else \
			echo "PUBLIC_DOMAIN=https://localhost" >> .env; \
		fi; \
	fi

install-docker: ## Install Docker Engine and Docker Compose V2 (requires sudo)
	@echo "Installing Docker Engine and Docker Compose V2..."
	curl -fsSL https://get.docker.com -o get-docker.sh
	sudo sh get-docker.sh
	sudo usermod -aG docker $(USER)
	@echo "Docker installed. Please log out and back in for group changes to take effect."

	# Install Docker Compose V2 plugin
	if ! docker compose version >/dev/null 2>&1; then \
		sudo mkdir -p /usr/libexec/docker/cli-plugins; \
		sudo curl -SL https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-linux-$(uname -m) -o /usr/libexec/docker/cli-plugins/docker-compose; \
		sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose; \
		echo "Docker Compose V2 installed successfully."; \
	else \
		echo "Docker Compose V2 is already installed."; \
	fi

security-setup: generate-secrets generate-docker-secrets generate-ssl ## Run complete security setup (secrets, Docker secrets, SSL)

generate-secrets: ## Generate cryptographically secure passwords and API keys
	./generate-secrets.sh

generate-docker-secrets: ## Create Docker secret files from .env
	./generate-docker-secrets.sh

generate-ssl: ## Generate self-signed SSL certificates
	./generate-ssl.sh

harden-security: ## Apply host-level security hardening (requires sudo)
	sudo ./harden-security.sh

# === SERVICE MANAGEMENT ===
up: ## Start all services in detached mode
	docker compose up -d

up-db-admin: ## Start all services including database admin (Adminer)
	docker compose --profile db-admin up -d

start: up ## Alias for up

down: ## Stop all services
	docker compose down

stop: down ## Alias for down

restart: ## Restart all services
	docker compose restart

ps: status ## Alias for status

status: ## Show status of all services
	docker compose ps

config: ## Validate and show compose configuration
	docker compose config

pull: ## Pull latest images for all services
	docker compose pull

update: pull up ## Update all images and restart services

# === MONITORING & LOGS ===
logs: ## View logs from all services (follow mode)
	docker compose logs -f

logs-tail: ## View last 100 lines from all services
	docker compose logs --tail=100

monitor: ## Open monitoring dashboard in browser (Linux)
	xdg-open https://localhost/monitoring/ 2>/dev/null || echo "Open https://localhost/monitoring/ in your browser"

health: ## Check health status of all services
	curl -k https://localhost/monitoring/ | python3 -m json.tool || echo "Monitoring service not available"

# === DEVELOPMENT ===
shell: ## Enter shell in monitoring container
	docker compose exec monitoring bash

exec: ## Execute command in service container (usage: make exec SERVICE=monitoring CMD="python --version")
	docker compose exec $(SERVICE) $(CMD)

scale: ## Scale a service (usage: make scale SERVICE=ollama REPLICAS=2)
	docker compose up -d --scale $(SERVICE)=$(REPLICAS)

test: ## Run tests in monitoring service
	docker compose exec monitoring python -m pytest --tb=short

# === BACKUP & RECOVERY ===
backup: backup-db backup-models ## Create full backup of data volumes
	@echo "Full backup completed"

backup-db: ## Backup database volume
	@echo "Backing up database..."
	mkdir -p backup
	docker run --rm -v ai-stack_db_data:/data -v $(PWD)/backup:/backup alpine tar czf /backup/db_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .

backup-models: ## Backup Ollama models volume
	@echo "Backing up models..."
	mkdir -p backup
	docker run --rm -v ai-stack_ollama_data:/data -v $(PWD)/backup:/backup alpine tar czf /backup/models_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .

restore: ## Restore from backup (usage: make restore FILE=backup/db_20241201.tar.gz VOLUME=db_data)
	@echo "Restoring $(FILE) to $(VOLUME)..."
	docker run --rm -v ai-stack_$(VOLUME):/data -v $(PWD):/backup alpine tar xzf /backup/$(FILE) -C /data

# === MAINTENANCE ===
clean: ## Stop services and remove containers, networks
	docker compose down --remove-orphans

clean-all: ## Stop services and remove everything including volumes (WARNING: destroys data)
	docker compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

clean-images: ## Remove unused Docker images
	docker image prune -f

# === MODEL MANAGEMENT ===
pull-models: ## Pull common models in Ollama
	@echo "Pulling common models..."
	docker compose exec ollama ollama pull llama3.2
	docker compose exec ollama ollama pull nomic-embed-text
	docker compose exec ollama ollama pull codellama

list-models: ## List available models in Ollama
	docker compose exec ollama ollama list

# === TROUBLESHOOTING ===
diagnose: ## Run diagnostic checks
	@echo "=== System Resources ==="
	free -h
	@echo ""
	@echo "=== Disk Usage ==="
	df -h
	@echo ""
	@echo "=== Docker Status ==="
	docker system df
	@echo ""
	@echo "=== Service Status ==="
	docker compose ps
	@echo ""
	@echo "=== Recent Logs ==="
	docker compose logs --tail=20

check-ports: ## Check if required ports are available
	@echo "Checking port availability..."
	lsof -i :80 || echo "Port 80: Available"
	lsof -i :443 || echo "Port 443: Available"
	lsof -i :8080 || echo "Port 8080: Available"
	lsof -i :3000 || echo "Port 3000: Available"
	lsof -i :5678 || echo "Port 5678: Available"

# === UTILITIES ===
env-check: ## Check environment configuration
	@echo "=== Environment Check ==="
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker compose version)"
	@echo "Python version: $(shell python3 --version)"
	@echo "Make version: $(shell make --version | head -1)"
	@echo ""
	@echo "=== Configuration Files ==="
	@[ -f .env ] && echo "✓ .env exists" || echo "✗ .env missing"
	@[ -f docker-compose.yml ] && echo "✓ docker-compose.yml exists" || echo "✗ docker-compose.yml missing"
	@[ -d secrets ] && echo "✓ secrets directory exists" || echo "✗ secrets directory missing"
	@[ -d nginx/ssl ] && echo "✓ SSL certificates directory exists" || echo "✗ SSL certificates directory missing"
	@echo ""
	@echo "=== Required Environment Variables ==="
	@if [ -f .env ]; then \
		for var in DB_HOST DB_PORT DB_USERNAME DB_PASSWORD DB_DATABASE REDIS_HOST REDIS_PORT REDIS_PASSWORD VECTOR_STORE QDRANT_URL QDRANT_API_KEY STORAGE_TYPE STORAGE_LOCAL_PATH; do \
			if grep -q "^$$var=" .env; then \
				echo "✓ $$var is set"; \
			else \
				echo "✗ $$var is missing"; \
			fi; \
		done; \
	else \
		echo "Cannot check variables: .env file missing"; \
	fi

version: ## Show versions of key components
	@echo "=== AI Stack Versions ==="
	@echo "Docker: $(shell docker --version)"
	@echo "Docker Compose: $(shell docker compose version)"
	@echo "Python: $(shell python3 --version)"
	@echo "Git: $(shell git --version)"
	@echo ""
	@echo "=== Service Versions ==="
	@echo "Ollama: $(shell docker compose exec ollama ollama --version 2>/dev/null || echo 'Not running')"
	@echo "PostgreSQL: $(shell docker compose exec db postgres --version 2>/dev/null | head -1 || echo 'Not running')"
	@echo "Redis: $(shell docker compose exec redis redis-server --version 2>/dev/null | head -1 || echo 'Not running')"

uninstall: ## Remove all containers and images
	docker compose down --rmi all --volumes --remove-orphans