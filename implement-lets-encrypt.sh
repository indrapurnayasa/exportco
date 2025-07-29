#!/bin/bash

# Let's Encrypt SSL Implementation Script
# Modern SSL setup with auto-renewal and security best practices

set -e  # Exit on any error

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
echo "🔐 LET'S ENCRYPT SSL IMPLEMENTATION"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Get domain from user
echo "Enter your domain name (e.g., yourdomain.com):"
read -r DOMAIN

if [ -z "$DOMAIN" ]; then
    print_error "Domain name is required"
    exit 1
fi

print_header "Setting up SSL for domain: $DOMAIN"

# Step 1: Update system and install dependencies
print_header "Step 1: Updating system and installing dependencies..."
apt update && apt upgrade -y
apt install -y curl wget git nginx snapd
print_success "System updated and dependencies installed"

# Step 2: Install certbot via snap (recommended)
print_header "Step 2: Installing certbot..."
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot
print_success "Certbot installed"

# Step 3: Verify domain pointing
print_header "Step 3: Verifying domain configuration..."
SERVER_IP=$(curl -s ifconfig.me)
print_warning "Your server IP: $SERVER_IP"
print_warning "Make sure your domain $DOMAIN points to this IP"
print_warning "DNS A record should be: $DOMAIN -> $SERVER_IP"

# Test domain resolution
echo ""
echo "Testing domain resolution..."
if nslookup "$DOMAIN" | grep -q "$SERVER_IP"; then
    print_success "Domain $DOMAIN is pointing to this server"
else
    print_warning "Domain $DOMAIN may not be pointing to this server"
    print_warning "Expected IP: $SERVER_IP"
    nslookup "$DOMAIN"
fi

echo ""
echo "Press Enter to continue after verifying DNS..."
read -r

# Step 4: Stop services using port 80
print_header "Step 4: Stopping services using port 80..."
systemctl stop nginx 2>/dev/null || true
systemctl stop apache2 2>/dev/null || true
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

# Verify port 80 is free
if netstat -tuln | grep -q ":80 "; then
    print_error "Port 80 is still in use. Please stop the service using it."
    exit 1
else
    print_success "Port 80 is free"
fi

# Step 5: Generate SSL certificate
print_header "Step 5: Generating SSL certificate..."
certbot certonly --standalone -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" || {
    print_error "Failed to generate certificate. Please check:"
    echo "1. Domain DNS is pointing to this server"
    echo "2. Port 80 is open and accessible"
    echo "3. Domain is valid and accessible"
    exit 1
}
print_success "SSL certificate generated"

# Step 6: Create Nginx configuration with modern SSL settings
print_header "Step 6: Creating Nginx configuration..."
cat > /etc/nginx/sites-available/"$DOMAIN" << EOF
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server with modern SSL configuration
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL Configuration - Modern and Secure
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Modern SSL protocols and ciphers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';";

    # API Backend (FastAPI)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://\$host" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        add_header Access-Control-Expose-Headers "Content-Length,Content-Range" always;
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "https://\$host" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Cache health checks for 30 seconds
        proxy_cache_valid 200 30s;
        add_header Cache-Control "public, max-age=30";
    }

    # API Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # OpenAPI JSON
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Cache OpenAPI spec for 1 hour
        proxy_cache_valid 200 1h;
        add_header Cache-Control "public, max-age=3600";
    }

    # Root redirect to API docs
    location / {
        return 301 https://\$server_name/docs;
    }

    # Security: Deny access to hidden files
    location ~ /\. {
        deny all;
    }

    # Security: Deny access to backup files
    location ~ ~$ {
        deny all;
    }
}
EOF

print_success "Nginx configuration created with modern SSL settings"

# Step 7: Enable site and test configuration
print_header "Step 7: Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/"$DOMAIN" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Test Nginx configuration
nginx -t || {
    print_error "Nginx configuration test failed"
    exit 1
}
print_success "Nginx configuration is valid"

# Step 8: Start Nginx
print_header "Step 8: Starting Nginx..."
systemctl start nginx
systemctl enable nginx
print_success "Nginx started and enabled"

