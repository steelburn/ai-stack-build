#!/bin/bash

# Generate self-signed SSL certificates for development
# This creates certificates for localhost HTTPS access

set -e

CERT_DIR="./nginx/ssl"
mkdir -p "$CERT_DIR"

echo "🔐 Generating self-signed SSL certificates for development..."

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