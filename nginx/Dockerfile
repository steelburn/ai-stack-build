FROM nginx:alpine

# Install apache2-utils for htpasswd
RUN apk add --no-cache apache2-utils

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy SSL certificates
COPY ssl/nginx-selfsigned.crt /etc/ssl/certs/nginx-selfsigned.crt
COPY ssl/nginx-selfsigned.key /etc/ssl/private/nginx-selfsigned.key

# Create upstream configuration directory and initial dummy upstreams
RUN mkdir -p /etc/nginx/conf.d/upstreams && \
    rm -f /etc/nginx/conf.d/default.conf && \
    rm -f /etc/nginx/conf.d/upstreams/default.conf && \
    echo 'upstream dify { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/dify.conf && \
    echo 'upstream n8n { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/n8n.conf && \
    echo 'upstream flowise { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/flowise.conf && \
    echo 'upstream openwebui { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/openwebui.conf && \
    echo 'upstream litellm { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/litellm.conf && \
    echo 'upstream monitoring { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/monitoring.conf && \
    echo 'upstream openmemory { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/openmemory.conf && \
    echo 'upstream ollama { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/ollama.conf && \
    echo 'upstream ollama-webui { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/ollama-webui.conf && \
    echo 'upstream adminer { server 127.0.0.1:1; }' > /etc/nginx/conf.d/upstreams/adminer.conf

# Create log directory
RUN mkdir -p /var/log/nginx

# Create adminer htpasswd file
RUN echo "${ADMINER_USERNAME:-admin}:$(openssl passwd -apr1 ${ADMINER_PASSWORD:-password})" > /etc/nginx/.htpasswd_adminer

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1