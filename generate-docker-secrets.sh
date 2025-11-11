#!/bin/bash

# Generate Docker secrets from .env file
# This creates individual secret files for sensitive data

set -e

SECRETS_DIR="./secrets"
mkdir -p "$SECRETS_DIR"

echo "🔐 Generating Docker secrets from .env file..."

# Function to extract value from .env
get_env_value() {
    grep "^$1=" .env | cut -d '=' -f2- | sed 's/^"//' | sed 's/"$//'
}

# Generate secrets
echo "$(get_env_value 'POSTGRES_PASSWORD')" > "$SECRETS_DIR/db_password.txt"
echo "$(get_env_value 'REDIS_PASSWORD')" > "$SECRETS_DIR/redis_password.txt"
echo "$(get_env_value 'QDRANT_API_KEY')" > "$SECRETS_DIR/qdrant_api_key.txt"
echo "$(get_env_value 'LITELLM_MASTER_KEY')" > "$SECRETS_DIR/litellm_master_key.txt"
echo "$(get_env_value 'LITELLM_SALT_KEY')" > "$SECRETS_DIR/litellm_salt_key.txt"
echo "$(get_env_value 'N8N_ENCRYPTION_KEY')" > "$SECRETS_DIR/n8n_encryption_key.txt"
echo "$(get_env_value 'FLOWISE_SECRETKEY')" > "$SECRETS_DIR/flowise_secret_key.txt"
echo "$(get_env_value 'OPENWEBUI_SECRET_KEY')" > "$SECRETS_DIR/openwebui_secret_key.txt"
echo "$(get_env_value 'MONITORING_USERNAME')" > "$SECRETS_DIR/monitoring_username.txt"
echo "$(get_env_value 'MONITORING_PASSWORD')" > "$SECRETS_DIR/monitoring_password.txt"
echo "$(get_env_value 'UI_USERNAME')" > "$SECRETS_DIR/ui_username.txt"
echo "$(get_env_value 'UI_PASSWORD')" > "$SECRETS_DIR/ui_password.txt"

# Set proper permissions
chmod 600 "$SECRETS_DIR"/*.txt

echo "✅ Docker secrets generated in $SECRETS_DIR/"
echo ""
echo "📋 Generated secrets:"
ls -la "$SECRETS_DIR/"
echo ""
echo "⚠️  SECURITY NOTES:"
echo "1. These files contain sensitive information"
echo "2. Ensure proper file permissions (600)"
echo "3. Never commit these files to version control"
echo "4. Use Docker secrets in production environments"