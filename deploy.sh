#!/bin/bash

# Hackathon Service VPS Deployment Script
# This script deploys the FastAPI application on a VPS with HTTPS support
# and automatic restart capabilities

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load configuration
if [ -f "deploy.config" ]; then
    source deploy.config
else
    print_error "deploy.config file not found. Please create it first."
    exit 1
fi

# Default values if not set in config
APP_NAME=${APP_NAME:-"hackathon-service"}
APP_DIR=${APP_DIR:-"/opt/$APP_NAME"}
SERVICE_NAME="${APP_NAME}.service"
DOMAIN_NAME=${DOMAIN_NAME:-""}
EMAIL=${EMAIL:-""}
PORT=${PORT:-8000}
SSL_PORT=443
UVICORN_WORKERS=${UVICORN_WORKERS:-4}
CONDA_ENV_NAME=${CONDA_ENV_NAME:-"hackathon-env"}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_system_requirements() {
    print_status "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
        exit 1
    fi
    
    # Check if sudo is available
    if ! command_exists sudo; then
        print_error "sudo is not installed. Please install sudo first."
        exit 1
    fi
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This script is designed for Linux systems only."
        exit 1
    fi
    
    # Check available memory (minimum 1GB)
    MEMORY_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    MEMORY_GB=$((MEMORY_KB / 1024 / 1024))
    if [ "$MEMORY_GB" -lt 1 ]; then
        print_error "Insufficient memory. At least 1GB RAM is required."
        exit 1
    fi
    
    # Check available disk space (minimum 5GB)
    DISK_SPACE=$(df / | awk 'NR==2 {print $4}')
    DISK_SPACE_GB=$((DISK_SPACE / 1024 / 1024))
    if [ "$DISK_SPACE_GB" -lt 5 ]; then
        print_error "Insufficient disk space. At least 5GB free space is required."
        exit 1
    fi
    
    print_success "System requirements check passed"
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        python3 \
        python3-pip \
        nginx \
        certbot \
        python3-certbot-nginx \
        postgresql \
        postgresql-contrib \
        curl \
        wget \
        git \
        unzip \
        build-essential \
        libpq-dev \
        python3-dev \
        ufw
    
    print_success "System dependencies installed"
}

# Function to install Miniconda
install_miniconda() {
    print_status "Installing Miniconda..."
    
    # Download Miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
    
    # Install Miniconda
    bash ~/miniconda.sh -b -p $HOME/miniconda
    
    # Add conda to PATH
    echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    
    # Initialize conda
    $HOME/miniconda/bin/conda init bash
    
    print_success "Miniconda installed"
}

# Function to setup firewall
setup_firewall() {
    if [ "$CONFIGURE_FIREWALL" = "true" ]; then
        print_status "Setting up firewall..."
        
        # Reset UFW to default
        sudo ufw --force reset
        
        # Set default policies
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        
        # Allow SSH
        if [ "$FIREWALL_ALLOW_SSH" = "true" ]; then
            sudo ufw allow ssh
        fi
        
        # Allow HTTP
        if [ "$FIREWALL_ALLOW_HTTP" = "true" ]; then
            sudo ufw allow 80/tcp
        fi
        
        # Allow HTTPS
        if [ "$FIREWALL_ALLOW_HTTPS" = "true" ]; then
            sudo ufw allow 443/tcp
        fi
        
        # Enable firewall
        sudo ufw --force enable
        
        print_success "Firewall configured and enabled"
    else
        print_warning "Firewall configuration skipped"
    fi
}

# Function to setup PostgreSQL
setup_postgresql() {
    print_status "Setting up PostgreSQL..."
    
    # Start PostgreSQL service
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE $POSTGRES_DB;" || print_warning "Database might already exist"
    sudo -u postgres psql -c "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';" || print_warning "User might already exist"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;" || print_warning "Privileges might already be granted"
    sudo -u postgres psql -c "ALTER USER $POSTGRES_USER CREATEDB;" || print_warning "User privileges might already be set"
    
    print_success "PostgreSQL setup completed"
}

# Function to create application directory and user
setup_application_user() {
    print_status "Setting up application user and directory..."
    
    # Create application user
    sudo useradd -r -s /bin/false $APP_NAME || print_warning "User might already exist"
    
    # Create application directory
    sudo mkdir -p $APP_DIR
    sudo chown $APP_NAME:$APP_NAME $APP_DIR
    
    print_success "Application user and directory setup completed"
}

# Function to deploy application code
deploy_application() {
    print_status "Deploying application code..."
    
    # Copy application files
    sudo cp -r . $APP_DIR/
    sudo chown -R $APP_NAME:$APP_NAME $APP_DIR
    
    # Install Miniconda for the application user
    sudo -u $APP_NAME wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $APP_DIR/miniconda.sh
    sudo -u $APP_NAME bash $APP_DIR/miniconda.sh -b -p $APP_DIR/miniconda
    sudo -u $APP_NAME rm $APP_DIR/miniconda.sh
    
    # Create conda environment
    sudo -u $APP_NAME $APP_DIR/miniconda/bin/conda create -n $CONDA_ENV_NAME python=3.11 -y
    
    # Install Python dependencies
    sudo -u $APP_NAME $APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin/pip install --upgrade pip
    sudo -u $APP_NAME $APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin/pip install -r $APP_DIR/requirements.txt
    
    print_success "Application code deployed"
}

