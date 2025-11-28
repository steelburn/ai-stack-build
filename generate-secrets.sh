#!/bin/bash

# Security Enhancement Script
# Generates secure passwords and updates configuration files

set -e

# Error logging setup
LOG_FILE="${HOME}/ai-stack-install.log"
exec 2>>"$LOG_FILE"  # Redirect stderr to log file

# Error handling
error_handler() {
    local exit_code=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Secret generation failed at line $LINENO with exit code $exit_code - Check log file: $LOG_FILE" >> "$LOG_FILE"
    exit 1
}
trap error_handler ERR

echo "🔐 Generating secure secrets for AI Stack..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Secret generation started" >> "$LOG_FILE"

# Function to generate a secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to generate a secure API key
generate_api_key() {
    openssl rand -hex 32
}

# Generate new secrets
echo "Generating database password..."
DB_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
QDRANT_API_KEY=$(generate_api_key)
LITELLM_MASTER_KEY="sk-$(generate_api_key)"
LITELLM_SALT_KEY=$(generate_api_key)
N8N_ENCRYPTION_KEY=$(generate_api_key)
FLOWISE_SECRETKEY=$(generate_api_key)
OPENWEBUI_SECRET_KEY=$(generate_api_key)
OPENAI_API_KEY="sk-$(generate_api_key)"  # Placeholder - user should set real key
ANTHROPIC_API_KEY="sk-ant-$(generate_api_key)"  # Placeholder - user should set real key
UI_PASSWORD=$(generate_password)

# Create secrets directory
echo "Creating secrets directory..."
mkdir -p secrets

# Create individual secret files for Docker
echo "Creating Docker secret files..."
echo -n "$DB_PASSWORD" > secrets/ai-stack_db_password.txt
echo -n "$REDIS_PASSWORD" > secrets/ai-stack_redis_password.txt
echo -n "$QDRANT_API_KEY" > secrets/ai-stack_qdrant_api_key.txt
echo -n "$LITELLM_MASTER_KEY" > secrets/ai-stack_litellm_master_key.txt
echo -n "$LITELLM_SALT_KEY" > secrets/ai-stack_litellm_salt_key.txt
echo -n "$N8N_ENCRYPTION_KEY" > secrets/ai-stack_n8n_encryption_key.txt
echo -n "$FLOWISE_SECRETKEY" > secrets/ai-stack_flowise_secret_key.txt
echo -n "$OPENWEBUI_SECRET_KEY" > secrets/ai-stack_openwebui_secret_key.txt

# Create monitoring credentials (these are not auto-generated, use defaults or prompt user)
echo -n "${MONITORING_USERNAME:-admin}" > secrets/ai-stack_monitoring_username.txt
echo -n "${MONITORING_PASSWORD:-$(generate_password)}" > secrets/ai-stack_monitoring_password.txt
echo -n "${UI_USERNAME:-admin}" > secrets/ai-stack_ui_username.txt
echo -n "${UI_PASSWORD:-$LITELLM_MASTER_KEY}" > secrets/ai-stack_ui_password.txt

# Update .env file
echo "Updating .env file with secure secrets..."
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DB_PASSWORD/" .env
sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" .env
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env
sed -i "s/QDRANT_API_KEY=.*/QDRANT_API_KEY=$QDRANT_API_KEY/" .env
sed -i "s/LITELLM_MASTER_KEY=.*/LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY/" .env
sed -i "s/LITELLM_SALT_KEY=.*/LITELLM_SALT_KEY=$LITELLM_SALT_KEY/" .env
sed -i "s/N8N_ENCRYPTION_KEY=.*/N8N_ENCRYPTION_KEY=$N8N_ENCRYPTION_KEY/" .env
sed -i "s/FLOWISE_SECRETKEY=.*/FLOWISE_SECRETKEY=$FLOWISE_SECRETKEY/" .env
sed -i "s/OPENWEBUI_SECRET_KEY=.*/OPENWEBUI_SECRET_KEY=$OPENWEBUI_SECRET_KEY/" .env
sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" .env
sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY/" .env
sed -i "s/UI_USERNAME=.*/UI_USERNAME=admin/" .env
sed -i "s/UI_PASSWORD=.*/UI_PASSWORD=$LITELLM_MASTER_KEY/" .env

# Update DATABASE_URL in .env
DATABASE_URL="postgresql://postgres:$DB_PASSWORD@db:5432/dify"
sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env

# Update OPENMEMORY_DATABASE_URL
OPENMEMORY_DATABASE_URL="postgresql://postgres:$DB_PASSWORD@db:5432/dify"
sed -i "s|OPENMEMORY_DATABASE_URL=.*|OPENMEMORY_DATABASE_URL=$OPENMEMORY_DATABASE_URL|" .env

echo "✅ Secrets generated and .env updated!"
echo "✅ Docker secret files created in ./secrets/"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "1. The OPENAI_API_KEY and ANTHROPIC_API_KEY are placeholders. Replace them with your real API keys."
echo "2. Change default usernames and passwords in services that use them."
echo "3. Store this .env file and ./secrets/ directory securely and never commit them to version control."
echo "4. Consider using Docker secrets or external secret management for production."
echo "5. The monitoring credentials are set to defaults - change them for security."
echo ""
echo "🔑 Generated Secrets Summary:"
echo "Database Password: $DB_PASSWORD"
echo "Redis Password: $REDIS_PASSWORD"
echo "Qdrant API Key: $QDRANT_API_KEY"
echo "LiteLLM Master Key: $LITELLM_MASTER_KEY"
echo "N8N Encryption Key: $N8N_ENCRYPTION_KEY"
echo "Flowise Secret Key: $FLOWISE_SECRETKEY"
echo "OpenWebUI Secret Key: $OPENWEBUI_SECRET_KEY"
echo "UI Password: $UI_PASSWORD"