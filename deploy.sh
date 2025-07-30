#!/bin/bash

# Hackathon Service Deployment Script
# This script sets up the FastAPI service with nginx auto-start

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="hackathon-service"
NGINX_SITE_NAME="hackathon-service"
DOMAIN_NAME="your-domain.com"  # Change this to your actual domain
APP_PORT=8000
NGINX_PORT=80
SSL_PORT=443

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Install Python and pip
    apt-get install -y python3 python3-pip python3-venv
    
    # Install nginx
    apt-get install -y nginx
    
    # Install Docker and Docker Compose
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Install additional tools
    apt-get install -y curl wget git unzip
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
}

# Create application directory and user
setup_application() {
    log "Setting up application directory and user..."
    
    # Create application user
    if ! id -u $SERVICE_NAME &>/dev/null; then
        useradd -r -s /bin/bash -d /opt/$SERVICE_NAME $SERVICE_NAME
    fi
    
    # Create application directory
    mkdir -p /opt/$SERVICE_NAME
    chown $SERVICE_NAME:$SERVICE_NAME /opt/$SERVICE_NAME
    
    # Copy application files
    cp -r . /opt/$SERVICE_NAME/
    chown -R $SERVICE_NAME:$SERVICE_NAME /opt/$SERVICE_NAME
    
    # Create logs and backups directories
    mkdir -p /opt/$SERVICE_NAME/logs /opt/$SERVICE_NAME/backups
    chown -R $SERVICE_NAME:$SERVICE_NAME /opt/$SERVICE_NAME/logs /opt/$SERVICE_NAME/backups
}

# Create systemd service file
create_systemd_service() {
    log "Creating systemd service..."
    
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Hackathon Service API
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/$SERVICE_NAME
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=$SERVICE_NAME
Group=$SERVICE_NAME
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME.service
}

