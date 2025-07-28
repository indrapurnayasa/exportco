# Docker Deployment Guide for ExportCo

Complete step-by-step guide to deploy your ExportCo service using Docker on VPS (101.50.2.59).

## 🐳 **Prerequisites**

- VPS with IP: 101.50.2.59
- SSH access to VPS
- Your project files ready

## 🚀 **Step-by-Step Docker Deployment**

### **Step 1: Install Docker on VPS**

```bash
# SSH to your VPS
ssh hackathon@101.50.2.59

# Update system
sudo apt update

# Install Docker
sudo apt install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker hackathon

# Log out and back in, or run:
newgrp docker

# Verify Docker installation
docker --version
docker-compose --version
```

### **Step 2: Upload Your Project**

```bash
# From your local machine, upload the project
scp -r /Users/66371/Documents/BNI/Hackathon\ BI/hackathon-service hackathon@101.50.2.59:~/exportco/

# Or use rsync (recommended)
rsync -avz --exclude='venv' --exclude='__pycache__' /Users/66371/Documents/BNI/Hackathon\ BI/hackathon-service/ hackathon@101.50.2.59:~/exportco/
```

### **Step 3: Set Up Environment Variables**

```bash
# SSH to VPS
ssh hackathon@101.50.2.59

# Navigate to project directory
cd ~/exportco

# Copy example environment file
cp env.example .env

# Edit the .env file with your actual values
nano .env
```

**Important: Update these values in .env:**
```env
# Change these values:
OPENAI_API_KEY=your-actual-openai-api-key
SECRET_KEY=your-generated-secret-key
POSTGRES_PASSWORD=your-secure-password
```

### **Step 4: Create Required Directories**

```bash
# Create logs and backups directories
mkdir -p ~/exportco/logs
mkdir -p ~/exportco/backups

# Set permissions
chmod 755 ~/exportco/logs
chmod 755 ~/exportco/backups
```

### **Step 5: Build and Deploy**

```bash
# Build and start the containers
docker-compose up --build -d

# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f
```

### **Step 6: Run Database Migrations**

```bash
# Run migrations inside the API container
docker-compose exec api alembic upgrade head

# Check migration status
docker-compose exec api alembic current
```

### **Step 7: Verify Deployment**

```bash
# Check container status
docker-compose ps

# Test the API
curl http://101.50.2.59:8000/api/v1/

# Test the documentation
curl http://101.50.2.59:8000/docs

# Check container logs
docker-compose logs api
```

## 🎯 **Your Service is Live!**

- **Main API**: http://101.50.2.59:8000
- **API Documentation**: http://101.50.2.59:8000/docs
- **ReDoc**: http://101.50.2.59:8000/redoc

## 🔧 **Docker Commands Reference**

### **Container Management**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f postgres
```

### **Database Operations**
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U maverick -d hackathondb

# Run migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "Description"

# Check migration status
docker-compose exec api alembic current
```

### **Application Operations**
```bash
# Access API container shell
docker-compose exec api bash

# Install new dependencies
docker-compose exec api pip install package-name

# Restart API only
docker-compose restart api
```

## 🔄 **Updating Your Application**

### **Method 1: Rebuild and Deploy**
```bash
# Pull latest changes (if using git)
git pull origin main

# Rebuild and restart
docker-compose up --build -d

# Run migrations if needed
docker-compose exec api alembic upgrade head
```

### **Method 2: Update Environment Variables**
```bash
# Edit .env file
nano .env

# Restart services
docker-compose restart
```

## 📊 **Monitoring and Maintenance**

### **Check System Resources**
```bash
# Check container resource usage
docker stats

# Check disk usage
docker system df

# Check logs
docker-compose logs -f
```

### **Backup Database**
```bash
# Create database backup
docker-compose exec postgres pg_dump -U maverick hackathondb > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker-compose exec -T postgres psql -U maverick hackathondb < backup_file.sql
```

### **Clean Up**
```bash
# Remove unused containers and images
docker system prune -a

# Remove unused volumes
docker volume prune
```

## 🆘 **Troubleshooting**

### **Container Won't Start**
```bash
# Check logs
docker-compose logs api

# Check if port is in use
sudo netstat -tlnp | grep :8000

# Restart Docker service
sudo systemctl restart docker
```

### **Database Connection Issues**
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test database connection
docker-compose exec api python -c "import psycopg2; psycopg2.connect('postgresql://maverick:Hackathon2025@postgres:5432/hackathondb')"
```

### **Permission Issues**
```bash
# Fix file permissions
sudo chown -R hackathon:hackathon ~/exportco
chmod 755 ~/exportco/logs ~/exportco/backups
```

## 🔒 **Security Considerations**

### **Firewall Setup**
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API
sudo ufw enable
```

### **Environment Variables**
- Never commit `.env` file to git
- Use strong passwords for database
- Generate secure SECRET_KEY
- Keep OpenAI API key secure

## 📋 **Quick Reference Commands**

```bash
# Start deployment
cd ~/exportco
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Update application
git pull && docker-compose up --build -d
```

## 🎉 **Success Checklist**

- [ ] Docker installed on VPS
- [ ] Project uploaded to VPS
- [ ] .env file configured
- [ ] Containers built and running
- [ ] Database migrations applied
- [ ] API responding at http://101.50.2.59:8000
- [ ] Documentation accessible
- [ ] Firewall configured

---

**Your ExportCo service is now deployed with Docker! 🚀**

**Benefits of Docker deployment:**
- ✅ No need to install Python/PostgreSQL/Nginx on host
- ✅ Consistent environment across deployments
- ✅ Easy updates and rollbacks
- ✅ Isolated services
- ✅ Simple scaling 