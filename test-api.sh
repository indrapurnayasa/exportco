#!/bin/bash

# Test API Endpoints
# Simple script to test all production endpoints

echo "=========================================="
echo "🧪 TESTING PRODUCTION API ENDPOINTS"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🔍 Testing HTTP endpoints..."
echo ""

# Test HTTP health
echo "1. HTTP Health Check:"
HTTP_HEALTH=$(curl -s http://127.0.0.1:8000/health)
if [ "$HTTP_HEALTH" = '{"status":"healthy"}' ]; then
    print_success "HTTP Health: $HTTP_HEALTH"
else
    print_error "HTTP Health failed: $HTTP_HEALTH"
fi

echo ""
echo "🔍 Testing HTTPS endpoints..."
echo ""

# Test HTTPS health
echo "2. HTTPS Health Check:"
HTTPS_HEALTH=$(curl -s -k https://127.0.0.1:8443/health)
if [ "$HTTPS_HEALTH" = '{"status":"healthy"}' ]; then
    print_success "HTTPS Health: $HTTPS_HEALTH"
else
    print_error "HTTPS Health failed: $HTTPS_HEALTH"
fi

echo ""
echo "🔍 Testing API endpoints..."
echo ""

# Test seasonal trend API
echo "3. Seasonal Trend API:"
SEASONAL_RESPONSE=$(curl -s -k https://127.0.0.1:8443/api/v1/export/seasonal-trend)
if echo "$SEASONAL_RESPONSE" | grep -q '"data"'; then
    print_success "Seasonal Trend API working"
    echo "Response preview: $(echo "$SEASONAL_RESPONSE" | head -c 100)..."
else
    print_error "Seasonal Trend API failed: $(echo "$SEASONAL_RESPONSE" | head -c 100)"
fi

echo ""
echo "🔍 Testing external endpoints..."
echo ""

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")

# Test external HTTPS health
echo "4. External HTTPS Health Check:"
EXTERNAL_HEALTH=$(curl -s -k https://$SERVER_IP:8443/health)
if [ "$EXTERNAL_HEALTH" = '{"status":"healthy"}' ]; then
    print_success "External HTTPS Health: $EXTERNAL_HEALTH"
else
    print_error "External HTTPS Health failed: $EXTERNAL_HEALTH"
fi

echo ""
echo "=========================================="
echo "📊 TEST SUMMARY"
echo "=========================================="

# Count successful tests
SUCCESS_COUNT=0
if [ "$HTTP_HEALTH" = '{"status":"healthy"}' ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); fi
if [ "$HTTPS_HEALTH" = '{"status":"healthy"}' ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); fi
if echo "$SEASONAL_RESPONSE" | grep -q '"data"'; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); fi
if [ "$EXTERNAL_HEALTH" = '{"status":"healthy"}' ]; then SUCCESS_COUNT=$((SUCCESS_COUNT + 1)); fi

if [ "$SUCCESS_COUNT" -eq 4 ]; then
    print_success "🎉 ALL TESTS PASSED! Your production API is working perfectly!"
    echo ""
    echo "=== YOUR PRODUCTION ENDPOINTS ==="
    echo "HTTP (Internal):  http://127.0.0.1:8000/health"
    echo "HTTPS (Internal): https://127.0.0.1:8443/health"
    echo "HTTPS (External): https://$SERVER_IP:8443/health"
    echo "API Docs:         https://$SERVER_IP:8443/docs"
    echo "Seasonal Trend:   https://$SERVER_IP:8443/api/v1/export/seasonal-trend"
    echo ""
    echo "=== FRONTEND CONFIGURATION ==="
    echo "Update your frontend to use:"
    echo "https://$SERVER_IP:8443/api/v1/export/seasonal-trend"
    echo ""
else
    print_error "❌ Some tests failed ($SUCCESS_COUNT/4 passed)"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Check if services are running: ps aux | grep uvicorn"
    echo "2. Check logs: tail -f logs/uvicorn-*.log"
    echo "3. Check ports: sudo lsof -i :8000 :8443"
    echo "4. Restart services: ./cleanup-production.sh && ./start-production-debug.sh"
fi

echo "=========================================="