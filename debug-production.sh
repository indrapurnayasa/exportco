#!/bin/bash

# Debug Production Services
# This script provides detailed logging and error analysis

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
echo "🔍 PRODUCTION SERVICE DEBUGGING"
echo "=========================================="
echo ""

# Function to check service status
check_service_status() {
    echo "=== SERVICE STATUS CHECK ==="
    echo ""
    
    # Check HTTP service
    echo "🔍 HTTP Service (Port 8000):"
    HTTP_PID=$(pgrep -f "uvicorn.*127.0.0.1:8000" 2>/dev/null || echo "")
    if [ -n "$HTTP_PID" ]; then
        print_success "HTTP Service is running (PID: $HTTP_PID)"
    else
        print_error "HTTP Service is NOT running"
    fi
    
    # Check HTTPS service
    echo "🔍 HTTPS Service (Port 8432):"
    HTTPS_PID=$(pgrep -f "uvicorn.*0.0.0.0:8432" 2>/dev/null || echo "")
    if [ -n "$HTTPS_PID" ]; then
        print_success "HTTPS Service is running (PID: $HTTPS_PID)"
    else
        print_error "HTTPS Service is NOT running"
    fi
    
    echo ""
}

# Function to check port usage
check_port_usage() {
    echo "=== PORT USAGE CHECK ==="
    echo ""
    
    echo "🔍 Port 8000 (HTTP):"
    PORT_8000=$(sudo lsof -i :8000 2>/dev/null || echo "No process found")
    if echo "$PORT_8000" | grep -q "LISTEN"; then
        print_success "Port 8000 is in use"
        echo "$PORT_8000"
    else
        print_warning "Port 8000 is free"
    fi
    
    echo ""
    echo "🔍 Port 8432 (HTTPS):"
    PORT_8432=$(sudo lsof -i :8432 2>/dev/null || echo "No process found")
    if echo "$PORT_8432" | grep -q "LISTEN"; then
        print_success "Port 8432 is in use"
        echo "$PORT_8432"
    else
        print_warning "Port 8432 is free"
    fi
    
    echo ""
}

# Function to check logs
check_logs() {
    echo "=== LOG ANALYSIS ==="
    echo ""
    
    echo "🔍 HTTP Service Logs (last 10 lines):"
    if [ -f "logs/uvicorn-http.log" ]; then
        tail -10 logs/uvicorn-http.log
    else
        print_error "HTTP log file not found"
    fi
    
    echo ""
    echo "🔍 HTTPS Service Logs (last 10 lines):"
    if [ -f "logs/uvicorn-https.log" ]; then
        tail -10 logs/uvicorn-https.log
    else
        print_error "HTTPS log file not found"
    fi
    
    echo ""
}

