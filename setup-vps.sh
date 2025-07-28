#!/bin/bash

# VPS Setup Script for Hackathon Service
# This script automates the deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

print_status "Starting VPS setup for Hackathon Service..."

# Step 1: Update System
print_status "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated successfully"

# Step 2: Install Essential Packages
print_status "Step 2: Installing essential packages..."
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release htop
print_success "Essential packages installed"

# Step 3: Install Python 3.10
print_status "Step 3: Installing Python 3.10..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip

# Set Python 3.10 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
print_success "Python 3.10 installed and configured"

# Step 4: Install PostgreSQL
print_status "Step 4: Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Set up database
sudo -u postgres psql -c "CREATE DATABASE hackathondb;" || print_warning "Database might already exist"
sudo -u postgres psql -c "CREATE USER maverick WITH PASSWORD 'Hackathon2025';" || print_warning "User might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;" || true
sudo -u postgres psql -c "ALTER USER maverick CREATEDB;" || true
print_success "PostgreSQL installed and configured"

# Step 5: Install Redis (Optional)
print_status "Step 5: Installing Redis..."
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
print_success "Redis installed and configured"

# Step 6: Configure Firewall
print_status "Step 6: Configuring firewall..."
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow 8000
sudo ufw --force enable
print_success "Firewall configured"

# Step 7: Create Application Directory
print_status "Step 7: Setting up application directory..."
sudo mkdir -p /opt/hackathon-service
sudo chown $USER:$USER /opt/hackathon-service
cd /opt/hackathon-service

# Check if application files are already present
if [ ! -f "hackathon-service.sh" ]; then
    print_warning "Application files not found in /opt/hackathon-service"
    print_status "Please upload your application files to /opt/hackathon-service"
    print_status "You can use SCP, SFTP, or Git to upload the files"
    print_status "Example: scp -r ./hackathon-service/* user@your-server:/opt/hackathon-service/"
    exit 1
fi

print_success "Application directory ready"

# Step 8: Set Up Python Environment
print_status "Step 8: Setting up Python environment..."

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

# Step 9: Configure Environment
print_status "Step 9: Configuring environment..."
if [ -f "env.example" ] && [ ! -f ".env" ]; then
    cp env.example .env
    print_success "Environment file created from template"
    print_warning "Please edit .env file with your specific configuration"
    print_status "Run: nano /opt/hackathon-service/.env"
else
    print_warning "Environment file already exists or template not found"
fi

# Step 10: Set Up Database
print_status "Step 10: Setting up database..."
if [ -f "alembic.ini" ]; then
    source venv/bin/activate
    alembic upgrade head || print_warning "Database migration might have failed or already completed"
    print_success "Database setup completed"
else
    print_warning "Alembic configuration not found, skipping database setup"
fi

# Step 11: Make Scripts Executable
print_status "Step 11: Setting up scripts..."
chmod +x hackathon-service.sh
print_success "Scripts made executable"

# Step 12: Test Service
print_status "Step 12: Testing service..."
./hackathon-service.sh start
sleep 5

# Check if service is running
if ./hackathon-service.sh status | grep -q "running"; then
    print_success "Service started successfully"
    ./hackathon-service.sh stop
else
    print_error "Service failed to start"
    ./hackathon-service.sh logs
    exit 1
fi

# Step 13: Create Systemd Service
print_status "Step 13: Creating systemd service..."
sudo tee /etc/systemd/system/hackathon-service.service > /dev/null <<EOF
[Unit]
Description=Hackathon Service
After=network.target postgresql.service

[Service]
Type=forking
User=$USER
Group=$USER
WorkingDirectory=/opt/hackathon-service
Environment=PATH=/opt/hackathon-service/venv/bin
ExecStart=/opt/hackathon-service/hackathon-service.sh start
ExecStop=/opt/hackathon-service/hackathon-service.sh stop
ExecReload=/opt/hackathon-service/hackathon-service.sh restart
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable hackathon-service
print_success "Systemd service created and enabled"

# Step 14: Create Backup Script
print_status "Step 14: Creating backup script..."
tee backup.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/opt/hackathon-service/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\$BACKUP_DIR/hackathondb_\$DATE.sql"

mkdir -p "\$BACKUP_DIR"
pg_dump -h localhost -U maverick hackathondb > "\$BACKUP_FILE"

# Keep only last 7 days of backups
find "\$BACKUP_DIR" -name "hackathondb_*.sql" -mtime +7 -delete

echo "Backup created: \$BACKUP_FILE"
EOF

chmod +x backup.sh
print_success "Backup script created"

# Step 15: Final Instructions
print_success "VPS setup completed successfully!"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Edit environment file: nano /opt/hackathon-service/.env"
echo "2. Update SECRET_KEY and OPENAI_API_KEY in .env"
echo "3. Start the service: ./hackathon-service.sh start"
echo "4. Check status: ./hackathon-service.sh status"
echo "5. View logs: ./hackathon-service.sh logs"
echo ""
echo "=== SERVICE COMMANDS ==="
echo "Start:   ./hackathon-service.sh start"
echo "Stop:    ./hackathon-service.sh stop"
echo "Restart: ./hackathon-service.sh restart"
echo "Status:  ./hackathon-service.sh status"
echo "Logs:    ./hackathon-service.sh logs"
echo ""
echo "=== ACCESS YOUR APPLICATION ==="
echo "Main API: http://$(curl -s ifconfig.me):8000"
echo "API Docs: http://$(curl -s ifconfig.me):8000/docs"
echo "Health:   http://$(curl -s ifconfig.me):8000/health"
echo ""
echo "=== SECURITY REMINDERS ==="
echo "1. Change default passwords"
echo "2. Set up SSL/TLS certificates"
echo "3. Configure domain name"
echo "4. Set up monitoring"
echo "" 