#!/bin/bash

# VPS Deployment with HTTPS Script
# Complete deployment script for Hackathon Service with HTTPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root. Run as a regular user with sudo privileges."
    exit 1
fi

print_status "Starting VPS deployment with HTTPS for Hackathon Service..."

# Get domain name
read -p "Enter your domain name (e.g., api.yourdomain.com): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    print_error "Domain name is required"
    exit 1
fi

print_status "Domain: $DOMAIN_NAME"

# Step 1: System Setup
print_status "Step 1: Setting up system..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release htop
print_success "System updated"

# Step 2: Install Python 3.10
print_status "Step 2: Installing Python 3.10..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
print_success "Python 3.10 installed"

# Step 3: Install PostgreSQL
print_status "Step 3: Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Setup database
sudo -u postgres psql -c "CREATE DATABASE hackathondb;" 2>/dev/null || print_warning "Database might already exist"
sudo -u postgres psql -c "CREATE USER maverick WITH PASSWORD 'Hackathon2025';" 2>/dev/null || print_warning "User might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER maverick CREATEDB;" 2>/dev/null || true
print_success "PostgreSQL installed and configured"

# Step 4: Install Redis
print_status "Step 4: Installing Redis..."
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
print_success "Redis installed"

# Step 5: Setup Application Directory
print_status "Step 5: Setting up application directory..."
sudo mkdir -p /opt/hackathon-service
sudo chown $USER:$USER /opt/hackathon-service
cd /opt/hackathon-service

# Check if application files are present
if [ ! -f "hackathon-service.sh" ]; then
    print_warning "Application files not found in /opt/hackathon-service"
    print_status "Please upload your application files to /opt/hackathon-service"
    print_status "You can use SCP, SFTP, or Git to upload the files"
    print_status "Example: scp -r ./hackathon-service/* user@your-server:/opt/hackathon-service/"
    exit 1
fi

print_success "Application directory ready"

# Step 6: Setup Python Environment
print_status "Step 6: Setting up Python environment..."

# Check if conda is available
if command -v conda &> /dev/null; then
    print_status "Using conda environment..."
    
    # Create conda environment if it doesn't exist
    if ! conda env list | grep -q "hackathon-env"; then
        print_status "Creating conda environment: hackathon-env"
        conda create -n hackathon-env python=3.10 -y
    fi
    
    # Activate conda environment
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate hackathon-env
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed in conda environment"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
else
    print_status "Conda not found, using virtual environment..."
    
    # Create virtual environment
    python3.10 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
fi

# Step 7: Setup Database
print_status "Step 7: Setting up database..."
if [ -f "alembic.ini" ]; then
    source venv/bin/activate 2>/dev/null || conda activate hackathon-env
    alembic upgrade head || print_warning "Database migration might have failed or already completed"
    print_success "Database setup completed"
else
    print_warning "Alembic configuration not found, skipping database setup"
fi

# Step 8: Make Scripts Executable
print_status "Step 8: Setting up scripts..."
chmod +x hackathon-service.sh
print_success "Scripts made executable"

# Step 9: Setup HTTPS Direct with FastAPI
print_status "Step 9: Setting up HTTPS directly with FastAPI..."

# Setup HTTPS directly
chmod +x setup-https-direct.sh
./setup-https-direct.sh
print_success "HTTPS setup completed"
# Step 10: Configure Firewall
print_status "Step 10: Configuring firewall..."
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow 8443
sudo ufw allow 8000
sudo ufw --force enable
print_success "Firewall configured"

# Step 11: Test Service
print_status "Step 11: Testing service..."
./hackathon-service.sh start
sleep 5

# Check if service is running
if ./hackathon-service.sh status | grep -q "running"; then
    print_success "Service started successfully"
else
    print_error "Service failed to start"
    ./hackathon-service.sh logs
    exit 1
fi

# Step 12: Create Backup Script
print_status "Step 12: Creating backup script..."
tee backup.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/hackathon-service/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hackathondb_$DATE.sql"

mkdir -p "$BACKUP_DIR"
pg_dump -h localhost -U maverick hackathondb > "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "hackathondb_*.sql" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
EOF

chmod +x backup.sh
print_success "Backup script created"



print_success "VPS deployment with HTTPS completed successfully!"
echo ""
echo "=== YOUR HTTPS ENDPOINTS ==="
echo "Health Check: https://$DOMAIN_NAME:8443/health"
echo "API Docs: https://$DOMAIN_NAME:8443/docs"
echo "Main API: https://$DOMAIN_NAME:8443/"
echo ""
echo "=== SERVICE COMMANDS ==="
echo "Start:   ./hackathon-service.sh start"
echo "Stop:    ./hackathon-service.sh stop"
echo "Restart: ./hackathon-service.sh restart"
echo "Status:  ./hackathon-service.sh status"
echo "Logs:    ./hackathon-service.sh logs"
echo ""
echo "=== TESTING COMMANDS ==="
echo "Test HTTPS: curl -k https://$DOMAIN_NAME:8443/health"
echo "Test API:   curl -k https://$DOMAIN_NAME:8443/api/v1/users"
echo ""
echo "=== SECURITY REMINDERS ==="
echo "1. Change default passwords"
echo "2. Set up monitoring"
echo "3. Regular backups: ./backup.sh"
echo "4. Check logs regularly"
echo "" 