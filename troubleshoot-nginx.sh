#!/bin/bash

echo "=========================================="
echo "🔧 NGINX TROUBLESHOOTING TOOL"
echo "=========================================="

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
        return 1
    fi
}

log "🔍 Starting Nginx diagnostics..."

# 1. Check if Nginx is installed
log "📦 Checking Nginx installation..."
if command -v nginx &> /dev/null; then
    log "✅ Nginx is installed"
    nginx -v
else
    log "❌ Nginx is not installed"
    log "💡 Install Nginx with: sudo apt update && sudo apt install nginx"
    exit 1
fi

# 2. Check Nginx service status
log "📊 Checking Nginx service status..."
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx service is running"
else
    log "❌ Nginx service is not running"
fi

# 3. Check Nginx configuration
log "🔧 Testing Nginx configuration..."
sudo nginx -t
check_status "Nginx configuration test"

# 4. Check if ports are available
log "🔍 Checking port availability..."
if sudo lsof -i :80 >/dev/null 2>&1; then
    log "⚠️  Port 80 is in use by:"
    sudo lsof -i :80
else
    log "✅ Port 80 is free"
fi

if sudo lsof -i :443 >/dev/null 2>&1; then
    log "⚠️  Port 443 is in use by:"
    sudo lsof -i :443
else
    log "✅ Port 443 is free"
fi

# 5. Check Nginx configuration files
log "📁 Checking Nginx configuration files..."
if [ -f /etc/nginx/nginx.conf ]; then
    log "✅ Main nginx.conf exists"
else
    log "❌ Main nginx.conf missing"
fi

if [ -d /etc/nginx/sites-available ]; then
    log "✅ Sites-available directory exists"
    ls -la /etc/nginx/sites-available/
else
    log "❌ Sites-available directory missing"
fi

if [ -d /etc/nginx/sites-enabled ]; then
    log "✅ Sites-enabled directory exists"
    ls -la /etc/nginx/sites-enabled/
else
    log "❌ Sites-enabled directory missing"
fi

# 6. Check SSL certificate files
log "🔐 Checking SSL certificate files..."
DOMAIN="dev-ngurah.fun"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ -f "$CERT_PATH" ]; then
    log "✅ SSL certificate exists: $CERT_PATH"
else
    log "❌ SSL certificate missing: $CERT_PATH"
fi

if [ -f "$KEY_PATH" ]; then
    log "✅ SSL private key exists: $KEY_PATH"
else
    log "❌ SSL private key missing: $KEY_PATH"
fi

# 7. Check Nginx logs
log "📋 Checking Nginx logs..."
if [ -f /var/log/nginx/error.log ]; then
    log "📋 Recent error logs:"
    sudo tail -n 5 /var/log/nginx/error.log
else
    log "⚠️  No error log found"
fi

if [ -f /var/log/nginx/access.log ]; then
    log "📋 Recent access logs:"
    sudo tail -n 5 /var/log/nginx/access.log
else
    log "⚠️  No access log found"
fi

# 8. Check systemd logs
log "📋 Checking systemd logs for Nginx..."
sudo journalctl -u nginx --no-pager -n 10

# 9. Try to start Nginx if not running
log "🚀 Attempting to start Nginx..."
if ! sudo systemctl is-active --quiet nginx; then
    log "🔄 Starting Nginx..."
    sudo systemctl start nginx
    sleep 2
    
    if sudo systemctl is-active --quiet nginx; then
        log "✅ Nginx started successfully"
    else
        log "❌ Nginx failed to start"
        log "📋 Detailed Nginx status:"
        sudo systemctl status nginx --no-pager -l
    fi
fi

# 10. Test Nginx functionality
log "🧪 Testing Nginx functionality..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80 | grep -q "200\|301\|302"; then
    log "✅ Nginx is responding on port 80"
else
    log "❌ Nginx is not responding on port 80"
fi

if curl -s -o /dev/null -w "%{http_code}" https://localhost:443 2>/dev/null | grep -q "200\|301\|302"; then
    log "✅ Nginx is responding on port 443"
else
    log "❌ Nginx is not responding on port 443"
fi

echo ""
log "🔧 Troubleshooting complete!"
log "💡 If Nginx is still not working, check the logs above for specific errors."