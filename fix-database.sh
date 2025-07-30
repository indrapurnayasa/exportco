#!/bin/bash

# Fix Database Connection Script
# This script helps fix PostgreSQL connection issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Install PostgreSQL if not present
install_postgresql() {
    log "Checking PostgreSQL installation..."
    
    if ! command -v psql &> /dev/null; then
        log "Installing PostgreSQL..."
        apt-get update -y
        apt-get install -y postgresql postgresql-contrib
    else
        log "PostgreSQL is already installed"
    fi
}

# Start PostgreSQL service
start_postgresql() {
    log "Starting PostgreSQL service..."
    
    systemctl start postgresql
    systemctl enable postgresql
    
    # Wait for PostgreSQL to be ready
    log "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Check if PostgreSQL is running
    if systemctl is-active --quiet postgresql; then
        log "✅ PostgreSQL is running"
    else
        error "❌ PostgreSQL failed to start"
    fi
}

# Create database and user
setup_database() {
    log "Setting up database and user..."
    
    # Create database and user
    sudo -u postgres psql << EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hackathondb') THEN
        CREATE DATABASE hackathondb;
    END IF;
END
\$\$;

DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'maverick') THEN
        CREATE USER maverick WITH PASSWORD 'Hackathon2025';
    END IF;
END
\$\$;

GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;
ALTER USER maverick CREATEDB;
\q
EOF
    
    log "✅ Database setup completed"
}

# Test database connection
test_connection() {
    log "Testing database connection..."
    
    # Test connection with psql
    if PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -c "SELECT 1;" &> /dev/null; then
        log "✅ Database connection successful"
    else
        error "❌ Database connection failed"
    fi
}

# Create .env file
create_env_file() {
    log "Creating .env file..."
    
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://maverick:Hackathon2025@localhost:5432/hackathondb
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=Hackathon2025
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# API Configuration
PROJECT_NAME=Hackathon Service API
VERSION=1.0.0
DESCRIPTION=A FastAPI service for hackathon management
API_V1_STR=/api/v1

# Security Configuration
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SECRET_KEY=your-secret-key-here-change-in-production

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Logging Configuration
LOG_LEVEL=INFO
DEBUG=false
EOF

    log "✅ .env file created"
}

# Run migrations
run_migrations() {
    log "Running database migrations..."
    
    # Check if conda is available
    if command -v conda &> /dev/null; then
        conda run -n hackathon-env alembic upgrade head
    else
        # Try with system Python
        python3 -m alembic upgrade head
    fi
    
    log "✅ Migrations completed"
}

# Main function
main() {
    log "Starting database fix..."
    
    check_root
    install_postgresql
    start_postgresql
    setup_database
    test_connection
    create_env_file
    run_migrations
    
    log "✅ Database fix completed successfully!"
    log ""
    log "=== Next Steps ==="
    log "1. Update the .env file with your actual API keys"
    log "2. Restart the service: sudo systemctl restart hackathon-service"
    log "3. Check service status: sudo systemctl status hackathon-service"
}

# Run main function
main 