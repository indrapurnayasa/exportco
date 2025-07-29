#!/bin/bash

# Start Production Services with Detailed Logging
# This script provides comprehensive logging and error analysis

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

# Configuration
HOST="0.0.0.0"
HTTP_PORT="8000"
HTTPS_PORT="8443"  # Back to original port
WORKERS="4"
LOG_DIR="logs"
PID_FILE_HTTP="logs/uvicorn-http.pid"
PID_FILE_HTTPS="logs/uvicorn-https.pid"

# Create logs directory
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "🚀 STARTING PRODUCTION SERVICES"
echo "=========================================="
echo ""

print_status "Starting Hackathon Service in Production Mode..."

# Step 1: Check environment
print_status "Step 1: Checking environment..."

# Check conda environment
if command -v conda &> /dev/null; then
    print_status "Conda is available"
    if conda env list | grep -q "hackathon-env"; then
        print_success "Conda environment 'hackathon-env' exists"
    else
        print_error "Conda environment 'hackathon-env' not found"
        print_status "Creating conda environment..."
        conda create -n hackathon-env python=3.10 -y
    fi
else
    print_error "Conda not found"
    exit 1
fi

# Activate conda environment
print_status "Activating conda environment: hackathon-env"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate hackathon-env

# Step 2: Check SSL certificates
print_status "Step 2: Checking SSL certificates..."
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    print_success "SSL certificates found"
else
    print_error "SSL certificates not found"
    print_status "Running setup to create SSL certificates..."
    ./setup-production-https.sh
fi

# Step 3: Check database connection
print_status "Step 3: Testing database connection..."
DB_TEST=$(python3 -c "import psycopg2; conn = psycopg2.connect('postgresql://maverick:Hackathon2025@101.50.2.59:5432/hackathondb'); print('OK'); conn.close()" 2>&1 || echo "FAILED")
if [ "$DB_TEST" = "OK" ]; then
    print_success "Database connection working"
else
    print_error "Database connection failed: $DB_TEST"
    print_warning "Continuing anyway..."
fi

# Step 4: Kill any existing processes
print_status "Step 4: Cleaning up existing processes..."
pkill -f "uvicorn.*app.main:app" || true
sleep 2

# Step 5: Start HTTP service
print_status "Step 5: Starting HTTP service on port $HTTP_PORT..."
nohup uvicorn app.main:app \
    --host "127.0.0.1" \
    --port "$HTTP_PORT" \
    --workers "$WORKERS" \
    --log-level info \
    --access-log \
    > "$LOG_DIR/uvicorn-http.log" 2>&1 &

HTTP_PID=$!
echo $HTTP_PID > "$PID_FILE_HTTP"
print_success "HTTP service started with PID: $HTTP_PID"

# Step 6: Start HTTPS service
print_status "Step 6: Starting HTTPS service on port $HTTPS_PORT..."
nohup uvicorn app.main:app \
    --host "$HOST" \
    --port "$HTTPS_PORT" \
    --workers "$WORKERS" \
    --ssl-certfile ssl/cert.pem \
    --ssl-keyfile ssl/key.pem \
    --log-level info \
    --access-log \
    > "$LOG_DIR/uvicorn-https.log" 2>&1 &

HTTPS_PID=$!
echo $HTTPS_PID > "$PID_FILE_HTTPS"
print_success "HTTPS service started with PID: $HTTPS_PID"

# Step 7: Wait and check
print_status "Step 7: Waiting for services to start..."
sleep 5

# Step 8: Verify services
print_status "Step 8: Verifying services..."

# Check if processes are running
HTTP_RUNNING=false
HTTPS_RUNNING=false

if kill -0 "$HTTP_PID" 2>/dev/null; then
    HTTP_RUNNING=true
    print_success "HTTP process is running (PID: $HTTP_PID)"
else
    print_error "HTTP process failed to start"
fi

if kill -0 "$HTTPS_PID" 2>/dev/null; then
    HTTPS_RUNNING=true
    print_success "HTTPS process is running (PID: $HTTPS_PID)"
