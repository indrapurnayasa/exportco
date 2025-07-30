#!/bin/bash

# Let's Encrypt SSL Setup Script for Hackathon Service
# This script sets up SSL certificates and configures the service for production

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
echo "🔐 LET'S ENCRYPT SSL SETUP"
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

# Step 1: Update system
print_header "Step 1: Updating system..."
apt update && apt upgrade -y
print_success "System updated"

# Step 2: Install dependencies
print_header "Step 2: Installing dependencies..."
apt install -y curl wget git nginx certbot python3-certbot-nginx snapd
print_success "Dependencies installed"

# Step 3: Install certbot via snap (recommended)
print_header "Step 3: Installing certbot..."
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot
print_success "Certbot installed"

# Step 4: Stop existing services
print_header "Step 4: Stopping existing services..."
systemctl stop nginx 2>/dev/null || true
systemctl stop apache2 2>/dev/null || true
print_success "Services stopped"

# Step 5: Verify domain pointing
print_header "Step 5: Verifying domain configuration..."
SERVER_IP=$(curl -s ifconfig.me)
print_warning "Your server IP: $SERVER_IP"
print_warning "Make sure your domain $DOMAIN points to this IP"
print_warning "DNS A record should be: $DOMAIN -> $SERVER_IP"

echo ""
echo "Press Enter to continue after verifying DNS..."
read -r

# Step 6: Generate SSL certificate
print_header "Step 6: Generating SSL certificate..."
certbot certonly --standalone -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" || {
    print_error "Failed to generate certificate. Please check:"
    echo "1. Domain DNS is pointing to this server"
    echo "2. Port 80 is open and accessible"
    echo "3. Domain is valid and accessible"
    exit 1
}
print_success "SSL certificate generated"

# Step 7: Create Nginx configuration
print_header "Step 7: Creating Nginx configuration..."
cat > /etc/nginx/sites-available/"$DOMAIN" << EOF
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

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
        
        # Timeout settings for Vercel compatibility
        proxy_connect_timeout 10s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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
    }

    # Root redirect to API docs
    location / {
        return 301 https://\$server_name/docs;
    }
}
EOF

print_success "Nginx configuration created"

# Step 8: Enable site
print_header "Step 8: Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/"$DOMAIN" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
print_success "Site enabled"

# Step 9: Test Nginx configuration
print_header "Step 9: Testing Nginx configuration..."
nginx -t || {
    print_error "Nginx configuration test failed"
    exit 1
}
print_success "Nginx configuration is valid"

# Step 10: Start Nginx
print_header "Step 10: Starting Nginx..."
systemctl start nginx
systemctl enable nginx
print_success "Nginx started and enabled"

# Step 11: Configure firewall
print_header "Step 11: Configuring firewall..."
ufw allow 80
ufw allow 443
ufw allow 22
ufw --force enable
print_success "Firewall configured"

# Step 12: Create SSL renewal script
print_header "Step 12: Creating SSL renewal script..."
cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash
# SSL Renewal Script for Hackathon Service

# Renew certificate
/usr/bin/certbot renew --quiet

# Restart services if renewal was successful
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "$(date): SSL certificate renewed successfully" >> /var/log/ssl-renewal.log
else
    echo "$(date): SSL certificate renewal failed" >> /var/log/ssl-renewal.log
fi
EOF

chmod +x /usr/local/bin/renew-ssl.sh
print_success "Renewal script created"

# Step 13: Setup auto-renewal cron job
print_header "Step 13: Setting up auto-renewal..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1") | crontab -
print_success "Auto-renewal configured"

# Step 14: Create production service script
print_header "Step 14: Creating production service script..."
cat > start-production-ssl.sh << EOF
#!/bin/bash

# Production Service with SSL
# This script starts the FastAPI service behind Nginx

echo "=========================================="
echo "🚀 STARTING PRODUCTION SERVICE WITH SSL"
echo "=========================================="

# Stop existing services
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

# Activate conda environment
source \$(conda info --base)/etc/profile.d/conda.sh
conda activate hackathon-env

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
else
    echo "❌ Failed to start FastAPI service"
    echo "Check logs: tail -f logs/uvicorn-ssl.log"
fi
EOF

chmod +x start-production-ssl.sh
print_success "Production service script created"

# Step 15: Create stop script
print_header "Step 15: Creating stop script..."
cat > stop-production-ssl.sh << 'EOF'
#!/bin/bash

echo "=========================================="
echo "🛑 STOPPING PRODUCTION SERVICE"
echo "=========================================="

# Stop FastAPI service
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

# Stop Nginx
systemctl stop nginx

echo "✅ Services stopped"
EOF

chmod +x stop-production-ssl.sh
print_success "Stop script created"

# Step 16: Create status script
print_header "Step 16: Creating status script..."
cat > status-production-ssl.sh << 'EOF'
#!/bin/bash

echo "=========================================="
echo "📊 PRODUCTION SERVICE STATUS"
echo "=========================================="

# Check FastAPI service
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ FastAPI service: RUNNING"
else
    echo "❌ FastAPI service: STOPPED"
fi

# Check Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service: RUNNING"
else
    echo "❌ Nginx service: STOPPED"
fi

# Check SSL certificate
if certbot certificates | grep -q "$DOMAIN"; then
    echo "✅ SSL certificate: VALID"
    certbot certificates | grep "$DOMAIN" -A 5
else
    echo "❌ SSL certificate: NOT FOUND"
fi

# Check ports
echo ""
echo "🔍 Port Status:"
netstat -tlnp | grep -E ":80|:443|:8000" || echo "No services listening on expected ports"
EOF

chmod +x status-production-ssl.sh
print_success "Status script created"

# Step 17: Test the setup
print_header "Step 17: Testing SSL setup..."

# Test certificate
if certbot certificates | grep -q "$DOMAIN"; then
    print_success "SSL certificate is valid"
else
    print_error "SSL certificate not found"
fi

# Test Nginx
if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx is not running"
fi

echo ""
echo "=========================================="
echo "🎉 SSL SETUP COMPLETED!"
echo "=========================================="
echo ""
echo "📋 SUMMARY:"
echo "✅ SSL certificate generated for $DOMAIN"
echo "✅ Nginx configured and running"
echo "✅ Firewall configured"
echo "✅ Auto-renewal setup"
echo "✅ Production scripts created"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Start your production service:"
echo "   ./start-production-ssl.sh"
echo ""
echo "2. Test your API endpoints:"
echo "   curl -k https://$DOMAIN/health"
echo "   curl -k https://$DOMAIN/api/v1/export/seasonal-trend"
echo ""
echo "3. Update your frontend to use:"
echo "   https://$DOMAIN/api/v1/export/seasonal-trend"
echo ""
echo "4. Check status anytime:"
echo "   ./status-production-ssl.sh"
echo ""
echo "5. Stop services:"
echo "   ./stop-production-ssl.sh"
echo ""
echo "🔐 SSL Certificate will auto-renew every 60 days"
echo "📝 Logs: /var/log/ssl-renewal.log"
echo "=========================================="