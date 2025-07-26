# ExportCo Deployment Guide

Simple deployment guide for ExportCo API using Docker Compose.

## 🚀 **Quick Deployment**

### **Prerequisites**
- Docker and Docker Compose installed
- Existing PostgreSQL database (separate container or server)
- GitHub repository access

### **Step 1: Create Deployment Directory**
```bash
mkdir -p ~/exportco-deploy
cd ~/exportco-deploy
```

### **Step 2: Create Environment File**
```bash
cat > .env << 'EOF'
# Database Configuration (point to your existing PostgreSQL)
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=maverick1946
POSTGRES_HOST=your-postgres-container-name
POSTGRES_PORT=5432
DATABASE_URL=postgresql://maverick:maverick1946@your-postgres-container-name:5432/hackathondb

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
EOF
```

### **Step 3: Create Logs and Backups Directories**
```bash
mkdir -p logs backups
chmod 755 logs backups
```

### **Step 4: Deploy**
```bash
# Build and start the API service
docker-compose up -d --build

# Check status
docker ps

# Run database migrations
docker exec -it exportco_api alembic upgrade head
```

### **Step 5: Verify Deployment**
```bash
# Test API
curl http://localhost:8000/api/v1/

# Test documentation
curl http://localhost:8000/docs

# Check logs
docker logs exportco_api
```

## 🔧 **Configuration**

### **Environment Variables**
Update your `.env` file with your actual values:

- `POSTGRES_HOST`: Your existing PostgreSQL container name or IP
- `DATABASE_URL`: Full database connection string
- `SECRET_KEY`: Generate a secure secret key
- `OPENAI_API_KEY`: Your actual OpenAI API key

### **Network Configuration**
If your PostgreSQL is in a different Docker network:
```bash
# Connect to the same network as your PostgreSQL
docker network connect your-postgres-network exportco_api
```

## 📊 **Management Commands**

### **Start/Stop**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

### **Updates**
```bash
# Pull latest code and rebuild
docker-compose up -d --build

# Run migrations after update
docker exec -it exportco_api alembic upgrade head
```

### **Monitoring**
```bash
# View logs
docker logs -f exportco_api

# Check health
docker inspect exportco_api | grep Health -A 10

# Check resource usage
docker stats exportco_api
```

## 🆘 **Troubleshooting**

### **Database Connection Issues**
```bash
# Test database connection
docker exec -it exportco_api python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://maverick:maverick1946@your-postgres-host:5432/hackathondb')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### **Port Conflicts**
```bash
# Check what's using port 8000
sudo netstat -tlnp | grep :8000

# Change port in .env file
PORT=8001
```

### **Build Issues**
```bash
# Rebuild without cache
docker-compose build --no-cache

# Check build logs
docker-compose logs api
```

## 🎯 **Success Checklist**

- [ ] Environment file configured with correct database settings
- [ ] Docker Compose deployment successful
- [ ] Database migrations applied
- [ ] API responding at http://localhost:8000
- [ ] Documentation accessible
- [ ] Health checks passing
- [ ] Logs monitoring set up

## 📋 **Quick Reference**

**Service URL**: http://localhost:8000  
**Documentation**: http://localhost:8000/docs  
**Health Check**: http://localhost:8000/health  

**Container Name**: `exportco_api`  
**Network**: `exportco-deploy_app-network`

---

**Your ExportCo API is now deployed and ready! 🚀** 