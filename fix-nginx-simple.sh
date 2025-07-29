#!/bin/bash

echo "=========================================="
echo "🔧 SIMPLE NGINX FIX"
echo "=========================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

DOMAIN="dev-ngurah.fun"

log "🔍 Starting simple Nginx fix..."

# Step 1: Stop everything first
log "🛑 Step 1: Stopping all services..."
sudo systemctl stop nginx 2>/dev/null || true
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
sleep 2

# Step 2: Check what's using ports
log "🔍 Step 2: Checking port usage..."
echo "Port 80:"
sudo lsof -i :80 2>/dev/null || echo "Port 80 is free"
echo "Port 443:"
sudo lsof -i :443 2>/dev/null || echo "Port 443 is free"
echo "Port 8000:"
sudo lsof -i :8000 2>/dev/null || echo "Port 8000 is free"

# Step 3: Check Nginx configuration
log "🔧 Step 3: Testing Nginx configuration..."
sudo nginx -t
if [ $? -ne 0 ]; then
    log "❌ Nginx configuration has errors"
    log "📋 Nginx configuration test output:"
    sudo nginx -t 2>&1
    exit 1
else
    log "✅ Nginx configuration is valid"
fi

# Step 4: Check SSL certificate files
log "🔐 Step 4: Checking SSL certificates..."
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ -f "$CERT_PATH" ] && [ -f "$KEY_PATH" ]; then
    log "✅ SSL certificate files exist"
    ls -la "$CERT_PATH"
    ls -la "$KEY_PATH"
else
    log "❌ SSL certificate files missing"
    log "🔧 Regenerating SSL certificate..."
    sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
fi

# Step 5: Fix permissions
log "🔧 Step 5: Fixing permissions..."
sudo chmod 644 "$CERT_PATH" 2>/dev/null || true
sudo chmod 600 "$KEY_PATH" 2>/dev/null || true
sudo chown root:root "$CERT_PATH" "$KEY_PATH" 2>/dev/null || true

# Step 6: Start Nginx
log "🚀 Step 6: Starting Nginx..."
sudo systemctl start nginx
sleep 3

# Step 7: Check if Nginx started
log "🔍 Step 7: Checking Nginx status..."
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx is running"
    sudo systemctl status nginx --no-pager -l
else
    log "❌ Nginx failed to start"
    log "📋 Nginx error logs:"
    sudo journalctl -u nginx --no-pager -n 10
    log "📋 Nginx error log file:"
    sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
    exit 1
fi

# Step 8: Check if Nginx is listening
log "🔍 Step 8: Checking if Nginx is listening..."
if sudo lsof -i :80 | grep -q nginx; then
    log "✅ Nginx is listening on port 80"
else
    log "❌ Nginx is not listening on port 80"
fi

if sudo lsof -i :443 | grep -q nginx; then
    log "✅ Nginx is listening on port 443"
else
    log "❌ Nginx is not listening on port 443"
fi

# Step 9: Test connections
log "🧪 Step 9: Testing connections..."
echo "Testing HTTP (should redirect to HTTPS):"
curl -I "http://$DOMAIN" 2>/dev/null | head -3 || echo "HTTP connection failed"

echo "Testing HTTPS:"
curl -I "https://$DOMAIN" 2>/dev/null | head -3 || echo "HTTPS connection failed"

log "✅ Nginx fix completed!"
log "💡 If Nginx is still not working, check the logs above for specific errors."