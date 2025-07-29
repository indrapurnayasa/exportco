#!/bin/bash

# Production HTTPS Setup for Hackathon Service
# This script sets up HTTPS for production without nginx

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

print_status "Setting up Production HTTPS for Hackathon Service..."

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
print_status "Server IP: $SERVER_IP"

# Step 1: Create SSL directory and certificates
print_status "Step 1: Creating SSL certificates..."
mkdir -p ssl

# Generate self-signed certificate for production
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
    -subj "/C=ID/ST=Jakarta/L=Jakarta/O=Hackathon Service/CN=$SERVER_IP"

print_success "SSL certificates created"

# Step 2: Create production start script
print_status "Step 2: Creating production start script..."

cat > start-production.sh << 'EOF'
#!/bin/bash

# Start Hackathon Service in Production Mode
# This script starts the service with HTTPS and proper logging

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
HTTP_PORT="8000"
HTTPS_PORT="8443"
WORKERS="4"
LOG_DIR="logs"
PID_FILE_HTTP="logs/uvicorn-http.pid"
PID_FILE_HTTPS="logs/uvicorn-https.pid"

# Create logs directory
mkdir -p "$LOG_DIR"

print_status "Starting Hackathon Service in Production Mode..."

# Check and activate conda environment
if command -v conda &> /dev/null; then
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
    # Fallback to virtual environment
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

# Check if SSL files exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    print_error "SSL certificates not found. Please run setup-production-https.sh first."
    exit 1
fi

# Start HTTP service (for internal use)
print_status "Starting HTTP service on port $HTTP_PORT..."
nohup uvicorn app.main:app \
    --host "127.0.0.1" \
    --port "$HTTP_PORT" \
    --workers "$WORKERS" \
    --log-level info \
    --access-log \
    > "$LOG_DIR/uvicorn-http.log" 2>&1 &

echo $! > "$PID_FILE_HTTP"
print_success "HTTP service started with PID: $(cat $PID_FILE_HTTP)"

# Start HTTPS service (for external access)
print_status "Starting HTTPS service on port $HTTPS_PORT..."
nohup uvicorn app.main:app \
    --host "$HOST" \
    --port "$HTTPS_PORT" \
    --workers "$WORKERS" \
    --ssl-certfile ssl/cert.pem \
    --ssl-keyfile ssl/key.pem \
    --log-level info \
    --access-log \
    > "$LOG_DIR/uvicorn-https.log" 2>&1 &

echo $! > "$PID_FILE_HTTPS"
print_success "HTTPS service started with PID: $(cat $PID_FILE_HTTPS)"

# Wait a moment for services to start
sleep 5

# Check if services are running
HTTP_RUNNING=false
HTTPS_RUNNING=false

if pgrep -f "uvicorn.*127.0.0.1:$HTTP_PORT" > /dev/null; then
    HTTP_RUNNING=true
fi

if pgrep -f "uvicorn.*$HOST:$HTTPS_PORT" > /dev/null; then
    HTTPS_RUNNING=true
fi

if [ "$HTTP_RUNNING" = true ] && [ "$HTTPS_RUNNING" = true ]; then
    print_success "All services are running successfully!"
    echo ""
    echo "=== PRODUCTION ENDPOINTS ==="
    echo "HTTP (Internal):  http://127.0.0.1:$HTTP_PORT/health"
    echo "HTTPS (External): https://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip"):$HTTPS_PORT/health"
    echo "API Docs:         https://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip"):$HTTPS_PORT/docs"
    echo ""
    echo "=== FRONTEND CONFIGURATION ==="
    echo "Update your frontend to use:"
    echo "https://$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip"):$HTTPS_PORT/api/v1/export/seasonal-trend"
    echo ""
    echo "=== IMPORTANT NOTES ==="
    echo "1. This uses a self-signed certificate"
    echo "2. Accept the certificate by visiting the health endpoint"
    echo "3. Use -k flag with curl for testing"
    echo "4. Both HTTP and HTTPS are running"
    echo ""
else
    print_error "Some services failed to start"
    if [ "$HTTP_RUNNING" = false ]; then
        print_error "HTTP service failed"
    fi
    if [ "$HTTPS_RUNNING" = false ]; then
        print_error "HTTPS service failed"
    fi
    print_status "Check logs: tail -f $LOG_DIR/uvicorn-*.log"
    exit 1
fi
EOF

chmod +x start-production.sh
print_success "Production start script created"

# Step 3: Create stop script
print_status "Step 3: Creating stop script..."

cat > stop-production.sh << 'EOF'
#!/bin/bash

# Stop Hackathon Service

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

PID_FILE_HTTP="logs/uvicorn-http.pid"
PID_FILE_HTTPS="logs/uvicorn-https.pid"

print_status "Stopping Hackathon Service..."

# Stop HTTP service
if [ -f "$PID_FILE_HTTP" ]; then
    PID=$(cat "$PID_FILE_HTTP")
    if kill -0 "$PID" 2>/dev/null; then
        print_status "Stopping HTTP service (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            print_warning "HTTP service still running, force killing..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE_HTTP"
        print_success "HTTP service stopped"
    else
        print_warning "HTTP service PID not found"
        rm -f "$PID_FILE_HTTP"
    fi
