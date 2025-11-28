#!/bin/bash

# Generate self-signed SSL certificates for development
# This creates certificates for localhost HTTPS access

set -e

# Error logging setup
LOG_FILE="${HOME}/ai-stack-install.log"
exec 2>>"$LOG_FILE"  # Redirect stderr to log file

# Error handling
error_handler() {
    local exit_code=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] SSL generation failed at line $LINENO with exit code $exit_code - Check log file: $LOG_FILE" >> "$LOG_FILE"
    exit 1
}
trap error_handler ERR

CERT_DIR="./nginx/ssl"
mkdir -p "$CERT_DIR"

echo "🔐 Generating self-signed SSL certificates for development..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] SSL certificate generation started" >> "$LOG_FILE"

# Generate private key
openssl genrsa -out "$CERT_DIR/nginx-selfsigned.key" 2048

# Generate certificate
openssl req -new -x509 -key "$CERT_DIR/nginx-selfsigned.key" -out "$CERT_DIR/nginx-selfsigned.crt" -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "✅ SSL certificates generated in $CERT_DIR/"
echo ""
echo "📋 Certificate details:"
openssl x509 -in "$CERT_DIR/nginx-selfsigned.crt" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)" | head -4

echo ""
echo "⚠️  SECURITY WARNING:"
echo "These are self-signed certificates for development only."
echo "For production, use certificates from a trusted CA like Let's Encrypt."
echo "Browser will show security warnings - this is expected for self-signed certs."