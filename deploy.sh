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
DOMAIN_NAME="dev-ngurah.fun"  # Change this to your actual domain
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
    apt-get install -y python3 python3-pip
    
    # Install nginx
    apt-get install -y nginx
    
    # Install additional tools
    apt-get install -y curl wget git unzip build-essential libpq-dev python3-dev
    
    # Install PostgreSQL
    apt-get install -y postgresql postgresql-contrib
    
    # Install Miniconda if not present
    if ! command -v conda &> /dev/null; then
        log "Installing Miniconda..."
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
        bash /tmp/miniconda.sh -b -p /opt/miniconda3
        rm /tmp/miniconda.sh
        
        # Add conda to PATH for all users
        echo 'export PATH="/opt/miniconda3/bin:$PATH"' >> /etc/profile
        echo 'export PATH="/opt/miniconda3/bin:$PATH"' >> /etc/bash.bashrc
        
        # Source the profile
        source /etc/profile
    fi
    
    # Create conda environment
    log "Creating conda environment..."
    /opt/miniconda3/bin/conda create -n hackathon-env python=3.11 -y
    
    # Install uvicorn in the conda environment
    /opt/miniconda3/bin/conda run -n hackathon-env pip install uvicorn[standard]
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
    
    # Install Python dependencies in conda environment
    log "Installing Python dependencies in conda environment..."
    cd /opt/$SERVICE_NAME
    /opt/miniconda3/bin/conda run -n hackathon-env pip install -r requirements.txt
}

# Set up PostgreSQL database
setup_postgresql() {
    log "Setting up PostgreSQL database..."
    
    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # Wait for PostgreSQL to be ready
    log "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Check if PostgreSQL is running
    if ! systemctl is-active --quiet postgresql; then
        error "PostgreSQL failed to start"
    fi
    
    # Create database and user (only if they don't exist)
    sudo -u postgres psql << EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hackathondb') THEN
        CREATE DATABASE hackathondb;
    END IF;
END
\$\$;

DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'maverick') THEN
        CREATE USER maverick WITH PASSWORD 'Hackathon2025';
    END IF;
END
\$\$;

GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;
ALTER USER maverick CREATEDB;
\q
EOF
    
    log "PostgreSQL database setup completed"
}

# Create .env file with database configuration
create_env_file() {
    log "Creating environment configuration..."
    
    cat > /opt/$SERVICE_NAME/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://maverick:Hackathon2025@localhost:5432/hackathondb
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=Hackathon2025
POSTGRES_HOST=101.50.2.59
POSTGRES_PORT=5432

# API Configuration
PROJECT_NAME=Hackathon Service API
VERSION=1.0.0
DESCRIPTION=A FastAPI service for hackathon management
API_V1_STR=/api/v1

# Security Configuration
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SECRET_KEY=your-secret-key-here-change-in-production

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Logging Configuration
LOG_LEVEL=INFO
DEBUG=false
EOF

    chown $SERVICE_NAME:$SERVICE_NAME /opt/$SERVICE_NAME/.env
    log "Environment file created"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    cd /opt/$SERVICE_NAME
    
    # Run alembic migrations
    /opt/miniconda3/bin/conda run -n hackathon-env alembic upgrade head
    
    log "Database migrations completed"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    cd /opt/$SERVICE_NAME
    
    # Run alembic migrations
    /opt/miniconda3/bin/conda run -n hackathon-env alembic upgrade head
    
    log "Database migrations completed"
}

# Create systemd service file
create_systemd_service() {
    log "Creating systemd service..."
    
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Hackathon Service API
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory=/opt/$SERVICE_NAME
ExecStart=/opt/miniconda3/bin/conda run -n hackathon-env uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
User=$SERVICE_NAME
Group=$SERVICE_NAME
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PATH=/opt/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

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
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
    
    # Client max body size
    client_max_body_size 100M;
    
    # Proxy settings for FastAPI
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
    
    # Specific proxy for /docs
    location /docs {
        proxy_pass http://localhost:$APP_PORT/docs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Proxy for OpenAPI JSON
    location /openapi.json {
        proxy_pass http://localhost:$APP_PORT/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
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

# Check Python processes
echo "Python/Uvicorn Processes:"
ps aux | grep -E "(uvicorn|conda.*hackathon-env)" | grep -v grep
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
    setup_postgresql
    create_env_file
    run_migrations
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
    log "4. Configure environment variables in .env file"
}

# Function to kill ports
kill_ports() {
    log "Killing processes on ports 80, 443, 8000..."
    
    # Kill processes on specific ports
    sudo fuser -k 80/tcp 2>/dev/null || true
    sudo fuser -k 443/tcp 2>/dev/null || true
    sudo fuser -k 8000/tcp 2>/dev/null || true
    
    log "Ports cleared"
}

# Function to restart nginx
restart_nginx() {
    log "Restarting nginx..."
    
    # Test nginx configuration
    sudo nginx -t
    
    # Restart nginx
    sudo systemctl restart nginx
    sudo systemctl status nginx --no-pager -l
}

# Function to check database
check_database() {
    log "Checking database connection..."
    
    # Check if PostgreSQL is running
    if systemctl is-active --quiet postgresql; then
        log "✅ PostgreSQL is running"
    else
        log "❌ PostgreSQL is not running, starting..."
        sudo systemctl start postgresql
    fi
    
    # Test database connection
    if PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -c "SELECT 1;" 2>/dev/null; then
        log "✅ Database connection successful"
    else
        log "❌ Database connection failed"
        log "Attempting to fix database..."
        setup_postgresql
    fi
}

# Function to start service
start_service() {
    log "Starting hackathon service..."
    
    # Start the service
    sudo systemctl start hackathon-service
    
    # Wait for service to start
    sleep 10
    
    # Check service status
    if systemctl is-active --quiet hackathon-service; then
        log "✅ Service started successfully!"
    else
        log "❌ Service failed to start"
        sudo systemctl status hackathon-service --no-pager -l
    fi
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
    echo "  kill-ports  Kill processes on ports 80, 443, 8000"
    echo "  restart-nginx Restart nginx service"
    echo "  check-db    Check database connection"
    echo "  start       Start hackathon service"
    echo "  full-restart Kill ports, restart nginx, check db, start service"
    echo "  help        Show this help message"
    echo ""
}

# Function to update service
update_service() {
    log "Updating Hackathon Service..."
    
    # Pull latest changes
    cd /opt/$SERVICE_NAME
    git pull origin main
    
    # Install/update Python dependencies in conda environment
    /opt/miniconda3/bin/conda run -n hackathon-env pip install -r requirements.txt
    
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
    kill-ports)
        kill_ports
        ;;
    restart-nginx)
        restart_nginx
        ;;
    check-db)
        check_database
        ;;
    start)
        start_service
        ;;
    full-restart)
        log "Performing full restart..."
        kill_ports
        restart_nginx
        check_database
        start_service
        log "Full restart completed!"
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
