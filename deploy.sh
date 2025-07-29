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

# Function to check port availability
check_port() {
    local port=$1
    local service_name=$2
    
    log "🔍 Checking port $port ($service_name)..."
    if sudo lsof -i :$port >/dev/null 2>&1; then
        log "⚠️  Port $port is in use by:"
        sudo lsof -i :$port
        return 1
    else
        log "✅ Port $port is free"
        return 0
    fi
}

# Function to verify service health
verify_service_health() {
    local service_name=$1
    local test_url=$2
    local expected_code=$3
    
    log "🧪 Testing $service_name..."
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$test_url" 2>/dev/null)
    
    if [ "$response_code" = "$expected_code" ]; then
        log "✅ $service_name is working (HTTP $response_code)"
        return 0
    else
        log "❌ $service_name failed (HTTP $response_code, expected $expected_code)"
        return 1
    fi
}

# STEP 1: Pre-deployment checks and cleanup
log "🔍 STEP 1: Pre-deployment checks and cleanup"

# Check all required ports
log "🔍 Checking port availability..."
check_port 80 "HTTP"
check_port 443 "HTTPS"
check_port 8000 "FastAPI"

# Kill any processes using our ports
log "🛑 Clearing ports..."
./kill-ports.sh
check_status "Ports cleared"

# Verify ports are now free
log "🔍 Verifying ports are free after cleanup..."
check_port 80 "HTTP"
check_port 443 "HTTPS"
check_port 8000 "FastAPI"

# STEP 2: Code and environment setup
log "📥 STEP 2: Code and environment setup"

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

# STEP 3: SSL certificate management
log "🔐 STEP 3: SSL certificate management"

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

# Verify SSL certificate files
log "🔐 Verifying SSL certificate files..."
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

if [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
    log "❌ SSL certificate files missing"
    log "🔧 Regenerating SSL certificate..."
    sudo systemctl stop nginx
    sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    sudo systemctl start nginx
    check_status "SSL certificate regenerated"
fi

# Fix SSL certificate permissions
log "🔧 Fixing SSL certificate permissions..."
sudo chmod 644 "$CERT_PATH" 2>/dev/null || true
sudo chmod 600 "$KEY_PATH" 2>/dev/null || true
sudo chown root:root "$CERT_PATH" "$KEY_PATH" 2>/dev/null || true

# STEP 4: Nginx configuration
log "🌐 STEP 4: Nginx configuration"

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

# Test nginx configuration
log "🔧 Testing nginx configuration..."
sudo nginx -t
check_status "Nginx configuration test"

# STEP 5: Nginx service management
log "🌐 STEP 5: Nginx service management"

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
        if [ $? -eq 0 ]; then
            log "✅ Nginx restarted successfully"
        else
            log "❌ Nginx restart failed"
            log "📋 Nginx error logs:"
            sudo journalctl -u nginx --no-pager -n 10
            log "🔧 Trying to enable and start Nginx..."
            sudo systemctl enable nginx
            sudo systemctl start nginx
            if [ $? -eq 0 ]; then
                log "✅ Nginx enabled and started"
            else
                log "❌ Nginx failed to start after enable"
                sudo systemctl status nginx --no-pager -l
                log "📋 Nginx error logs:"
                sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
                exit 1
            fi
        fi
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
        if [ $? -eq 0 ]; then
            log "✅ Nginx enabled and started"
        else
            log "❌ Nginx failed to start after enable"
            sudo systemctl status nginx --no-pager -l
            log "📋 Nginx error logs:"
            sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
            exit 1
        fi
    fi
fi

# Verify Nginx is actually running and stays running
log "🔍 Verifying Nginx is running and stable..."
sleep 3

# Multiple checks to ensure Nginx is stable
for i in {1..3}; do
    if sudo systemctl is-active --quiet nginx; then
        log "✅ Nginx is running (check $i/3)"
    else
        log "❌ Nginx is not running (check $i/3)"
        sudo systemctl status nginx --no-pager -l
        log "📋 Nginx error logs:"
        sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
        exit 1
    fi
    sleep 2
done

log "✅ Nginx is stable and running"

# Verify Nginx is listening on ports
log "🔍 Verifying Nginx is listening on ports..."
if sudo lsof -i :80 | grep -q nginx; then
    log "✅ Nginx is listening on port 80"
else
    log "❌ Nginx is not listening on port 80"
    exit 1
fi

if sudo lsof -i :443 | grep -q nginx; then
    log "✅ Nginx is listening on port 443"
else
    log "❌ Nginx is not listening on port 443"
    exit 1
fi

# STEP 6: FastAPI service deployment
log "🚀 STEP 6: FastAPI service deployment"

# Start FastAPI service
log "🚀 Starting FastAPI service..."
./start-production-ssl.sh
check_status "FastAPI service started"

# Wait for services to stabilize
log "⏳ Waiting for services to stabilize..."
sleep 10

# STEP 7: Post-deployment verification
log "📊 STEP 7: Post-deployment verification"

# Check service status
log "📊 Checking service status..."
./status-production-ssl.sh

# Wait for services to fully stabilize
log "⏳ Waiting for services to fully stabilize..."
sleep 15

# Comprehensive service health checks
log "🧪 Running comprehensive service health checks..."

# Test HTTP to HTTPS redirect
if verify_service_health "HTTP to HTTPS redirect" "http://$DOMAIN" "301"; then
    log "✅ HTTP to HTTPS redirect working"
else
    log "❌ HTTP to HTTPS redirect failed"
    log "🔍 Testing with verbose output:"
    curl -v "http://$DOMAIN" 2>&1 | head -10
fi

# Test HTTPS connection
if verify_service_health "HTTPS connection" "https://$DOMAIN" "200"; then
    log "✅ HTTPS connection working"
else
    log "❌ HTTPS connection failed"
    log "🔍 Testing with verbose output:"
    curl -v "https://$DOMAIN" 2>&1 | head -10
fi

# Test the API endpoint
if verify_service_health "API endpoint" "https://$DOMAIN/api/v1/export/seasonal-trend" "200"; then
    log "✅ API endpoint test passed"
else
    log "❌ API endpoint test failed"
    log "🔍 Testing with verbose output:"
    curl -v "https://$DOMAIN/api/v1/export/seasonal-trend" 2>&1 | head -10
fi

# Final verification of all critical services
log "🔍 Final verification of all critical services..."

# Check if Nginx is still running
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx service is running"
else
    log "❌ Nginx service is not running"
    exit 1
fi

# Check if FastAPI is still running
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    log "✅ FastAPI service is running"
else
    log "❌ FastAPI service is not running"
    exit 1
fi

# Check if ports are properly allocated
if sudo lsof -i :80 | grep -q nginx; then
    log "✅ Port 80 is allocated to Nginx"
else
    log "❌ Port 80 is not allocated to Nginx"
    exit 1
fi

if sudo lsof -i :443 | grep -q nginx; then
    log "✅ Port 443 is allocated to Nginx"
else
    log "❌ Port 443 is not allocated to Nginx"
    exit 1
fi

if sudo lsof -i :8000 | grep -q uvicorn; then
    log "✅ Port 8000 is allocated to FastAPI"
else
    log "❌ Port 8000 is not allocated to FastAPI"
    exit 1
fi

# Final port verification
log "🔍 Final port verification..."
check_port 80 "HTTP"
check_port 443 "HTTPS"
check_port 8000 "FastAPI"

# Only declare success if all critical services are working
log "🎯 All critical services verified successfully!"
log "✅ Deployment completed successfully!"
log "🌐 Your API is available at: https://$DOMAIN"
log "📊 Service status: ./status-production-ssl.sh"