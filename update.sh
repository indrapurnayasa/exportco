#!/bin/bash

# Hackathon Service Update Script
# This script updates the application code without full redeployment

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

# Default values
APP_NAME=${APP_NAME:-"hackathon-service"}
APP_DIR=${APP_DIR:-"/opt/$APP_NAME"}
SERVICE_NAME="${APP_NAME}.service"
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

# Function to backup current application
backup_current_app() {
    print_status "Creating backup of current application..."
    
    BACKUP_DIR="/opt/backups"
    sudo mkdir -p $BACKUP_DIR
    DATE=$(date +%Y%m%d_%H%M%S)
    
    if [ -d "$APP_DIR" ]; then
        sudo tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt $APP_NAME
        print_success "Backup created: app_backup_$DATE.tar.gz"
    else
        print_warning "Application directory not found, skipping backup"
    fi
}

# Function to update application code
update_application() {
    print_status "Updating application code..."
    
    # Stop the service
    sudo systemctl stop $SERVICE_NAME
    
    # Backup current application
    backup_current_app
    
    # Copy new application files
    sudo cp -r . $APP_DIR/
    sudo chown -R $APP_NAME:$APP_NAME $APP_DIR
    
    # Update Python dependencies
    sudo -u $APP_NAME $APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin/pip install --upgrade pip
    sudo -u $APP_NAME $APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin/pip install -r $APP_DIR/requirements.txt
    
    print_success "Application code updated"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    cd $APP_DIR
    sudo -u $APP_NAME $APP_DIR/miniconda/envs/$CONDA_ENV_NAME/bin/alembic upgrade head
    
    print_success "Database migrations completed"
}

# Function to restart services
restart_services() {
    print_status "Restarting services..."
    
    # Restart application service
    sudo systemctl restart $SERVICE_NAME
    
    # Wait a moment for the service to start
    sleep 5
    
    print_success "Services restarted"
}

# Function to check service status
check_service_status() {
    print_status "Checking service status..."
    
    # Check if application service is running
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Application service is running"
    else
        print_error "Application service is not running"
        return 1
    fi
    
    # Check if application is responding
    sleep 5
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Application is responding to health checks"
    else
        print_error "Application is not responding to health checks"
        return 1
    fi
    
    print_success "Application is running correctly"
}

# Function to show update summary
show_update_summary() {
    echo
    echo "=========================================="
    echo "           UPDATE SUMMARY"
    echo "=========================================="
    echo "Application Name: $APP_NAME"
    echo "Application Directory: $APP_DIR"
    echo "Service Name: $SERVICE_NAME"
    echo "Conda Environment: $CONDA_ENV_NAME"
    echo
    echo "Service Status:"
    sudo systemctl status $SERVICE_NAME --no-pager -l
    echo
    echo "Useful Commands:"
    echo "  View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  Check status: sudo systemctl status $SERVICE_NAME"
    echo
    echo "=========================================="
}

# Main update function
main() {
    echo "Starting Hackathon Service Update..."
    echo "=========================================="
    
    # Check if running with sudo
    if [[ $EUID -eq 0 ]]; then
        print_error "Please run this script as a regular user with sudo privileges"
        exit 1
    fi
    
    # Update application
    update_application
    
    # Run migrations
    run_migrations
    
    # Restart services
    restart_services
    
    # Check service status
    if check_service_status; then
        print_success "Update completed successfully!"
        show_update_summary
    else
        print_error "Update completed with errors. Please check the logs."
        exit 1
    fi
}

# Run main function
main "$@" 