#!/bin/bash

# Database Configuration Fix Script
# This script helps fix database connection issues

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

print_status "Fixing database configuration..."

# Step 1: Check if PostgreSQL is running
print_status "Step 1: Checking PostgreSQL status..."
if sudo systemctl is-active --quiet postgresql; then
    print_success "PostgreSQL is running"
else
    print_error "PostgreSQL is not running. Starting it..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Step 2: Create database and user if they don't exist
print_status "Step 2: Setting up database and user..."
sudo -u postgres psql -c "CREATE DATABASE hackathondb;" 2>/dev/null || print_warning "Database might already exist"
sudo -u postgres psql -c "CREATE USER maverick WITH PASSWORD 'Hackathon2025';" 2>/dev/null || print_warning "User might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER maverick CREATEDB;" 2>/dev/null || true
print_success "Database setup completed"

# Step 3: Test database connection
print_status "Step 3: Testing database connection..."
if psql -h localhost -U maverick -d hackathondb -c "SELECT 1;" >/dev/null 2>&1; then
    print_success "Database connection successful"
else
    print_error "Database connection failed"
    print_status "Trying to fix connection issues..."
    
    # Check if password authentication is configured
    if ! grep -q "local.*all.*all.*md5" /etc/postgresql/*/main/pg_hba.conf; then
        print_status "Configuring password authentication..."
        sudo sed -i 's/local.*all.*all.*peer/local all all md5/' /etc/postgresql/*/main/pg_hba.conf
        sudo systemctl restart postgresql
        print_success "Password authentication configured"
    fi
fi

# Step 4: Create .env file if it doesn't exist
print_status "Step 4: Creating .env file..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Database Configuration (Local PostgreSQL)
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=Hackathon2025
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://maverick:Hackathon2025@localhost:5432/hackathondb

# API Configuration
PORT=8000
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration
OPENAI_API_KEY=your-actual-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Application Configuration
PROJECT_NAME=ExportCo API
VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# CORS Configuration
ALLOWED_HOSTS=["*"]

# Production settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=1
CACHE_TTL=300
CACHE_MAX_SIZE=1000
MAX_QUERY_LIMIT=10000
QUERY_TIMEOUT=30
EOF
    print_success ".env file created"
else
    print_warning ".env file already exists"
fi

# Step 5: Test Alembic connection
print_status "Step 5: Testing Alembic connection..."
if command -v conda &> /dev/null && conda env list | grep -q "hackathon-env"; then
    # Use conda environment
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate hackathon-env
    if alembic current >/dev/null 2>&1; then
        print_success "Alembic connection successful"
    else
        print_warning "Alembic connection failed, but this might be normal for a fresh database"
    fi
elif source venv/bin/activate 2>/dev/null; then
    # Fallback to virtual environment
    if alembic current >/dev/null 2>&1; then
        print_success "Alembic connection successful"
    else
        print_warning "Alembic connection failed, but this might be normal for a fresh database"
    fi
else
    print_warning "No Python environment found, skipping Alembic test"
fi

print_success "Database configuration fix completed!"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Run database migrations: alembic upgrade head"
echo "2. Test the application: ./hackathon-service.sh start"
echo "3. Check logs if needed: ./hackathon-service.sh logs"
echo ""
echo "=== TROUBLESHOOTING ==="
echo "If you still have issues:"
echo "1. Check PostgreSQL logs: sudo journalctl -u postgresql"
echo "2. Test connection: psql -h localhost -U maverick -d hackathondb"
echo "3. Check .env file: cat .env"
echo "" 