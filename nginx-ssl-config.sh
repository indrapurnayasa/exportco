#!/bin/bash

echo "=========================================="
echo "🔧 FIXING NGINX CORS CONFIGURATION"
echo "=========================================="

# Create proper SSL nginx config WITHOUT CORS headers
sudo tee /etc/nginx/sites-available/dev-ngurah.fun << 'EOF'
server {
    listen 80;
    server_name dev-ngurah.fun www.dev-ngurah.fun;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dev-ngurah.fun www.dev-ngurah.fun;
    
    ssl_certificate /etc/letsencrypt/live/dev-ngurah.fun/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dev-ngurah.fun/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the configuration
sudo rm -f /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/dev-ngurah.fun /etc/nginx/sites-enabled/

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx

echo "✅ Nginx CORS headers removed - FastAPI will handle CORS"
echo "🌐 Test your API: https://dev-ngurah.fun/api/v1/export/country-demand"