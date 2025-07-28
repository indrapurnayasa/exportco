#!/bin/bash

# Local Database Setup Script
# This script sets up a local database for development

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

print_status "Setting up local database..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL is not installed"
    print_status "Installing PostgreSQL..."
    
    # For macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install postgresql@14
            brew services start postgresql@14
            export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"
        else
            print_error "Homebrew not found. Please install PostgreSQL manually."
            exit 1
        fi
    else
        print_error "Please install PostgreSQL manually for your system."
        exit 1
    fi
fi

# Create database and user
print_status "Creating database and user..."

# Create user if it doesn't exist
psql postgres -c "CREATE USER maverick WITH PASSWORD 'Hackathon2025';" 2>/dev/null || print_warning "User might already exist"

# Create database if it doesn't exist
psql postgres -c "CREATE DATABASE hackathondb OWNER maverick;" 2>/dev/null || print_warning "Database might already exist"

# Grant privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;" 2>/dev/null || true
psql postgres -c "ALTER USER maverick CREATEDB;" 2>/dev/null || true

print_success "Database setup completed"

# Test connection
print_status "Testing database connection..."
if psql -h localhost -U maverick -d hackathondb -c "SELECT 1;" >/dev/null 2>&1; then
    print_success "Database connection successful"
else
    print_error "Database connection failed"
    print_status "Trying to fix authentication..."
    
    # For macOS, we might need to update pg_hba.conf
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "For macOS, you may need to update PostgreSQL authentication"
        print_status "Run: brew services restart postgresql@14"
    fi
fi

# Create .env file if it doesn't exist
print_status "Creating .env file..."
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

print_success "Local database setup completed!"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Run database migrations: alembic upgrade head"
echo "2. Start the service: ./hackathon-service.sh start"
echo "3. Test the API: curl http://localhost:8000/health"
echo "" 