# Step 9: Create SSL renewal script
print_header "Step 9: Creating SSL renewal script..."
cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash

echo "🔄 Renewing SSL certificates..."

# Renew certificate
/usr/bin/certbot renew --quiet

# Check if renewal was successful
if [ $? -eq 0 ]; then
    echo "✅ SSL certificates renewed successfully"
    
    # Reload Nginx
    systemctl reload nginx
    echo "✅ Nginx reloaded"
    
    # Restart FastAPI service if running
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        pkill -f "uvicorn.*app.main:app"
        sleep 2
        cd /path/to/your/app && ./start-production-ssl.sh
        echo "✅ FastAPI service restarted"
    fi
else
    echo "❌ SSL certificate renewal failed"
    exit 1
fi
EOF

chmod +x /usr/local/bin/renew-ssl.sh
print_success "SSL renewal script created"

# Step 10: Setup auto-renewal cron job
print_header "Step 10: Setting up auto-renewal..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1") | crontab -
print_success "Auto-renewal configured (daily at 2 AM)"

# Step 11: Create production service script
print_header "Step 11: Creating production service script..."
cat > start-production-ssl.sh << EOF
#!/bin/bash

echo "=========================================="
echo "🚀 STARTING PRODUCTION SERVICE WITH SSL"
echo "=========================================="

# Kill any processes using our ports first
echo "🛑 Clearing ports before startup..."
./kill-ports.sh

echo ""
echo "🚀 Starting production service..."

# Check if conda is available and activate environment
if command -v conda &> /dev/null; then
    echo "Activating conda environment..."
    source \$(conda info --base)/etc/profile.d/conda.sh
    conda activate hackathon-env
else
    echo "Conda not found, using system Python..."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start FastAPI service (HTTP only, Nginx handles HTTPS)
echo "Starting FastAPI service on port 8000..."
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 > logs/uvicorn-ssl.log 2>&1 &

# Wait for service to start
sleep 5

# Check if service is running
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ FastAPI service started successfully"
    echo "🌐 Your API is now available at:"
    echo "   https://$DOMAIN/api/v1/export/seasonal-trend"
    echo "   https://$DOMAIN/docs"
    echo "   https://$DOMAIN/health"
    echo ""
    echo "📝 Logs are available at: logs/uvicorn-ssl.log"
    echo "🔍 To monitor logs: tail -f logs/uvicorn-ssl.log"
    echo ""
    echo "🔧 To stop the service: ./stop-production-ssl.sh"
    echo "📊 To check status: ./status-production-ssl.sh"
else
    echo "❌ Failed to start FastAPI service"
    echo "Check logs: tail -f logs/uvicorn-ssl.log"
    exit 1
fi
EOF

chmod +x start-production-ssl.sh
print_success "Production service script created"

# Step 12: Test SSL configuration
print_header "Step 12: Testing SSL configuration..."

# Test with openssl
echo "🔐 Testing SSL certificate..."
if command -v openssl &> /dev/null; then
    echo "SSL Certificate Info:"
    echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates
else
    echo "⚠️  OpenSSL not available for testing"
fi

# Test with curl
echo ""
echo "🌐 Testing HTTPS endpoint..."
curl -I "https://$DOMAIN/health" 2>/dev/null || echo "⚠️  HTTPS test failed - service may not be running yet"

print_success "SSL implementation completed!"

echo ""
echo "🎯 SSL Implementation Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Start your service: ./start-production-ssl.sh"
echo "2. Test your API: https://$DOMAIN/api/v1/export/seasonal-trend"
echo "3. Check documentation: https://$DOMAIN/docs"
echo "4. Monitor logs: tail -f logs/uvicorn-ssl.log"
echo ""
echo "🔄 SSL will auto-renew daily at 2 AM"
echo "📝 Check renewal logs: tail -f /var/log/ssl-renewal.log"
echo ""
echo "🔐 SSL Certificate Details:"
echo "   - Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "   - Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo "   - Auto-renewal: /usr/local/bin/renew-ssl.sh"
echo ""
echo "🌐 Test your SSL: https://www.ssllabs.com/ssltest/"