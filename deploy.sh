#!/bin/bash

# Hackathon Service Deployment Script
# For VPS IP: 101.50.2.59

set -e  # Exit on any error

echo "🚀 Starting deployment of Hackathon Service on VPS..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libpq-dev \
    python3-dev

# Ensure conda is available and environment exists
echo "🐍 Checking conda environment..."
if ! command -v conda &> /dev/null; then
    echo "❌ Conda not found. Please install miniconda first."
    exit 1
fi

# Initialize conda for this session
source ~/miniconda3/etc/profile.d/conda.sh

# Check if hackathon-env exists, create if not
if ! conda env list | grep -q "hackathon-env"; then
    echo "📦 Creating hackathon-env conda environment..."
    conda create -n hackathon-env python=3.11 -y
fi

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/exportco
sudo chown $USER:$USER /opt/exportco
cd /opt/exportco

# Clone or copy your application
echo "📋 Copying application files..."
# If you have the files locally, you can copy them here
# cp -r /path/to/your/exportco/* /opt/exportco/

# Activate conda environment
echo "🐍 Activating conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate hackathon-env

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up PostgreSQL
echo "🗄️ Setting up PostgreSQL database..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE hackathondb;
CREATE USER maverick WITH PASSWORD 'Hackathon2025';
GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;
ALTER USER maverick CREATEDB;
\q
EOF

# Create .env file
echo "⚙️ Creating environment configuration..."
cat > .env << EOF
# API Configuration
PROJECT_NAME=Hackathon Service API
VERSION=1.0.0
DESCRIPTION=A FastAPI service for hackathon management
API_V1_STR=/api/v1

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS Configuration
ALLOWED_HOSTS=["*"]

# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# PostgreSQL Database Configuration
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=Hackathon2025
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://maverick:Hackathon2025@localhost:5432/hackathondb

# Security Configuration
SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Logging Configuration
LOG_LEVEL=INFO

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

# Run database migrations
echo "🔄 Running database migrations..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate hackathon-env
alembic upgrade head

# Create systemd service file
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/exportco.service > /dev/null << EOF
[Unit]
Description=Hackathon Service API
After=network.target postgresql.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=/opt/exportco
Environment=PATH=/home/$USER/miniconda3/envs/hackathon-env/bin
ExecStart=/home/$USER/miniconda3/envs/hackathon-env/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "🚀 Starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable exportco
sudo systemctl start exportco

# Set up Nginx as reverse proxy
echo "🌐 Setting up Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/exportco > /dev/null << EOF
server {
    listen 80;
    server_name 101.50.2.59;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site and restart Nginx
sudo ln -sf /etc/nginx/sites-available/exportco /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Set up firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Check service status
echo "📊 Checking service status..."
sleep 5
sudo systemctl status exportco --no-pager

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Your service is now available at:"
echo "   - Main API: http://101.50.2.59"
echo "   - API Docs: http://101.50.2.59/docs"
echo "   - ReDoc: http://101.50.2.59/redoc"
echo ""
echo "📋 Useful commands:"
echo "   - Check service status: sudo systemctl status exportco"
echo "   - View logs: sudo journalctl -u exportco -f"
echo "   - Restart service: sudo systemctl restart exportco"
echo "   - Stop service: sudo systemctl stop exportco"
echo ""
echo "🔧 Next steps:"
echo "   1. Update the .env file with your actual OpenAI API key"
echo "   2. Configure SSL certificate for HTTPS (recommended)"
echo "   3. Set up monitoring and logging"
echo "   4. Configure backup strategy" 