# Configure nginx
configure_nginx() {
    log "Configuring nginx..."
    
    # Create nginx site configuration
    cat > /etc/nginx/sites-available/$NGINX_SITE_NAME << EOF
server {
    listen $NGINX_PORT;
    server_name $DOMAIN_NAME;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen $SSL_PORT ssl http2;
    server_name $DOMAIN_NAME;
    
    # SSL Configuration (you'll need to add your SSL certificates)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
    
    # Client max body size
    client_max_body_size 100M;
    
    # Proxy settings
    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:$APP_PORT/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/$SERVICE_NAME/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Enable the site
    ln -sf /etc/nginx/sites-available/$NGINX_SITE_NAME /etc/nginx/sites-enabled/
    
    # Remove default nginx site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    # Restart nginx
    systemctl restart nginx
    systemctl enable nginx
}

# Setup SSL with Let's Encrypt (optional)
setup_ssl() {
    info "Setting up SSL with Let's Encrypt..."
    
    # Install certbot
    apt-get install -y certbot python3-certbot-nginx
    
    # Get SSL certificate
    if [ "$DOMAIN_NAME" != "your-domain.com" ]; then
        certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
    else
        warning "Please update DOMAIN_NAME in the script and run certbot manually:"
        warning "certbot --nginx -d your-domain.com"
    fi
}

# Create firewall rules
setup_firewall() {
    log "Setting up firewall..."
    
    # Install ufw if not present
    apt-get install -y ufw
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    ufw --force enable
}

# Create backup script
create_backup_script() {
    log "Creating backup script..."
    
    cat > /opt/$SERVICE_NAME/backup.sh << 'EOF'
#!/bin/bash

# Backup script for Hackathon Service
BACKUP_DIR="/opt/hackathon-service/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="hackathon_backup_$DATE.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup
tar -czf $BACKUP_DIR/$BACKUP_NAME \
    --exclude='./logs/*' \
    --exclude='./backups/*' \
    --exclude='./.git/*' \
    --exclude='./__pycache__/*' \
    --exclude='./*.pyc' \
    .

# Keep only last 7 backups
find $BACKUP_DIR -name "hackathon_backup_*.tar.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_NAME"
EOF

    chmod +x /opt/$SERVICE_NAME/backup.sh
    chown $SERVICE_NAME:$SERVICE_NAME /opt/$SERVICE_NAME/backup.sh
}

# Create monitoring script
create_monitoring_script() {
    log "Creating monitoring script..."
    
    cat > /opt/$SERVICE_NAME/monitor.sh << 'EOF'
#!/bin/bash

# Monitoring script for Hackathon Service
SERVICE_NAME="hackathon-service"
APP_PORT=8000

echo "=== Hackathon Service Status ==="
echo "Date: $(date)"
echo ""

# Check systemd service status
echo "Systemd Service Status:"
systemctl status $SERVICE_NAME --no-pager -l
echo ""

# Check Docker containers
echo "Docker Containers:"
docker ps -a
echo ""

# Check nginx status
echo "Nginx Status:"
systemctl status nginx --no-pager -l
echo ""

# Check application health
echo "Application Health Check:"
curl -f http://localhost:$APP_PORT/health 2>/dev/null && echo "✅ Application is healthy" || echo "❌ Application is not responding"
echo ""

# Check disk usage
echo "Disk Usage:"
df -h
echo ""

# Check memory usage
echo "Memory Usage:"
free -h
echo ""

# Check recent logs
echo "Recent Application Logs:"
tail -n 20 /opt/$SERVICE_NAME/logs/*.log 2>/dev/null || echo "No log files found"
EOF

    chmod +x /opt/$SERVICE_NAME/monitor.sh
    chown $SERVICE_NAME:$SERVICE_NAME /opt/$SERVICE_NAME/monitor.sh
}

# Create log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/$SERVICE_NAME << EOF
/opt/$SERVICE_NAME/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_NAME $SERVICE_NAME
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
}

# Main deployment function
deploy() {
    log "Starting Hackathon Service deployment..."
    
    check_root
    update_system
    install_dependencies
    setup_application
    create_systemd_service
    configure_nginx
    setup_firewall
    create_backup_script
    create_monitoring_script
    setup_log_rotation
    
    # Start the service
    log "Starting the service..."
    systemctl start $SERVICE_NAME
    
    # Wait a moment for the service to start
    sleep 10
    
    # Check service status
    if systemctl is-active --quiet $SERVICE_NAME; then
        log "✅ Service started successfully!"
    else
        error "❌ Service failed to start. Check logs with: journalctl -u $SERVICE_NAME -f"
    fi
    
    log "Deployment completed successfully!"
    log ""
    log "=== Service Information ==="
    log "Service Name: $SERVICE_NAME"
    log "Application URL: http://localhost:$APP_PORT"
    log "Nginx URL: http://$DOMAIN_NAME"
    log ""
    log "=== Useful Commands ==="
    log "Check service status: systemctl status $SERVICE_NAME"
    log "View service logs: journalctl -u $SERVICE_NAME -f"
    log "Restart service: systemctl restart $SERVICE_NAME"
    log "Monitor service: /opt/$SERVICE_NAME/monitor.sh"
    log "Create backup: /opt/$SERVICE_NAME/backup.sh"
    log ""
    log "=== Next Steps ==="
    log "1. Update DOMAIN_NAME in this script and run setup_ssl()"
    log "2. Configure your domain DNS to point to this server"
    log "3. Set up SSL certificates with Let's Encrypt"
    log "4. Configure environment variables in docker-compose.yml"
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy      Deploy the complete service"
    echo "  update      Update the service"
    echo "  restart     Restart the service"
    echo "  status      Show service status"
    echo "  logs        Show service logs"
    echo "  backup      Create backup"
    echo "  monitor     Run monitoring script"
    echo "  help        Show this help message"
    echo ""
}

# Function to update service
update_service() {
    log "Updating Hackathon Service..."
    
    # Pull latest changes
    cd /opt/$SERVICE_NAME
    git pull origin main
    
    # Restart service
    systemctl restart $SERVICE_NAME
    
    log "Service updated successfully!"
}

# Function to restart service
restart_service() {
    log "Restarting Hackathon Service..."
    systemctl restart $SERVICE_NAME
    log "Service restarted!"
}

# Function to show status
show_status() {
    systemctl status $SERVICE_NAME --no-pager -l
}

# Function to show logs
show_logs() {
    journalctl -u $SERVICE_NAME -f
}

# Function to create backup
create_backup() {
    /opt/$SERVICE_NAME/backup.sh
}

# Function to run monitoring
run_monitoring() {
    /opt/$SERVICE_NAME/monitor.sh
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    update)
        update_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        create_backup
        ;;
    monitor)
        run_monitoring
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        error "Unknown option: $1"
        usage
        exit 1
        ;;
esac