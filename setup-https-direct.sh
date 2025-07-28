#!/bin/bash

# HTTPS Setup Direct with FastAPI/Uvicorn
# This script sets up HTTPS directly without nginx

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

print_status "Setting up HTTPS directly with FastAPI..."

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)
print_status "Server IP: $SERVER_IP"

# Step 1: Create SSL directory
print_status "Step 1: Creating SSL directory..."
mkdir -p ssl
print_success "SSL directory created"

# Step 2: Generate self-signed certificate
print_status "Step 2: Generating self-signed certificate..."
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$SERVER_IP"

print_success "Self-signed certificate created"

# Step 3: Create HTTPS start script
print_status "Step 3: Creating HTTPS start script..."

cat > start-https.sh << 'EOF'
#!/bin/bash

# Start FastAPI with HTTPS
# This script starts the service with SSL certificates

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

# Configuration
HOST="0.0.0.0"
PORT="8443"
WORKERS="4"
LOG_DIR="logs"
PID_FILE="logs/uvicorn-https.pid"

# Create logs directory
mkdir -p "$LOG_DIR"

print_status "Starting FastAPI with HTTPS..."

# Check and activate conda environment
if command -v conda &> /dev/null; then
    # Check if conda environment exists
    if conda env list | grep -q "hackathon-env"; then
        print_status "Activating conda environment: hackathon-env"
        source $(conda info --base)/etc/profile.d/conda.sh
        conda activate hackathon-env
    else
        print_warning "Conda environment 'hackathon-env' not found"
        print_status "Please create the environment: conda create -n hackathon-env python=3.10"
        exit 1
    fi
else
    # Fallback to virtual environment if conda not available
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

# Check if SSL files exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    print_error "SSL certificates not found. Please run setup-https-direct.sh first."
    exit 1
fi

# Start uvicorn with SSL
print_status "Starting uvicorn with SSL on $HOST:$PORT..."
nohup uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --ssl-certfile ssl/cert.pem \
    --ssl-keyfile ssl/key.pem \
    --log-level info \
    --access-log \
    > "$LOG_DIR/uvicorn-https.log" 2>&1 &

# Save PID
echo $! > "$PID_FILE"
print_success "Service started with PID: $(cat $PID_FILE)"

# Wait a moment for service to start
sleep 3

# Check if service is running
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    print_success "Service is running successfully!"
    echo ""
    echo "=== HTTPS ENDPOINTS ==="
    echo "Health Check: https://$(curl -s ifconfig.me):$PORT/health"
    echo "API Docs: https://$(curl -s ifconfig.me):$PORT/docs"
    echo "Main API: https://$(curl -s ifconfig.me):$PORT/"
    echo ""
    echo "=== TESTING COMMANDS ==="
    echo "Test HTTPS: curl -k https://$(curl -s ifconfig.me):$PORT/health"
    echo "Test API: curl -k https://$(curl -s ifconfig.me):$PORT/api/v1/users"
    echo ""
    echo "=== IMPORTANT NOTES ==="
    echo "1. This uses a self-signed certificate"
    echo "2. Use -k flag with curl to ignore SSL warnings"
    echo "3. Browsers will show security warnings"
    echo "4. Service is running on port $PORT"
    echo ""
else
    print_error "Service failed to start. Check logs: tail -f $LOG_DIR/uvicorn-https.log"
    exit 1
fi
EOF

chmod +x start-https.sh
print_success "HTTPS start script created"

# Step 4: Create stop script
print_status "Step 4: Creating stop script..."

cat > stop-https.sh << 'EOF'
#!/bin/bash

# Stop FastAPI HTTPS service

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

PID_FILE="logs/uvicorn-https.pid"

print_status "Stopping HTTPS service..."

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        print_status "Stopping process $PID..."
        kill "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            print_warning "Process still running, force killing..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        print_success "Service stopped"
    else
        print_warning "Process $PID not found"
        rm -f "$PID_FILE"
    fi
else
    print_warning "PID file not found, trying to kill by process name..."
    pkill -f "uvicorn.*app.main:app" || true
    print_success "Service stopped"
fi
EOF

chmod +x stop-https.sh
print_success "HTTPS stop script created"

# Step 5: Create status script
print_status "Step 5: Creating status script..."

cat > status-https.sh << 'EOF'
#!/bin/bash

# Check HTTPS service status

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

PID_FILE="logs/uvicorn-https.pid"

print_status "Checking HTTPS service status..."

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        print_success "Service is running (PID: $PID)"
        echo ""
        echo "=== SERVICE INFO ==="
        echo "Port: 8443 (HTTPS)"
        echo "Health: https://$(curl -s ifconfig.me):8443/health"
        echo "Docs: https://$(curl -s ifconfig.me):8443/docs"
        echo ""
        echo "=== PROCESS INFO ==="
        ps aux | grep "uvicorn.*app.main:app" | grep -v grep || true
    else
        print_error "Service is not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
else
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        print_warning "Service is running but PID file not found"
        ps aux | grep "uvicorn.*app.main:app" | grep -v grep || true
    else
        print_error "Service is not running"
    fi
fi
EOF

chmod +x status-https.sh
print_success "HTTPS status script created"

# Step 6: Configure firewall
print_status "Step 6: Configuring firewall..."
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow 8443
sudo ufw allow 8000
sudo ufw --force enable
print_success "Firewall configured"

print_success "HTTPS setup completed!"
echo ""
echo "=== YOUR HTTPS ENDPOINTS ==="
echo "Health Check: https://$SERVER_IP:8443/health"
echo "API Docs: https://$SERVER_IP:8443/docs"
echo "Main API: https://$SERVER_IP:8443/"
echo ""
echo "=== USAGE COMMANDS ==="
echo "Start HTTPS: ./start-https.sh"
echo "Stop HTTPS: ./stop-https.sh"
echo "Status: ./status-https.sh"
echo ""
echo "=== TESTING COMMANDS ==="
echo "Test HTTPS: curl -k https://$SERVER_IP:8443/health"
echo "Test API: curl -k https://$SERVER_IP:8443/api/v1/users"
echo ""
echo "=== IMPORTANT NOTES ==="
echo "1. This uses a self-signed certificate"
echo "2. Use -k flag with curl to ignore SSL warnings"
echo "3. Browsers will show security warnings"
echo "4. Service runs on port 8443 (HTTPS)"
echo "5. No nginx required!"
echo "" 