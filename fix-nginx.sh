#!/bin/bash

echo "=== Fixing Nginx Configuration ==="

# 1. Backup current config
echo "Backing up current nginx config..."
cp /etc/nginx/sites-enabled/hackathon-service /etc/nginx/sites-enabled/hackathon-service.backup

# 2. Create correct nginx configuration
echo "Creating correct nginx configuration..."
cat > /etc/nginx/sites-enabled/hackathon-service << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration (you'll need to add your SSL certificates)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
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
    
    # Proxy settings
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
nginx -t

# 4. If test passes, restart nginx
if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    systemctl restart nginx
    systemctl status nginx
else
    echo "❌ Nginx configuration still has errors"
    echo "Check the configuration manually"
fi

echo "Nginx configuration fix completed!" 