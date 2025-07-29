#!/bin/bash

# Check Hackathon Service Status

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

PID_FILE_HTTP="logs/uvicorn-http.pid"
PID_FILE_HTTPS="logs/uvicorn-https.pid"

print_status "Checking Hackathon Service Status..."

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")

echo ""
echo "=== SERVICE STATUS ==="

# Check HTTP service
if [ -f "$PID_FILE_HTTP" ]; then
    PID=$(cat "$PID_FILE_HTTP")
    if kill -0 "$PID" 2>/dev/null; then
        print_success "HTTP Service: RUNNING (PID: $PID, Port: 8000)"
    else
        print_error "HTTP Service: NOT RUNNING (stale PID file)"
        rm -f "$PID_FILE_HTTP"
    fi
else
    if pgrep -f "uvicorn.*127.0.0.1:8000" > /dev/null; then
        print_warning "HTTP Service: RUNNING (no PID file)"
    else
        print_error "HTTP Service: NOT RUNNING"
    fi
fi

# Check HTTPS service
if [ -f "$PID_FILE_HTTPS" ]; then
    PID=$(cat "$PID_FILE_HTTPS")
    if kill -0 "$PID" 2>/dev/null; then
        print_success "HTTPS Service: RUNNING (PID: $PID, Port: 8443)"
    else
        print_error "HTTPS Service: NOT RUNNING (stale PID file)"
        rm -f "$PID_FILE_HTTPS"
    fi
else
    if pgrep -f "uvicorn.*0.0.0.0:8443" > /dev/null; then
        print_warning "HTTPS Service: RUNNING (no PID file)"
    else
        print_error "HTTPS Service: NOT RUNNING"
    fi
fi

echo ""
echo "=== ENDPOINTS ==="
echo "HTTP (Internal):  http://127.0.0.1:8000/health"
echo "HTTPS (External): https://$SERVER_IP:8443/health"
echo "API Docs:         https://$SERVER_IP:8443/docs"
echo ""

echo "=== TESTING COMMANDS ==="
echo "Test HTTP:   curl http://127.0.0.1:8000/health"
echo "Test HTTPS:  curl -k https://$SERVER_IP:8443/health"
echo ""

echo "=== LOG FILES ==="
echo "HTTP Logs:   tail -f logs/uvicorn-http.log"
echo "HTTPS Logs:  tail -f logs/uvicorn-https.log"
echo ""
