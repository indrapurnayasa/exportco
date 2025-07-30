#!/bin/bash

echo "🚀 Starting ExportCo deployment with fixed database configuration..."

# Navigate to deployment directory
cd ~/exportco-deploy

# Create .env file with correct configuration
echo "📝 Creating .env file with correct database settings..."
cat > .env << 'EOF'
# Database Configuration (Updated for your PostgreSQL container)
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=Hackathon2025
POSTGRES_HOST=hackathon-bi
POSTGRES_PORT=5432
DATABASE_URL=postgresql://maverick:Hackathon2025@hackathon-bi:5432/hackathondb

# API Configuration
PORT=8000
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration
OPENAI_API_KEY=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
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Application Configuration
PROJECT_NAME=ExportCo API
VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
EOF

# Create logs and backups directories
echo "📁 Creating directories..."
mkdir -p logs backups
chmod 755 logs backups

# Connect API container to bridge network (same as PostgreSQL)
echo "🔗 Connecting to bridge network..."
docker network connect bridge exportco_api 2>/dev/null || true

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start the API service
echo "🔧 Building and starting API service..."
docker-compose up -d --build

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker exec -it exportco_api alembic upgrade head

# Check status
echo "✅ Checking deployment status..."
docker ps

# Test connection
echo "🧪 Testing database connection..."
docker exec -it exportco_api python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://maverick:Hackathon2025@hackathon-bi:5432/hackathondb')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"

echo "🎉 Deployment complete!"
echo "🌐 API: http://101.50.2.59:8000"
echo "📚 Docs: http://101.50.2.59:8000/docs"
echo "🔍 Logs: docker logs -f exportco_api" 