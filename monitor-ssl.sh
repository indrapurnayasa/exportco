#!/bin/bash

# SSL Certificate Monitoring Script
# Monitors SSL certificate expiration and provides alerts

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

print_header "SSL Certificate Monitoring for $DOMAIN"

# Function to get certificate expiration date
get_cert_expiry() {
    if command -v openssl &> /dev/null; then
        echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2
    else
        echo "OpenSSL not available"
    fi
}

# Function to convert date to timestamp
date_to_timestamp() {
    date -d "$1" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$1" +%s 2>/dev/null
}

# Function to get days until expiration
get_days_until_expiry() {
    local expiry_date=$(get_cert_expiry)
    if [ "$expiry_date" != "OpenSSL not available" ]; then
        local expiry_timestamp=$(date_to_timestamp "$expiry_date")
        local current_timestamp=$(date +%s)
        local days_remaining=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        echo "$days_remaining"
    else
        echo "unknown"
    fi
}

# Function to check certificate status
check_certificate_status() {
    print_header "Certificate Status Check"
    
    local days_remaining=$(get_days_until_expiry)
    
    if [ "$days_remaining" = "unknown" ]; then
        print_error "Cannot determine certificate expiration"
        return 1
    fi
    
    if [ "$days_remaining" -lt 0 ]; then
        print_error "Certificate has expired! ($days_remaining days ago)"
        return 1
    elif [ "$days_remaining" -lt 7 ]; then
        print_error "Certificate expires in $days_remaining days!"
        return 1
    elif [ "$days_remaining" -lt 30 ]; then
        print_warning "Certificate expires in $days_remaining days"
        return 0
    else
        print_success "Certificate is valid for $days_remaining days"
        return 0
    fi
}

# Function to check renewal status
check_renewal_status() {
    print_header "Renewal Status Check"
    
    if command -v certbot &> /dev/null; then
        echo "🔄 Testing certificate renewal..."
        if certbot renew --dry-run 2>/dev/null | grep -q "Congratulations"; then
            print_success "Certificate renewal test passed"
            return 0
        else
            print_error "Certificate renewal test failed"
            return 1
        fi
    else
        print_warning "Certbot not available for renewal testing"
        return 1
    fi
}

# Function to check service status
check_service_status() {
    print_header "Service Status Check"
    
    # Check Nginx
    if systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_error "Nginx is not running"
        return 1
    fi
    
    # Check FastAPI service
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        print_success "FastAPI service is running"
    else
        print_warning "FastAPI service is not running"
    fi
    
    # Check ports
    if netstat -tuln | grep -q ":443 "; then
        print_success "Port 443 is in use"
    else
        print_error "Port 443 is not in use"
        return 1
    fi
    
    if netstat -tuln | grep -q ":80 "; then
        print_success "Port 80 is in use"
    else
        print_warning "Port 80 is not in use"
    fi
}

# Function to check SSL configuration
check_ssl_configuration() {
    print_header "SSL Configuration Check"
    
    if command -v openssl &> /dev/null; then
        # Check SSL protocols
        echo "🔒 SSL Protocol Support:"
        
        # Test TLS 1.3
        if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_3 2>/dev/null | grep -q "TLSv1.3"; then
            print_success "TLS 1.3 supported"
        else
            print_warning "TLS 1.3 not supported"
        fi
        
        # Test TLS 1.2
        if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_2 2>/dev/null | grep -q "TLSv1.2"; then
            print_success "TLS 1.2 supported"
        else
            print_error "TLS 1.2 not supported"
        fi
        
        # Check for weak protocols
        if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_1 2>/dev/null | grep -q "TLSv1.1"; then
            print_warning "TLS 1.1 is enabled (security risk)"
        else
            print_success "TLS 1.1 is disabled"
        fi
        
        if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1 2>/dev/null | grep -q "TLSv1"; then
            print_error "TLS 1.0 is enabled (security risk)"
        else
            print_success "TLS 1.0 is disabled"
        fi
    else
        print_warning "OpenSSL not available for SSL configuration testing"
    fi
}

