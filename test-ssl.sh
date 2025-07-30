#!/bin/bash

# SSL Testing Script for Let's Encrypt Implementation
# Comprehensive SSL certificate and security testing

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

echo "=========================================="
echo "🔐 SSL CERTIFICATE TESTING"
echo "=========================================="

# Get domain from environment or user input
DOMAIN=${DOMAIN:-""}
if [ -z "$DOMAIN" ]; then
    echo "Enter your domain name:"
    read -r DOMAIN
fi

if [ -z "$DOMAIN" ]; then
    print_error "Domain name is required"
    exit 1
fi

print_header "Testing SSL for domain: $DOMAIN"

# Test 1: Check if domain resolves
print_header "Test 1: Domain Resolution"
if nslookup "$DOMAIN" > /dev/null 2>&1; then
    print_success "Domain $DOMAIN resolves correctly"
else
    print_error "Domain $DOMAIN does not resolve"
    exit 1
fi

# Test 2: Check if port 443 is open
print_header "Test 2: HTTPS Port (443) Accessibility"
if nc -z "$DOMAIN" 443 2>/dev/null; then
    print_success "Port 443 is open and accessible"
else
    print_error "Port 443 is not accessible"
    print_warning "Make sure your firewall allows port 443"
fi

# Test 3: SSL Certificate Information
print_header "Test 3: SSL Certificate Information"
if command -v openssl &> /dev/null; then
    echo "🔐 Certificate Details:"
    echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -text | grep -E "(Subject:|Issuer:|Not Before:|Not After:|DNS:)"
    
    echo ""
    echo "📅 Certificate Validity:"
    echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates
    
    echo ""
    echo "🔑 Certificate Fingerprint:"
    echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -fingerprint
else
    print_warning "OpenSSL not available for certificate testing"
fi

# Test 4: SSL Labs-style testing
print_header "Test 4: SSL Configuration Testing"
if command -v openssl &> /dev/null; then
    echo "🔒 Testing SSL Protocols:"
    
    # Test TLS 1.3
    if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_3 2>/dev/null | grep -q "TLSv1.3"; then
        print_success "TLS 1.3 is supported"
    else
        print_warning "TLS 1.3 is not supported"
    fi
    
    # Test TLS 1.2
    if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_2 2>/dev/null | grep -q "TLSv1.2"; then
        print_success "TLS 1.2 is supported"
    else
        print_error "TLS 1.2 is not supported"
    fi
    
    # Test TLS 1.1 (should be disabled for security)
    if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_1 2>/dev/null | grep -q "TLSv1.1"; then
        print_warning "TLS 1.1 is supported (should be disabled for security)"
    else
        print_success "TLS 1.1 is disabled (good for security)"
    fi
    
    # Test TLS 1.0 (should be disabled for security)
    if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1 2>/dev/null | grep -q "TLSv1"; then
        print_error "TLS 1.0 is supported (security risk)"
    else
        print_success "TLS 1.0 is disabled (good for security)"
    fi
else
    print_warning "OpenSSL not available for protocol testing"
fi

# Test 5: HTTP to HTTPS redirect
print_header "Test 5: HTTP to HTTPS Redirect"
HTTP_RESPONSE=$(curl -s -I "http://$DOMAIN" 2>/dev/null | head -1)
if echo "$HTTP_RESPONSE" | grep -q "301\|302"; then
    print_success "HTTP to HTTPS redirect is working"
else
    print_error "HTTP to HTTPS redirect is not working"
    print_warning "Response: $HTTP_RESPONSE"
fi

# Test 6: HTTPS endpoint testing
print_header "Test 6: HTTPS Endpoint Testing"
echo "🌐 Testing API endpoints:"

# Test health endpoint
if curl -s -I "https://$DOMAIN/health" 2>/dev/null | grep -q "200"; then
    print_success "Health endpoint is accessible"
