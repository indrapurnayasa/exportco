#!/bin/bash

echo "=== Fixing Nginx Configuration After SSL ==="

# 1. Backup current config
echo "Backing up current nginx config..."
sudo cp /etc/nginx/sites-enabled/hackathon-service /etc/nginx/sites-enabled/hackathon-service.backup.$(date +%Y%m%d_%H%M%S)

# 2. Create proper nginx configuration with SSL
echo "Creating proper nginx configuration with SSL..."
sudo tee /etc/nginx/sites-enabled/hackathon-service > /dev/null << 'EOF'
server {
    listen 80;
    server_name dev-ngurah.fun;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dev-ngurah.fun;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/dev-ngurah.fun-0001/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dev-ngurah.fun-0001/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;

    # Client max body size
    client_max_body_size 100M;

    # Proxy settings for FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Specific proxy for /docs
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy for OpenAPI JSON
    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/hackathon-service/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 3. Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

# 4. If test passes, restart nginx
if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    sudo systemctl restart nginx
    sudo systemctl status nginx
else
    echo "❌ Nginx configuration has errors"
    echo "Check the configuration manually"
fi

echo "Nginx configuration fix completed!" 