fi

# Stop HTTPS service
if [ -f "$PID_FILE_HTTPS" ]; then
    PID=$(cat "$PID_FILE_HTTPS")
    if kill -0 "$PID" 2>/dev/null; then
        print_status "Stopping HTTPS service (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            print_warning "HTTPS service still running, force killing..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE_HTTPS"
        print_success "HTTPS service stopped"
    else
        print_warning "HTTPS service PID not found"
        rm -f "$PID_FILE_HTTPS"
    fi
fi

# Kill any remaining uvicorn processes
pkill -f "uvicorn.*app.main:app" || true
print_success "All services stopped"
EOF

chmod +x stop-production.sh
print_success "Production stop script created"

# Step 4: Create status script
print_status "Step 4: Creating status script..."

cat > status-production.sh << 'EOF'
#!/bin/bash

# Check Hackathon Service Status

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

PID_FILE_HTTP="logs/uvicorn-http.pid"
PID_FILE_HTTPS="logs/uvicorn-https.pid"

print_status "Checking Hackathon Service Status..."

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")

echo ""
echo "=== SERVICE STATUS ==="

# Check HTTP service
if [ -f "$PID_FILE_HTTP" ]; then
    PID=$(cat "$PID_FILE_HTTP")
    if kill -0 "$PID" 2>/dev/null; then
        print_success "HTTP Service: RUNNING (PID: $PID, Port: 8000)"
    else
        print_error "HTTP Service: NOT RUNNING (stale PID file)"
        rm -f "$PID_FILE_HTTP"
    fi
else
    if pgrep -f "uvicorn.*127.0.0.1:8000" > /dev/null; then
        print_warning "HTTP Service: RUNNING (no PID file)"
    else
        print_error "HTTP Service: NOT RUNNING"
    fi
fi

# Check HTTPS service
if [ -f "$PID_FILE_HTTPS" ]; then
    PID=$(cat "$PID_FILE_HTTPS")
    if kill -0 "$PID" 2>/dev/null; then
        print_success "HTTPS Service: RUNNING (PID: $PID, Port: 8443)"
    else
        print_error "HTTPS Service: NOT RUNNING (stale PID file)"
        rm -f "$PID_FILE_HTTPS"
    fi
else
    if pgrep -f "uvicorn.*0.0.0.0:8443" > /dev/null; then
        print_warning "HTTPS Service: RUNNING (no PID file)"
    else
        print_error "HTTPS Service: NOT RUNNING"
    fi
fi

echo ""
echo "=== ENDPOINTS ==="
echo "HTTP (Internal):  http://127.0.0.1:8000/health"
echo "HTTPS (External): https://$SERVER_IP:8443/health"
echo "API Docs:         https://$SERVER_IP:8443/docs"
echo ""

echo "=== TESTING COMMANDS ==="
echo "Test HTTP:   curl http://127.0.0.1:8000/health"
echo "Test HTTPS:  curl -k https://$SERVER_IP:8443/health"
echo ""

echo "=== LOG FILES ==="
echo "HTTP Logs:   tail -f logs/uvicorn-http.log"
echo "HTTPS Logs:  tail -f logs/uvicorn-https.log"
echo ""
EOF

chmod +x status-production.sh
print_success "Production status script created"

# Step 5: Configure firewall
print_status "Step 5: Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 8000
sudo ufw allow 8443
sudo ufw --force enable
print_success "Firewall configured"

# Step 6: Create systemd service
print_status "Step 6: Creating systemd service..."

sudo tee /etc/systemd/system/hackathon-service.service << EOF
[Unit]
Description=Hackathon Service
After=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start-production.sh
ExecStop=$(pwd)/stop-production.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable hackathon-service
print_success "Systemd service created and enabled"

print_success "Production HTTPS setup completed!"
echo ""
echo "=== YOUR PRODUCTION ENDPOINTS ==="
echo "HTTP (Internal):  http://127.0.0.1:8000/health"
echo "HTTPS (External): https://$SERVER_IP:8443/health"
echo "API Docs:         https://$SERVER_IP:8443/docs"
echo ""
echo "=== USAGE COMMANDS ==="
echo "Start:     ./start-production.sh"
echo "Stop:      ./stop-production.sh"
echo "Status:    ./status-production.sh"
echo "Restart:   ./stop-production.sh && ./start-production.sh"
echo ""
echo "=== SYSTEMD COMMANDS ==="
echo "Start:     sudo systemctl start hackathon-service"
echo "Stop:      sudo systemctl stop hackathon-service"
echo "Status:    sudo systemctl status hackathon-service"
echo "Restart:   sudo systemctl restart hackathon-service"
echo ""
echo "=== FRONTEND CONFIGURATION ==="
echo "Update your frontend to use:"
echo "https://$SERVER_IP:8443/api/v1/export/seasonal-trend"
echo ""
echo "=== IMPORTANT NOTES ==="
echo "1. This uses a self-signed certificate"
echo "2. Accept the certificate by visiting the health endpoint"
echo "3. Use -k flag with curl for testing"
echo "4. Both HTTP and HTTPS are running"
echo "5. Service will auto-start on boot"
echo ""