# Function to create systemd service
create_systemd_service() {
    print_status "Creating systemd service..."
    
    cat << EOF | sudo tee /etc/systemd/system/$SERVICE_NAME
[Unit]
Description=Hackathon Service FastAPI Application
After=network.target postgresql.service

[Service]
Type=exec
User=$APP_NAME
Group=$APP_NAME
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin
ExecStart=$APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers $UVICORN_WORKERS
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_success "Systemd service created and enabled"
}

# Function to setup Nginx
setup_nginx() {
    print_status "Setting up Nginx..."
    
    # Create Nginx configuration
    cat << EOF | sudo tee /etc/nginx/sites-available/$APP_NAME
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;
    
    # SSL configuration will be added by certbot
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:$PORT/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    sudo nginx -t
    
    print_success "Nginx configuration created"
}

# Function to setup SSL certificate
setup_ssl() {
    if [ -z "$DOMAIN_NAME" ] || [ -z "$EMAIL" ]; then
        print_warning "Domain name or email not set. Skipping SSL setup."
        return
    fi
    
    print_status "Setting up SSL certificate..."
    
    # Check if DOMAIN_NAME is an IP address
    if [[ $DOMAIN_NAME =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_warning "SSL certificates cannot be issued for IP addresses. HTTPS will not be available."
        print_warning "Consider using a domain name for HTTPS support."
        return
    fi
    
    # Get SSL certificate
    sudo certbot --nginx -d $DOMAIN_NAME --email $EMAIL --non-interactive --agree-tos
    
    # Setup auto-renewal
    sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
    
    print_success "SSL certificate setup completed"
}

# Function to create environment file
create_environment_file() {
    print_status "Creating environment file..."
    
    cat << EOF | sudo tee $APP_DIR/.env
# Database settings
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=$POSTGRES_HOST
POSTGRES_PORT=$POSTGRES_PORT

# Production settings
DB_POOL_SIZE=$DB_POOL_SIZE
DB_MAX_OVERFLOW=$DB_MAX_OVERFLOW
DB_POOL_TIMEOUT=$DB_POOL_TIMEOUT
DB_POOL_RECYCLE=$DB_POOL_RECYCLE

# Rate limiting
RATE_LIMIT_REQUESTS=$RATE_LIMIT_REQUESTS
RATE_LIMIT_WINDOW=$RATE_LIMIT_WINDOW

# Cache settings
CACHE_TTL=$CACHE_TTL
CACHE_MAX_SIZE=$CACHE_MAX_SIZE

# Query limits
MAX_QUERY_LIMIT=$MAX_QUERY_LIMIT
QUERY_TIMEOUT=$QUERY_TIMEOUT

# Logging
LOG_LEVEL=$LOG_LEVEL
EOF
    
    sudo chown $APP_NAME:$APP_NAME $APP_DIR/.env
    sudo chmod 600 $APP_DIR/.env
    
    print_success "Environment file created"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    cd $APP_DIR
    sudo -u $APP_NAME $APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin/alembic upgrade head
    
    print_success "Database migrations completed"
}

# Function to setup monitoring (optional)
setup_monitoring() {
    if [ "$ENABLE_MONITORING" = "true" ]; then
        print_status "Setting up basic monitoring..."
        
        # Install htop for system monitoring
        sudo apt-get install -y htop
        
        # Create a simple monitoring script
        cat << EOF | sudo tee /opt/monitor.sh
#!/bin/bash
# Simple monitoring script
echo "=== System Status ==="
echo "Date: \$(date)"
echo "Uptime: \$(uptime)"
echo "Memory: \$(free -h | grep Mem)"
echo "Disk: \$(df -h / | tail -1)"
echo "=== Service Status ==="
systemctl is-active postgresql
systemctl is-active nginx
systemctl is-active $SERVICE_NAME
echo "=== Application Health ==="
curl -f http://localhost:$PORT/health 2>/dev/null || echo "Application not responding"
EOF
        
        sudo chmod +x /opt/monitor.sh
        
        # Add to crontab for periodic monitoring
        sudo crontab -l 2>/dev/null | { cat; echo "*/5 * * * * /opt/monitor.sh >> /var/log/monitor.log 2>&1"; } | sudo crontab -
        
        print_success "Basic monitoring setup completed"
    fi
}

# Function to setup backups (optional)
setup_backups() {
    if [ "$ENABLE_BACKUPS" = "true" ]; then
        print_status "Setting up automatic backups..."
        
        # Create backup directory
        sudo mkdir -p $BACKUP_DIR
        sudo chown $APP_NAME:$APP_NAME $BACKUP_DIR
        
        # Create backup script
        cat << EOF | sudo tee /opt/backup.sh
#!/bin/bash
# Backup script for Hackathon Service
BACKUP_DIR="$BACKUP_DIR"
RETENTION_DAYS=$BACKUP_RETENTION_DAYS
DATE=\$(date +%Y%m%d_%H%M%S)

# Create backup
sudo -u $APP_NAME pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > \$BACKUP_DIR/db_backup_\$DATE.sql

# Compress backup
gzip \$BACKUP_DIR/db_backup_\$DATE.sql

# Remove old backups
find \$BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +\$RETENTION_DAYS -delete

echo "Backup completed: db_backup_\$DATE.sql.gz"
EOF
        
        sudo chmod +x /opt/backup.sh
        
        # Add to crontab for daily backups
        sudo crontab -l 2>/dev/null | { cat; echo "0 2 * * * /opt/backup.sh >> /var/log/backup.log 2>&1"; } | sudo crontab -
        
        print_success "Automatic backup setup completed"
    fi
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    # Start Nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    # Start application service
    sudo systemctl start $SERVICE_NAME
    
    print_success "Services started"
}

# Function to check service status
check_service_status() {
    print_status "Checking service status..."
    
    # Check PostgreSQL
    if sudo systemctl is-active --quiet postgresql; then
        print_success "PostgreSQL is running"
    else
        print_error "PostgreSQL is not running"
        return 1
    fi
    
    # Check Nginx
    if sudo systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_error "Nginx is not running"
        return 1
    fi
    
    # Check application service
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Application service is running"
    else
        print_error "Application service is not running"
        return 1
    fi
    
    # Check if application is responding
    sleep 5
    if curl -f http://localhost:$PORT/health >/dev/null 2>&1; then
        print_success "Application is responding to health checks"
    else
        print_error "Application is not responding to health checks"
        return 1
    fi
    
    print_success "All services are running correctly"
}

# Function to show deployment summary
show_deployment_summary() {
    echo
    echo "=========================================="
    echo "           DEPLOYMENT SUMMARY"
    echo "=========================================="
    echo "Application Name: $APP_NAME"
    echo "Application Directory: $APP_DIR"
    echo "Service Name: $SERVICE_NAME"
    echo "Port: $PORT"
    echo "Domain: $DOMAIN_NAME"
    echo "Email: $EMAIL"
    echo "Conda Environment: $CONDA_ENV_NAME"
    echo "Workers: $UVICORN_WORKERS"
    echo
    echo "Service Status:"
    sudo systemctl status $SERVICE_NAME --no-pager -l
    echo
    echo "Nginx Status:"
    sudo systemctl status nginx --no-pager -l
    echo
    echo "Useful Commands:"
    echo "  View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  Stop service: sudo systemctl stop $SERVICE_NAME"
    echo "  Start service: sudo systemctl start $SERVICE_NAME"
    echo "  Check status: sudo systemctl status $SERVICE_NAME"
    echo "  Monitor system: sudo /opt/monitor.sh"
    echo
    if [ -n "$DOMAIN_NAME" ]; then
        if [[ $DOMAIN_NAME =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Your application is available at:"
            echo "  HTTP: http://$DOMAIN_NAME"
            echo "  Note: HTTPS not available for IP addresses"
        else
            echo "Your application should be available at:"
            echo "  HTTP: http://$DOMAIN_NAME"
            echo "  HTTPS: https://$DOMAIN_NAME"
        fi
    fi
    echo "=========================================="
}

# Main deployment function
main() {
    echo "Starting Hackathon Service VPS Deployment..."
    echo "=========================================="
    
    # Check if running with sudo
    if [[ $EUID -eq 0 ]]; then
        print_error "Please run this script as a regular user with sudo privileges"
        exit 1
    fi
    
    # Check system requirements
    check_system_requirements
    
    # Install system dependencies
    install_system_dependencies
    
    # Install Miniconda
    install_miniconda
    
    # Setup firewall
    setup_firewall
    
    # Setup services
    setup_postgresql
    setup_application_user
    
    # Deploy application
    deploy_application
    
    # Create systemd service
    create_systemd_service
    
    # Setup Nginx
    setup_nginx
    
    # Setup SSL (if domain and email are provided)
    if [ -n "$DOMAIN_NAME" ] && [ -n "$EMAIL" ]; then
        setup_ssl
    fi
    
    # Create environment file
    create_environment_file
    
    # Run migrations
    run_migrations
    
    # Setup monitoring (optional)
    setup_monitoring
    
    # Setup backups (optional)
    setup_backups
    
    # Start services
    start_services
    
    # Check service status
    if check_service_status; then
        print_success "Deployment completed successfully!"
        show_deployment_summary
    else
        print_error "Deployment completed with errors. Please check the logs."
        exit 1
    fi
}

# Run main function
main "$@" 