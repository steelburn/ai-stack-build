FROM nginx:alpine

# Install apache2-utils for htpasswd
RUN apk add --no-cache apache2-utils

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy SSL certificates
COPY ssl/nginx-selfsigned.crt /etc/ssl/certs/nginx-selfsigned.crt
COPY ssl/nginx-selfsigned.key /etc/ssl/private/nginx-selfsigned.key

# Create log directory
RUN mkdir -p /var/log/nginx

# Create adminer htpasswd file
RUN echo "${ADMINER_USERNAME:-admin}:$(openssl passwd -apr1 ${ADMINER_PASSWORD:-password})" > /etc/nginx/.htpasswd_adminer

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1