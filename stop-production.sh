#!/bin/bash

# Stop Hackathon Service

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

print_status "Stopping Hackathon Service..."

# Stop HTTP service
if [ -f "$PID_FILE_HTTP" ]; then
    PID=$(cat "$PID_FILE_HTTP")
    if kill -0 "$PID" 2>/dev/null; then
        print_status "Stopping HTTP service (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            print_warning "HTTP service still running, force killing..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE_HTTP"
        print_success "HTTP service stopped"
    else
        print_warning "HTTP service PID not found"
        rm -f "$PID_FILE_HTTP"
    fi
fi

# Stop HTTPS service
if [ -f "$PID_FILE_HTTPS" ]; then
    PID=$(cat "$PID_FILE_HTTPS")
    if kill -0 "$PID" 2>/dev/null; then
        print_status "Stopping HTTPS service (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            print_warning "HTTPS service still running, force killing..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE_HTTPS"
        print_success "HTTPS service stopped"
    else
        print_warning "HTTPS service PID not found"
        rm -f "$PID_FILE_HTTPS"
    fi
fi

# Kill any remaining uvicorn processes
pkill -f "uvicorn.*app.main:app" || true
print_success "All services stopped"
