#!/bin/bash

# Cleanup Production Services
# This script kills all existing processes and frees up ports

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

echo "=========================================="
echo "🧹 CLEANING UP PRODUCTION SERVICES"
echo "=========================================="
echo ""

# Step 1: Show current processes
print_status "Step 1: Checking current processes..."
echo "Current uvicorn processes:"
ps aux | grep uvicorn | grep -v grep || echo "No uvicorn processes found"

echo ""
echo "Current port usage:"
sudo lsof -i :8000 2>/dev/null || echo "Port 8000 is free"
sudo lsof -i :8443 2>/dev/null || echo "Port 8443 is free"

# Step 2: Kill processes by PID files
print_status "Step 2: Killing processes by PID files..."

if [ -f "logs/uvicorn-http.pid" ]; then
    HTTP_PID=$(cat logs/uvicorn-http.pid 2>/dev/null || echo "")
    if [ -n "$HTTP_PID" ] && kill -0 "$HTTP_PID" 2>/dev/null; then
        print_status "Killing HTTP process (PID: $HTTP_PID)..."
        kill -9 "$HTTP_PID" 2>/dev/null || true
        print_success "HTTP process killed"
    else
        print_warning "HTTP PID file is stale or process not found"
    fi
    rm -f logs/uvicorn-http.pid
fi

if [ -f "logs/uvicorn-https.pid" ]; then
    HTTPS_PID=$(cat logs/uvicorn-https.pid 2>/dev/null || echo "")
    if [ -n "$HTTPS_PID" ] && kill -0 "$HTTPS_PID" 2>/dev/null; then
        print_status "Killing HTTPS process (PID: $HTTPS_PID)..."
        kill -9 "$HTTPS_PID" 2>/dev/null || true
        print_success "HTTPS process killed"
    else
        print_warning "HTTPS PID file is stale or process not found"
    fi
    rm -f logs/uvicorn-https.pid
fi

# Step 3: Kill all uvicorn processes
print_status "Step 3: Killing all uvicorn processes..."
pkill -f "uvicorn.*app.main:app" || true
sleep 2

# Step 4: Force kill by ports
print_status "Step 4: Force killing processes by ports..."

# Kill process on port 8000
PORT_8000_PID=$(sudo lsof -ti :8000 2>/dev/null || echo "")
if [ -n "$PORT_8000_PID" ]; then
    print_status "Killing process on port 8000 (PID: $PORT_8000_PID)..."
    sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
    print_success "Port 8000 freed"
else
    print_success "Port 8000 is already free"
fi

# Kill process on port 8443
PORT_8443_PID=$(sudo lsof -ti :8443 2>/dev/null || echo "")
if [ -n "$PORT_8443_PID" ]; then
    print_status "Killing process on port 8443 (PID: $PORT_8443_PID)..."
    sudo kill -9 "$PORT_8443_PID" 2>/dev/null || true
    print_success "Port 8443 freed"
else
    print_success "Port 8443 is already free"
fi

# Step 5: Wait and verify
print_status "Step 5: Waiting for cleanup..."
sleep 3

# Step 6: Verify cleanup
print_status "Step 6: Verifying cleanup..."

echo "Remaining uvicorn processes:"
ps aux | grep uvicorn | grep -v grep || echo "No uvicorn processes found"

echo ""
echo "Port status:"
echo "Port 8000:"
sudo lsof -i :8000 2>/dev/null || echo "✅ Port 8000 is free"

echo "Port 8443:"
sudo lsof -i :8443 2>/dev/null || echo "✅ Port 8443 is free"

# Step 7: Clean up log files
print_status "Step 7: Cleaning up log files..."
rm -f logs/uvicorn-*.pid
print_success "PID files cleaned"

echo ""
echo "=========================================="
echo "📊 CLEANUP SUMMARY"
echo "=========================================="

# Final check
REMAINING_PROCESSES=$(ps aux | grep uvicorn | grep -v grep | wc -l)
PORT_8000_FREE=$(sudo lsof -i :8000 2>/dev/null | wc -l)
PORT_8443_FREE=$(sudo lsof -i :8443 2>/dev/null | wc -l)

if [ "$REMAINING_PROCESSES" -eq 0 ] && [ "$PORT_8000_FREE" -eq 0 ] && [ "$PORT_8443_FREE" -eq 0 ]; then
    print_success "🎉 CLEANUP COMPLETED SUCCESSFULLY!"
    echo ""
    echo "✅ All uvicorn processes killed"
    echo "✅ Port 8000 is free"
    echo "✅ Port 8443 is free"
    echo "✅ PID files cleaned"
    echo ""
    echo "🚀 Ready to start services: ./start-production-debug.sh"
else
    print_warning "⚠️  Some cleanup may be incomplete"
    echo ""
    echo "Remaining processes: $REMAINING_PROCESSES"
    echo "Port 8000 in use: $([ $PORT_8000_FREE -gt 0 ] && echo "Yes" || echo "No")"
    echo "Port 8443 in use: $([ $PORT_8443_FREE -gt 0 ] && echo "Yes" || echo "No")"
    echo ""
    echo "🔧 Manual cleanup may be needed"
fi

echo "=========================================="