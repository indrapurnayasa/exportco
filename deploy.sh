#!/bin/bash

echo "=========================================="
echo "🚀 STARTING DEPLOYMENT"
echo "=========================================="

# Set domain
DOMAIN="dev-ngurah.fun"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        log "✅ $1"
    else
        log "❌ $1"
        exit 1
    fi
}

# Kill any processes using our ports
log "🛑 Clearing ports..."
./kill-ports.sh
check_status "Ports cleared"

# Pull latest code
log "📥 Pulling latest code..."
git pull origin main
check_status "Code pulled"

# Activate conda environment
log "🐍 Activating conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate hackathon-env
check_status "Conda environment activated"

# Install/update dependencies
log "📦 Installing dependencies..."
pip install -r requirements.txt
check_status "Dependencies installed"

# Check SSL certificate
log "🔐 Checking SSL certificate..."
if ! sudo certbot certificates | grep -q "$DOMAIN"; then
    log "⚠️  SSL certificate not found, generating..."
    sudo systemctl stop nginx
    sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    sudo systemctl start nginx
    check_status "SSL certificate generated"
else
    log "✅ SSL certificate exists"
fi

# Create/update nginx configuration
log "🌐 Updating nginx configuration..."
sudo tee /etc/nginx/sites-available/$DOMAIN << 'NGINX_EOF'
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
NGINX_EOF

# Enable nginx configuration
sudo rm -f /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Test and reload nginx
sudo nginx -t
check_status "Nginx configuration test"

# Enhanced Nginx service management
log "🌐 Managing Nginx service..."

# Check current Nginx status
if sudo systemctl is-active --quiet nginx; then
    log "🔄 Nginx is active, reloading..."
    sudo systemctl reload nginx
    if [ $? -eq 0 ]; then
        log "✅ Nginx reloaded successfully"
    else
        log "❌ Nginx reload failed, trying restart..."
        sudo systemctl restart nginx
        check_status "Nginx restarted"
    fi
else
    log "⚠️  Nginx is not active, starting service..."
    
    # Try to start Nginx
    sudo systemctl start nginx
    if [ $? -eq 0 ]; then
        log "✅ Nginx started successfully"
    else
        log "❌ Nginx start failed, checking logs..."
        sudo journalctl -u nginx --no-pager -n 10
        log "🔧 Trying to enable and start Nginx..."
        sudo systemctl enable nginx
        sudo systemctl start nginx
        check_status "Nginx enabled and started"
    fi
fi

# Verify Nginx is actually running
sleep 2
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx is now running"
else
    log "❌ Nginx failed to start, showing detailed status..."
    sudo systemctl status nginx --no-pager -l
    log "📋 Nginx error logs:"
    sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
    exit 1
fi

# Start FastAPI service
log "🚀 Starting FastAPI service..."
./start-production-ssl.sh
check_status "FastAPI service started"

# Wait a moment for services to start
sleep 5

# Check service status
log "📊 Checking service status..."
./status-production-ssl.sh

# Test the service
log "🧪 Testing service..."
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/api/v1/export/seasonal-trend | grep -q "200"; then
    log "✅ API endpoint test passed"
else
    log "❌ API endpoint test failed"
fi

log "✅ Deployment completed!"
log "🌐 Your API is available at: https://$DOMAIN"