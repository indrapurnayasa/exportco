#!/bin/bash

echo "=== Service Health Check ==="
echo "Date: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check service
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✅ $service is running${NC}"
    else
        echo -e "${RED}❌ $service is not running${NC}"
    fi
}

# Function to check port
check_port() {
    local port=$1
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✅ Port $port is listening${NC}"
    else
        echo -e "${RED}❌ Port $port is not listening${NC}"
    fi
}

# Function to test endpoint
test_endpoint() {
    local url=$1
    local description=$2
    if curl -s -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $description is accessible${NC}"
    else
        echo -e "${RED}❌ $description is not accessible${NC}"
    fi
}

echo "1. Checking Services..."
check_service "hackathon-service"
check_service "nginx"
check_service "postgresql"
echo ""

echo "2. Checking Ports..."
check_port "80"
check_port "443"
check_port "8000"
echo ""

echo "3. Testing Local Access..."
test_endpoint "http://localhost:8000/health" "Local FastAPI Health"
echo ""

echo "4. Testing External Access..."
test_endpoint "https://dev-ngurah.fun/health" "External HTTPS Health"
echo ""

echo "5. Testing Database..."
if PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -c "SELECT 1;" 2>/dev/null | grep -q "1"; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
fi
echo ""

echo "6. Checking Memory Usage..."
echo "Hackathon Service:"
systemctl show hackathon-service --property=MemoryCurrent | cut -d= -f2 | numfmt --to=iec
echo "Nginx:"
systemctl show nginx --property=MemoryCurrent | cut -d= -f2 | numfmt --to=iec
echo ""

echo "7. Recent Logs (last 5 lines)..."
echo "Hackathon Service:"
sudo journalctl -u hackathon-service -n 5 --no-pager
echo ""

echo "=== Health Check Complete ===" 