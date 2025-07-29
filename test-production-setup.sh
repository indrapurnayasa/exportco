#!/bin/bash

# Test Production HTTPS Setup
# This script tests if your production setup is working correctly

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

print_status "Testing Production HTTPS Setup..."

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")

echo ""
echo "=== PRODUCTION SETUP TEST ==="
echo "Server IP: $SERVER_IP"
echo ""

# Test 1: Check if SSL certificates exist
print_status "Test 1: Checking SSL certificates..."
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    print_success "SSL certificates found"
else
    print_error "SSL certificates not found"
    echo "Run: ./setup-production-https.sh"
    exit 1
fi

# Test 2: Check if service scripts exist
print_status "Test 2: Checking service scripts..."
if [ -f "start-production.sh" ] && [ -f "stop-production.sh" ] && [ -f "status-production.sh" ]; then
    print_success "Service scripts found"
else
    print_error "Service scripts not found"
    echo "Run: ./setup-production-https.sh"
    exit 1
fi

# Test 3: Check if services are running
print_status "Test 3: Checking if services are running..."

HTTP_RUNNING=false
HTTPS_RUNNING=false

if pgrep -f "uvicorn.*127.0.0.1:8000" > /dev/null; then
    HTTP_RUNNING=true
fi

if pgrep -f "uvicorn.*0.0.0.0:8443" > /dev/null; then
    HTTPS_RUNNING=true
fi

if [ "$HTTP_RUNNING" = true ]; then
    print_success "HTTP service is running"
else
    print_warning "HTTP service is not running"
fi

if [ "$HTTPS_RUNNING" = true ]; then
    print_success "HTTPS service is running"
else
    print_warning "HTTPS service is not running"
fi

# Test 4: Test HTTP endpoint
print_status "Test 4: Testing HTTP endpoint..."
HTTP_RESPONSE=$(curl -s -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tail -c 4)
HTTP_BODY=$(echo "$HTTP_RESPONSE" | head -c -4)

if [ "$HTTP_STATUS" = "200" ]; then
    print_success "HTTP endpoint working: $HTTP_BODY"
else
    print_error "HTTP endpoint failed: Status $HTTP_STATUS"
fi

# Test 5: Test HTTPS endpoint
print_status "Test 5: Testing HTTPS endpoint..."
HTTPS_RESPONSE=$(curl -s -k -w "%{http_code}" https://$SERVER_IP:8432/health 2>/dev/null || echo "000")
HTTPS_STATUS=$(echo "$HTTPS_RESPONSE" | tail -c 4)
HTTPS_BODY=$(echo "$HTTPS_RESPONSE" | head -c -4)

if [ "$HTTPS_STATUS" = "200" ]; then
    print_success "HTTPS endpoint working: $HTTPS_BODY"
else
    print_error "HTTPS endpoint failed: Status $HTTPS_STATUS"
fi

# Test 6: Test API endpoint
print_status "Test 6: Testing API endpoint..."
API_RESPONSE=$(curl -s -k -w "%{http_code}" https://$SERVER_IP:8432/api/v1/export/seasonal-trend 2>/dev/null || echo "000")
API_STATUS=$(echo "$API_RESPONSE" | tail -c 4)
API_BODY=$(echo "$API_RESPONSE" | head -c -4)

if [ "$API_STATUS" = "200" ]; then
    print_success "API endpoint working: Status $API_STATUS"
else
    print_error "API endpoint failed: Status $API_STATUS"
fi

# Test 7: Check firewall
print_status "Test 7: Checking firewall..."
FIREWALL_STATUS=$(sudo ufw status 2>/dev/null | grep -E "(8432|8000)" || echo "Ports not found")

if echo "$FIREWALL_STATUS" | grep -q "8432\|8000"; then
    print_success "Firewall configured for required ports"
else
    print_warning "Firewall may not be configured for required ports"
fi

echo ""
echo "=== TEST RESULTS SUMMARY ==="

if [ "$HTTP_RUNNING" = true ] && [ "$HTTPS_RUNNING" = true ] && [ "$HTTP_STATUS" = "200" ] && [ "$HTTPS_STATUS" = "200" ]; then
    print_success "🎉 PRODUCTION SETUP IS WORKING CORRECTLY!"
    echo ""
    echo "=== YOUR PRODUCTION ENDPOINTS ==="
    echo "Health Check: https://$SERVER_IP:8432/health"
    echo "API Docs:     https://$SERVER_IP:8432/docs"
    echo "Seasonal Trend: https://$SERVER_IP:8432/api/v1/export/seasonal-trend"
    echo ""
    echo "=== FRONTEND CONFIGURATION ==="
    echo "Update your frontend to use:"
    echo "https://$SERVER_IP:8432/api/v1/export/seasonal-trend"
    echo ""
    echo "=== NEXT STEPS ==="
    echo "1. Accept the SSL certificate by visiting: https://$SERVER_IP:8432/health"
    echo "2. Update your frontend API calls to use HTTPS"
    echo "3. Test your frontend application"
    echo ""
else
    print_error "❌ PRODUCTION SETUP HAS ISSUES"
    echo ""
    echo "=== TROUBLESHOOTING ==="
    if [ "$HTTP_RUNNING" = false ] || [ "$HTTPS_RUNNING" = false ]; then
        echo "1. Start services: ./start-production.sh"
    fi
    if [ "$HTTP_STATUS" != "200" ] || [ "$HTTPS_STATUS" != "200" ]; then
        echo "2. Check logs: tail -f logs/uvicorn-*.log"
    fi
    echo "3. Check database connection"
    echo "4. Verify firewall settings"
    echo ""
fi

echo "=== TESTING COMMANDS ==="
echo "Test HTTP:   curl http://127.0.0.1:8000/health"
echo "Test HTTPS:  curl -k https://$SERVER_IP:8432/health"
echo "Test API:    curl -k https://$SERVER_IP:8432/api/v1/export/seasonal-trend"
echo ""