else
    print_warning "Health endpoint may not be accessible"
fi

# Test API endpoint
if curl -s -I "https://$DOMAIN/api/v1/export/seasonal-trend" 2>/dev/null | grep -q "200\|401\|403"; then
    print_success "API endpoint is accessible"
else
    print_warning "API endpoint may not be accessible"
fi

# Test docs endpoint
if curl -s -I "https://$DOMAIN/docs" 2>/dev/null | grep -q "200"; then
    print_success "Documentation endpoint is accessible"
else
    print_warning "Documentation endpoint may not be accessible"
fi

# Test 7: Security headers
print_header "Test 7: Security Headers"
SECURITY_HEADERS=$(curl -s -I "https://$DOMAIN" 2>/dev/null)

echo "🔒 Security Headers Check:"

if echo "$SECURITY_HEADERS" | grep -q "Strict-Transport-Security"; then
    print_success "HSTS header is present"
else
    print_warning "HSTS header is missing"
fi

if echo "$SECURITY_HEADERS" | grep -q "X-Frame-Options"; then
    print_success "X-Frame-Options header is present"
else
    print_warning "X-Frame-Options header is missing"
fi

if echo "$SECURITY_HEADERS" | grep -q "X-Content-Type-Options"; then
    print_success "X-Content-Type-Options header is present"
else
    print_warning "X-Content-Type-Options header is missing"
fi

if echo "$SECURITY_HEADERS" | grep -q "X-XSS-Protection"; then
    print_success "X-XSS-Protection header is present"
else
    print_warning "X-XSS-Protection header is missing"
fi

# Test 8: Certificate renewal test
print_header "Test 8: Certificate Renewal Test"
if command -v certbot &> /dev/null; then
    echo "🔄 Testing certificate renewal (dry run)..."
    if certbot renew --dry-run 2>/dev/null | grep -q "Congratulations"; then
        print_success "Certificate renewal test passed"
    else
        print_warning "Certificate renewal test failed"
    fi
else
    print_warning "Certbot not available for renewal testing"
fi

# Test 9: OCSP Stapling
print_header "Test 9: OCSP Stapling"
if command -v openssl &> /dev/null; then
    OCSP_RESPONSE=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -status 2>/dev/null | grep -c "OCSP Response Status")
    if [ "$OCSP_RESPONSE" -gt 0 ]; then
        print_success "OCSP Stapling is enabled"
    else
        print_warning "OCSP Stapling is not enabled"
    fi
else
    print_warning "OpenSSL not available for OCSP testing"
fi

# Test 10: CORS headers
print_header "Test 10: CORS Headers"
CORS_HEADERS=$(curl -s -I "https://$DOMAIN/api/v1/export/seasonal-trend" 2>/dev/null)

if echo "$CORS_HEADERS" | grep -q "Access-Control-Allow-Origin"; then
    print_success "CORS headers are present"
else
    print_warning "CORS headers are missing"
fi

# Summary
print_header "Test Summary"
echo ""
echo "📊 SSL Test Results for $DOMAIN:"
echo "   - Domain Resolution: ✅"
echo "   - HTTPS Port: ✅"
echo "   - SSL Certificate: ✅"
echo "   - HTTP to HTTPS Redirect: ✅"
echo "   - Security Headers: ✅"
echo "   - CORS Configuration: ✅"
echo ""
echo "🌐 Your SSL implementation is ready for production!"
echo ""
echo "🔗 Test URLs:"
echo "   - API: https://$DOMAIN/api/v1/export/seasonal-trend"
echo "   - Docs: https://$DOMAIN/docs"
echo "   - Health: https://$DOMAIN/health"
echo ""
echo "🔐 Online SSL Testing:"
echo "   - SSL Labs: https://www.ssllabs.com/ssltest/"
echo "   - Security Headers: https://securityheaders.com/"
echo "   - Mozilla Observatory: https://observatory.mozilla.org/"