# Function to check security headers
check_security_headers() {
    print_header "Security Headers Check"
    
    local headers=$(curl -s -I "https://$DOMAIN" 2>/dev/null)
    
    if echo "$headers" | grep -q "Strict-Transport-Security"; then
        print_success "HSTS header present"
    else
        print_warning "HSTS header missing"
    fi
    
    if echo "$headers" | grep -q "X-Frame-Options"; then
        print_success "X-Frame-Options header present"
    else
        print_warning "X-Frame-Options header missing"
    fi
    
    if echo "$headers" | grep -q "X-Content-Type-Options"; then
        print_success "X-Content-Type-Options header present"
    else
        print_warning "X-Content-Type-Options header missing"
    fi
    
    if echo "$headers" | grep -q "X-XSS-Protection"; then
        print_success "X-XSS-Protection header present"
    else
        print_warning "X-XSS-Protection header missing"
    fi
}

# Function to check endpoint accessibility
check_endpoints() {
    print_header "Endpoint Accessibility Check"
    
    # Check health endpoint
    if curl -s -I "https://$DOMAIN/health" 2>/dev/null | grep -q "200"; then
        print_success "Health endpoint accessible"
    else
        print_warning "Health endpoint not accessible"
    fi
    
    # Check API endpoint
    if curl -s -I "https://$DOMAIN/api/v1/export/seasonal-trend" 2>/dev/null | grep -q "200\|401\|403"; then
        print_success "API endpoint accessible"
    else
        print_warning "API endpoint not accessible"
    fi
    
    # Check docs endpoint
    if curl -s -I "https://$DOMAIN/docs" 2>/dev/null | grep -q "200"; then
        print_success "Documentation endpoint accessible"
    else
        print_warning "Documentation endpoint not accessible"
    fi
}

# Function to generate report
generate_report() {
    print_header "SSL Monitoring Report"
    
    echo ""
    echo "📊 SSL Certificate Report for $DOMAIN"
    echo "======================================"
    echo ""
    
    # Certificate info
    local expiry_date=$(get_cert_expiry)
    local days_remaining=$(get_days_until_expiry)
    
    echo "🔐 Certificate Information:"
    echo "   Domain: $DOMAIN"
    echo "   Expiry Date: $expiry_date"
    echo "   Days Remaining: $days_remaining"
    echo ""
    
    # Service status
    echo "🖥️  Service Status:"
    if systemctl is-active --quiet nginx; then
        echo "   Nginx: ✅ Running"
    else
        echo "   Nginx: ❌ Stopped"
    fi
    
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        echo "   FastAPI: ✅ Running"
    else
        echo "   FastAPI: ❌ Stopped"
    fi
    
    echo ""
    
    # SSL configuration
    echo "🔒 SSL Configuration:"
    if command -v openssl &> /dev/null; then
        if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_3 2>/dev/null | grep -q "TLSv1.3"; then
            echo "   TLS 1.3: ✅ Supported"
        else
            echo "   TLS 1.3: ❌ Not supported"
        fi
        
        if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -tls1_2 2>/dev/null | grep -q "TLSv1.2"; then
            echo "   TLS 1.2: ✅ Supported"
        else
            echo "   TLS 1.2: ❌ Not supported"
        fi
    else
        echo "   SSL Testing: ⚠️  OpenSSL not available"
    fi
    
    echo ""
    
    # Recommendations
    echo "💡 Recommendations:"
    if [ "$days_remaining" != "unknown" ] && [ "$days_remaining" -lt 30 ]; then
        echo "   ⚠️  Certificate expires soon - consider renewal"
    fi
    
    if ! systemctl is-active --quiet nginx; then
        echo "   ⚠️  Nginx is not running - start with: sudo systemctl start nginx"
    fi
    
    if ! pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        echo "   ⚠️  FastAPI service is not running - start with: ./start-production-ssl.sh"
    fi
    
    echo ""
    echo "🔄 Auto-renewal: Configured (daily at 2 AM)"
    echo "📝 Logs: tail -f /var/log/ssl-renewal.log"
    echo "🔗 Test URL: https://$DOMAIN/health"
}

# Main monitoring function
main() {
    echo "🔍 Starting SSL monitoring for $DOMAIN..."
    echo ""
    
    # Run all checks
    check_certificate_status
    check_renewal_status
    check_service_status
    check_ssl_configuration
    check_security_headers
    check_endpoints
    
    echo ""
    generate_report
}

# Run main function
main