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

# Simple and reliable Nginx management
log "🌐 Managing Nginx service..."

# Stop Nginx first to ensure clean state
log "🛑 Stopping Nginx for clean restart..."
sudo systemctl stop nginx 2>/dev/null || true
sleep 2

# Enable Nginx to start on boot
log "🔧 Enabling Nginx service..."
sudo systemctl enable nginx
check_status "Nginx enabled"

# Start Nginx
log "🚀 Starting Nginx service..."
sudo systemctl start nginx
if [ $? -eq 0 ]; then
    log "✅ Nginx started successfully"
else
    log "❌ Nginx start failed, checking logs..."
    sudo journalctl -u nginx --no-pager -n 10
    log "📋 Nginx error logs:"
    sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
    exit 1
fi

# Wait for Nginx to fully start
log "⏳ Waiting for Nginx to fully start..."
sleep 5

# Verify Nginx is running
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx is running"
else
    log "❌ Nginx is not running after start"
    sudo systemctl status nginx --no-pager -l
    exit 1
fi

# Check if Nginx is listening on ports
log "🔍 Checking if Nginx is listening on ports..."
sleep 2

if sudo lsof -i :80 | grep -q nginx; then
    log "✅ Nginx is listening on port 80"
else
    log "❌ Nginx is not listening on port 80"
    log "📋 Checking Nginx process:"
    sudo lsof -i :80 || echo "Nothing listening on port 80"
    exit 1
fi

if sudo lsof -i :443 | grep -q nginx; then
    log "✅ Nginx is listening on port 443"
else
    log "❌ Nginx is not listening on port 443"
    log "📋 Checking Nginx process:"
    sudo lsof -i :443 || echo "Nothing listening on port 443"
    exit 1
fi

# STEP 6: FastAPI service deployment
log "🚀 STEP 6: FastAPI service deployment"

# Start FastAPI service directly (don't use start-production-ssl.sh as it kills ports)
log "🚀 Starting FastAPI service..."

# Check if conda is available and activate environment
if command -v conda &> /dev/null; then
    log "🐍 Activating conda environment..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate hackathon-env
else
    log "🐍 Conda not found, using system Python..."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start FastAPI service (HTTP only, Nginx handles HTTPS)
log "🚀 Starting FastAPI service on port 8000..."
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 > logs/uvicorn-ssl.log 2>&1 &

# Wait for service to start
sleep 5

# Check if service is running
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    log "✅ FastAPI service started successfully"
else
    log "❌ Failed to start FastAPI service"
    log "📋 Check logs: tail -f logs/uvicorn-ssl.log"
    exit 1
fi

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
sleep 10

# Simple health checks
log "🧪 Running simple health checks..."

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

# Simple connectivity test
log "🧪 Testing basic connectivity..."
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:80" | grep -q "301\|302"; then
    log "✅ Local HTTP redirect working"
else
    log "❌ Local HTTP redirect failed"
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