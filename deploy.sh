#!/bin/bash

# Hackathon Service Deployment Script for VPS
# This script sets up the service on a VPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_status "Starting Hackathon Service deployment..."

# Update system packages
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx curl wget git

# Create application directory
APP_DIR="/root/hackathon-service"
print_status "Setting up application directory: $APP_DIR"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Copy service files (assuming this script is run from the project directory)
print_status "Copying service files..."
cp -r . "$APP_DIR/"

# Set up Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip

# Fix distutils issue for Python 3.12+
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$python_version" == "3.12"* ]] || [[ "$python_version" == "3.13"* ]]; then
    print_warning "Detected Python $python_version, applying distutils fix..."
    pip install setuptools>=68.0.0 wheel>=0.40.0
fi

pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Set up systemd service
print_status "Setting up systemd service..."
cp hackathon-service.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable hackathon-service

# Configure firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    print_status "Configuring firewall..."
    ufw allow 8000/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
fi

# Set up Nginx reverse proxy (optional)
print_status "Setting up Nginx reverse proxy..."
cat > /etc/nginx/sites-available/hackathon-service << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/hackathon-service /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

# Make service script executable
chmod +x hackathon-service.sh

# Start the service
print_status "Starting the service..."
systemctl start hackathon-service

# Wait a moment and check status
sleep 5
if systemctl is-active --quiet hackathon-service; then
    print_success "Service started successfully!"
    print_success "Service status: $(systemctl is-active hackathon-service)"
    print_success "API available at: http://$(curl -s ifconfig.me):8000"
    print_success "Health check: http://$(curl -s ifconfig.me):8000/health"
    print_success "API docs: http://$(curl -s ifconfig.me):8000/docs"
    print_success "Logs: journalctl -u hackathon-service -f"
else
    print_error "Service failed to start"
    systemctl status hackathon-service
    exit 1
fi

print_success "Deployment completed successfully!"
print_status "Useful commands:"
echo "  systemctl start hackathon-service"
echo "  systemctl stop hackathon-service"
echo "  systemctl restart hackathon-service"
echo "  systemctl status hackathon-service"
echo "  journalctl -u hackathon-service -f"
echo "  ./hackathon-service.sh start"
echo "  ./hackathon-service.sh stop"
echo "  ./hackathon-service.sh restart" 