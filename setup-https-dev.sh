#!/bin/bash

# Development HTTPS Setup Script
# This script sets up HTTPS using self-signed certificates for development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

print_status "Setting up HTTPS for development..."

# Step 1: Create SSL directory
print_status "Step 1: Creating SSL directory..."
mkdir -p ssl
cd ssl

# Step 2: Generate self-signed certificate
print_status "Step 2: Generating self-signed certificate..."
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

print_success "Self-signed certificate created"

# Step 3: Update FastAPI to use SSL
print_status "Step 3: Creating HTTPS startup script..."

cd ..

# Create HTTPS startup script
cat > start-https.sh << 'EOF'
#!/bin/bash

# HTTPS Startup Script for Hackathon Service
# This script starts the service with SSL certificates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1"
}

print_status "Starting Hackathon Service with HTTPS..."

# Check if SSL certificates exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    print_error "SSL certificates not found. Run setup-https-dev.sh first."
    exit 1
fi

# Activate conda environment
if command -v conda &> /dev/null && conda env list | grep -q "hackathon-env"; then
    print_status "Activating conda environment: hackathon-env"
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate hackathon-env
else
    print_warning "Conda environment not found, using system Python"
fi

# Create log directory
mkdir -p logs

# Start the service with SSL
print_status "Starting server with HTTPS on 0.0.0.0:8443..."

nohup uvicorn app.main:app \
    --host "0.0.0.0" \
    --port 8443 \
    --ssl-certfile ssl/cert.pem \
    --ssl-keyfile ssl/key.pem \
    --workers 4 \
    --log-level info \
    --access-log \
    > logs/uvicorn-https.log 2>&1 &

local pid=$!
echo "$pid" > hackathon_service_https.pid

# Wait a moment for the service to start
sleep 3

# Check if service started successfully
if ps -p "$pid" > /dev/null 2>&1; then
    print_success "HTTPS Service started successfully (PID: $pid)"
    print_success "Server running on https://0.0.0.0:8443"
    print_success "Health check: https://0.0.0.0:8443/health"
    print_success "API docs: https://0.0.0.0:8443/docs"
    print_warning "Note: This uses a self-signed certificate. Browsers will show a security warning."
    print_status "To test: curl -k https://localhost:8443/health"
else
    print_error "Failed to start HTTPS service"
    rm -f hackathon_service_https.pid
    exit 1
fi
EOF

chmod +x start-https.sh

# Create stop script for HTTPS
cat > stop-https.sh << 'EOF'
#!/bin/bash

# Stop HTTPS Service Script

PID_FILE="hackathon_service_https.pid"

if [ -f "$PID_FILE" ]; then
    local pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Stopping HTTPS service (PID: $pid)..."
        kill -TERM "$pid"
        rm -f "$PID_FILE"
        echo "HTTPS service stopped"
    else
        echo "HTTPS service not running"
        rm -f "$PID_FILE"
    fi
else
    echo "PID file not found"
fi
EOF

chmod +x stop-https.sh

print_success "HTTPS setup completed!"
echo ""
echo "=== HTTPS ENDPOINTS ==="
echo "Health Check: https://localhost:8443/health"
echo "API Docs: https://localhost:8443/docs"
echo "Main API: https://localhost:8443/"
echo ""
echo "=== USAGE ==="
echo "Start HTTPS service: ./start-https.sh"
echo "Stop HTTPS service: ./stop-https.sh"
echo ""
echo "=== TESTING ==="
echo "Test with curl (ignore SSL warning):"
echo "curl -k https://localhost:8443/health"
echo "curl -k https://localhost:8443/docs"
echo ""
echo "=== BROWSER ACCESS ==="
echo "Open in browser: https://localhost:8443/docs"
echo "Note: Browser will show security warning for self-signed certificate"
echo "Click 'Advanced' and 'Proceed to localhost' to continue"
echo "" 