# Function to test endpoints
test_endpoints() {
    echo "=== ENDPOINT TESTING ==="
    echo ""
    
    echo "🔍 Testing HTTP endpoint (127.0.0.1:8000/health):"
    HTTP_RESPONSE=$(curl -s -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
    HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tail -c 4)
    HTTP_BODY=$(echo "$HTTP_RESPONSE" | head -c -4)
    
    if [ "$HTTP_STATUS" = "200" ]; then
        print_success "HTTP endpoint working: $HTTP_BODY"
    else
        print_error "HTTP endpoint failed: Status $HTTP_STATUS"
    fi
    
    echo ""
    echo "🔍 Testing HTTPS endpoint (127.0.0.1:8432/health):"
    HTTPS_RESPONSE=$(curl -s -k -w "%{http_code}" https://127.0.0.1:8432/health 2>/dev/null || echo "000")
    HTTPS_STATUS=$(echo "$HTTPS_RESPONSE" | tail -c 4)
    HTTPS_BODY=$(echo "$HTTPS_RESPONSE" | head -c -4)
    
    if [ "$HTTPS_STATUS" = "200" ]; then
        print_success "HTTPS endpoint working: $HTTPS_BODY"
    else
        print_error "HTTPS endpoint failed: Status $HTTPS_STATUS"
    fi
    
    echo ""
}

# Function to check environment
check_environment() {
    echo "=== ENVIRONMENT CHECK ==="
    echo ""
    
    echo "🔍 Conda environment:"
    if conda env list | grep -q "hackathon-env"; then
        print_success "Conda environment 'hackathon-env' exists"
    else
        print_error "Conda environment 'hackathon-env' not found"
    fi
    
    echo ""
    echo "🔍 SSL certificates:"
    if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
        print_success "SSL certificates found"
    else
        print_error "SSL certificates missing"
    fi
    
    echo ""
    echo "🔍 Database connection:"
    DB_TEST=$(python3 -c "import psycopg2; conn = psycopg2.connect('postgresql://maverick:Hackathon2025@101.50.2.59:5432/hackathondb'); print('OK'); conn.close()" 2>&1 || echo "FAILED")
    if [ "$DB_TEST" = "OK" ]; then
        print_success "Database connection working"
    else
        print_error "Database connection failed: $DB_TEST"
    fi
    
    echo ""
}

# Function to show detailed process info
show_process_details() {
    echo "=== DETAILED PROCESS INFO ==="
    echo ""
    
    echo "🔍 All uvicorn processes:"
    ps aux | grep uvicorn | grep -v grep || echo "No uvicorn processes found"
    
    echo ""
    echo "🔍 Process tree:"
    pstree -p $(pgrep -f "uvicorn.*app.main:app" 2>/dev/null | head -1) 2>/dev/null || echo "No process tree available"
    
    echo ""
}

# Function to check PID files
check_pid_files() {
    echo "=== PID FILE CHECK ==="
    echo ""
    
    echo "🔍 HTTP PID file:"
    if [ -f "logs/uvicorn-http.pid" ]; then
        HTTP_PID_FILE=$(cat logs/uvicorn-http.pid 2>/dev/null || echo "empty")
        echo "PID file content: $HTTP_PID_FILE"
        if kill -0 "$HTTP_PID_FILE" 2>/dev/null; then
            print_success "HTTP PID file is valid"
        else
            print_error "HTTP PID file is stale"
        fi
    else
        print_error "HTTP PID file not found"
    fi
    
    echo ""
    echo "🔍 HTTPS PID file:"
    if [ -f "logs/uvicorn-https.pid" ]; then
        HTTPS_PID_FILE=$(cat logs/uvicorn-https.pid 2>/dev/null || echo "empty")
        echo "PID file content: $HTTPS_PID_FILE"
        if kill -0 "$HTTPS_PID_FILE" 2>/dev/null; then
            print_success "HTTPS PID file is valid"
        else
            print_error "HTTPS PID file is stale"
        fi
    else
        print_error "HTTPS PID file not found"
    fi
    
    echo ""
}

# Main execution
echo "Starting comprehensive debugging..."
echo ""

# Run all checks
check_service_status
check_port_usage
check_logs
test_endpoints
check_environment
show_process_details
check_pid_files

echo "=========================================="
echo "📊 SUMMARY"
echo "=========================================="

# Count running services
HTTP_COUNT=$(pgrep -f "uvicorn.*127.0.0.1:8000" | wc -l)
HTTPS_COUNT=$(pgrep -f "uvicorn.*0.0.0.0:8432" | wc -l)

echo "HTTP Services running: $HTTP_COUNT"
echo "HTTPS Services running: $HTTPS_COUNT"

if [ "$HTTP_COUNT" -gt 0 ] && [ "$HTTPS_COUNT" -gt 0 ]; then
    print_success "Both services appear to be running!"
    echo ""
    echo "🎯 Your endpoints should be:"
    echo "   HTTP:  http://127.0.0.1:8000/health"
    echo "   HTTPS: https://127.0.0.1:8432/health"
    echo "   External: https://$(curl -s ifconfig.me 2>/dev/null || echo "your-ip"):8432/health"
else
    print_error "Some services are not running properly"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "1. Check the logs above for error messages"
    echo "2. Verify conda environment is activated"
    echo "3. Check database connection"
    echo "4. Ensure SSL certificates exist"
    echo "5. Try restarting: ./stop-production.sh && ./start-production.sh"
fi

echo ""
echo "=========================================="