else
    print_error "HTTPS process failed to start"
fi

# Check port usage
print_status "Step 9: Checking port usage..."
PORT_8000=$(sudo lsof -i :8000 2>/dev/null || echo "No process found")
PORT_8443=$(sudo lsof -i :8443 2>/dev/null || echo "No process found")

if echo "$PORT_8000" | grep -q "LISTEN"; then
    print_success "Port 8000 is listening"
else
    print_error "Port 8000 is not listening"
fi

if echo "$PORT_8443" | grep -q "LISTEN"; then
    print_success "Port 8443 is listening"
else
    print_error "Port 8443 is not listening"
fi

# Step 10: Test endpoints
print_status "Step 10: Testing endpoints..."

# Test HTTP endpoint
HTTP_RESPONSE=$(curl -s -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tail -c 4)
HTTP_BODY=$(echo "$HTTP_RESPONSE" | head -c -4)

if [ "$HTTP_STATUS" = "200" ]; then
    print_success "HTTP endpoint working: $HTTP_BODY"
else
    print_error "HTTP endpoint failed: Status $HTTP_STATUS"
fi

# Test HTTPS endpoint
HTTPS_RESPONSE=$(curl -s -k -w "%{http_code}" https://127.0.0.1:8443/health 2>/dev/null || echo "000")
HTTPS_STATUS=$(echo "$HTTPS_RESPONSE" | tail -c 4)
HTTPS_BODY=$(echo "$HTTPS_RESPONSE" | head -c -4)

if [ "$HTTPS_STATUS" = "200" ]; then
    print_success "HTTPS endpoint working: $HTTPS_BODY"
else
    print_error "HTTPS endpoint failed: Status $HTTPS_STATUS"
fi

# Step 11: Show logs
print_status "Step 11: Recent log entries..."

echo ""
echo "🔍 HTTP Service Logs (last 5 lines):"
if [ -f "logs/uvicorn-http.log" ]; then
    tail -5 logs/uvicorn-http.log
else
    print_error "HTTP log file not found"
fi

echo ""
echo "🔍 HTTPS Service Logs (last 5 lines):"
if [ -f "logs/uvicorn-https.log" ]; then
    tail -5 logs/uvicorn-https.log
else
    print_error "HTTPS log file not found"
fi

# Step 12: Summary
echo ""
echo "=========================================="
echo "📊 STARTUP SUMMARY"
echo "=========================================="

if [ "$HTTP_RUNNING" = true ] && [ "$HTTPS_RUNNING" = true ] && [ "$HTTP_STATUS" = "200" ] && [ "$HTTPS_STATUS" = "200" ]; then
    print_success "🎉 ALL SERVICES STARTED SUCCESSFULLY!"
    echo ""
    echo "=== YOUR PRODUCTION ENDPOINTS ==="
    echo "HTTP (Internal):  http://127.0.0.1:$HTTP_PORT/health"
    echo "HTTPS (External): https://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip"):$HTTPS_PORT/health"
    echo "API Docs:         https://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip"):$HTTPS_PORT/docs"
    echo ""
    echo "=== FRONTEND CONFIGURATION ==="
    echo "Update your frontend to use:"
    echo "https://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip"):$HTTPS_PORT/api/v1/export/seasonal-trend"
    echo ""
    echo "=== IMPORTANT NOTES ==="
    echo "1. This uses a self-signed certificate"
    echo "2. Accept the certificate by visiting the health endpoint"
    echo "3. Use -k flag with curl for testing"
    echo "4. Both HTTP and HTTPS are running"
    echo "5. HTTPS port: $HTTPS_PORT"
    echo ""
else
    print_error "❌ SOME SERVICES FAILED TO START"
    echo ""
    echo "=== TROUBLESHOOTING ==="
    echo "1. Check logs: tail -f logs/uvicorn-*.log"
    echo "2. Check processes: ps aux | grep uvicorn"
    echo "3. Check ports: sudo lsof -i :8000 :8432"
    echo "4. Restart: ./stop-production.sh && ./start-production.sh"
    echo ""
fi

echo "=========================================="