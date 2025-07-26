# Complete Step-by-Step Deployment Guide

This guide will take you from zero to a fully deployed Hackathon Service on your VPS (101.50.2.59).

## 📋 Prerequisites Checklist

- [ ] VPS with IP: 101.50.2.59
- [ ] SSH access to VPS
- [ ] GitHub account
- [ ] Your code pushed to GitHub repository
- [ ] OpenAI API key (for the application)

---

## 🚀 Step 1: Prepare Your Local Repository

### 1.1 Initialize Git and Push to GitHub

```bash
# On your local machine
cd /Users/66371/Documents/BNI/Hackathon\ BI/exportco

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Hackathon Service API"

# Add GitHub remote (replace YOUR_USERNAME with your actual GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/exportco.git

# Set main branch and push
git branch -M main
git push -u origin main
```

### 1.2 Verify GitHub Repository

1. Go to https://github.com/YOUR_USERNAME/exportco
2. Confirm your files are uploaded
3. Note your repository URL: `https://github.com/YOUR_USERNAME/exportco.git`

---

## 🔐 Step 2: Set Up VPS Access

### 2.1 Connect to Your VPS

```bash
# Connect to your VPS
ssh root@101.50.2.59

# If you get a fingerprint warning, type 'yes' to continue
```

### 2.2 Create a Deployment User (Recommended)

```bash
# Create a new user for deployment
adduser hackathon

# Add user to sudo group
usermod -aG sudo hackathon

# Switch to the new user
su - hackathon
```

---

## 🔑 Step 3: Set Up GitHub Authentication

### 3.1 Method A: Personal Access Token (Recommended)

#### Create Personal Access Token on GitHub:
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Give it a name: "VPS Deployment"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (if using GitHub Actions)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

#### Configure on VPS:
```bash
# Upload the setup script to VPS
# (You'll need to copy the github-setup.sh file to your VPS)

# Make it executable
chmod +x github-setup.sh

# Run the setup
./github-setup.sh

# Choose option 1 (Personal Access Token)
# Enter your GitHub username and the token you created
```

### 3.2 Method B: SSH Keys (Alternative)

```bash
# Generate SSH key on VPS
ssh-keygen -t rsa -b 4096 -C "vps@101.50.2.59"
# Press Enter for all prompts (use default settings)

# Display the public key
cat ~/.ssh/id_rsa.pub

# Copy this key and add it to GitHub:
# GitHub.com → Settings → SSH and GPG keys → New SSH key
# Title: "VPS 101.50.2.59"
# Paste the key and save

# Test SSH connection
ssh -T git@github.com
# You should see: "Hi username! You've successfully authenticated..."
```

---

## 🛠️ Step 4: Initial VPS Setup

### 4.1 Run System Setup Script

```bash
# Upload setup.sh to your VPS (if not already there)
# Make it executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This script will:
- Update system packages
- Install required dependencies (Python, PostgreSQL, Nginx, etc.)
- Configure firewall and security
- Set up monitoring and backup scripts
- Create necessary directories

### 4.2 Verify System Setup

```bash
# Check if required services are installed
python3 --version
postgresql --version
nginx -v
git --version

# Check if directories were created
ls -la /opt/exportco
ls -la /var/log/exportco
ls -la /var/backups/exportco
```

---

## 📥 Step 5: Clone and Deploy from GitHub

### 5.1 Clone Your Repository

```bash
# Navigate to the application directory
cd /opt/exportco

# Clone your repository
git clone https://github.com/YOUR_USERNAME/exportco.git .

# Verify the clone
ls -la
git status
```

### 5.2 Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### 5.3 Set Up Database

```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE hackathondb;
CREATE USER maverick WITH PASSWORD 'maverick1946';
GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;
ALTER USER maverick CREATEDB;
\q
EOF

# Test database connection
sudo -u postgres psql -d hackathondb -c "SELECT 1;"
```

### 5.4 Create Environment Configuration

```bash
# Create .env file
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
POSTGRES_PASSWORD=maverick1946
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://maverick:maverick1946@localhost:5432/hackathondb

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

# Set proper permissions
chmod 600 .env
```

### 5.5 Run Database Migrations

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify migrations
alembic current
```

### 5.6 Test the Application

```bash
# Test the application locally
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, test the API
curl http://localhost:8000/api/v1/
curl http://localhost:8000/docs

# Stop the test server (Ctrl+C)
```

---

## 🔧 Step 6: Create System Service

### 6.1 Create Systemd Service File

```bash
# Create the service file
sudo tee /etc/systemd/system/exportco.service > /dev/null << EOF
[Unit]
Description=Hackathon Service API
After=network.target postgresql.service

[Service]
Type=exec
User=hackathon
Group=hackathon
WorkingDirectory=/opt/exportco
Environment=PATH=/opt/exportco/venv/bin
ExecStart=/opt/exportco/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 6.2 Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable the service (start on boot)
sudo systemctl enable exportco

# Start the service
sudo systemctl start exportco

# Check service status
sudo systemctl status exportco
```

---

## 🌐 Step 7: Configure Nginx Reverse Proxy

### 7.1 Create Nginx Configuration

```bash
# Create Nginx site configuration
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
```

### 7.2 Enable Nginx Site

```bash
# Enable the site
sudo ln -sf /etc/nginx/sites-available/exportco /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx
```

---

## 🔥 Step 8: Configure Firewall

```bash
# Allow SSH
sudo ufw allow ssh

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (for future SSL)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable

# Check firewall status
sudo ufw status
```

---

## ✅ Step 9: Verify Deployment

### 9.1 Check Service Status

```bash
# Check if service is running
sudo systemctl status exportco

# Check if Nginx is running
sudo systemctl status nginx

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

### 9.2 Test the Application

```bash
# Test the API
curl http://101.50.2.59/api/v1/

# Test the documentation
curl http://101.50.2.59/docs

# Test from your local machine
curl http://101.50.2.59/api/v1/
```

### 9.3 Check Logs

```bash
# View application logs
sudo journalctl -u exportco -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# View system logs
sudo journalctl -f
```

---

## 🔧 Step 10: Final Configuration

### 10.1 Update Environment Variables

```bash
# Edit the .env file
sudo nano /opt/exportco/.env

# Update these important variables:
# - OPENAI_API_KEY=your-actual-openai-api-key
# - SECRET_KEY=your-generated-secret-key

# Restart the service after changes
sudo systemctl restart exportco
```

### 10.2 Create Update Script

```bash
# Create update script
cat > /opt/exportco/update.sh << 'EOF'
#!/bin/bash
cd /opt/exportco
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart exportco
echo "Update completed successfully!"
EOF

# Make it executable
chmod +x /opt/exportco/update.sh
```

### 10.3 Set Up Monitoring

```bash
# Check if monitoring script exists
ls -la /usr/local/bin/monitor-service.sh

# Check if backup script exists
ls -la /usr/local/bin/backup-service.sh

# View monitoring logs
tail -f /var/log/exportco/monitor.log
```

---

## 🎯 Step 11: Test Everything

### 11.1 Test All Endpoints

```bash
# Test main API
curl http://101.50.2.59/api/v1/

# Test authentication (if implemented)
curl -X POST http://101.50.2.59/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Test export endpoints
curl http://101.50.2.59/api/v1/export/seasonal-trend
curl http://101.50.2.59/api/v1/export/country-demand
```

### 11.2 Test Documentation

Open in your browser:
- **API Documentation**: http://101.50.2.59/docs
- **ReDoc**: http://101.50.2.59/redoc

### 11.3 Test from Different Locations

```bash
# Test from your local machine
curl http://101.50.2.59/api/v1/

# Test from another server
curl http://101.50.2.59/api/v1/
```

---

## 🔄 Step 12: Future Updates

### 12.1 Make Changes Locally

```bash
# On your local machine
cd /Users/66371/Documents/BNI/Hackathon\ BI/exportco

# Make your changes
# ... edit files ...

# Commit and push
git add .
git commit -m "Add new feature"
git push origin main
```

### 12.2 Deploy Updates

```bash
# SSH to VPS
ssh hackathon@101.50.2.59

# Update the application
cd /opt/exportco
./update.sh

# Or manually:
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart exportco
```

---

## 🆘 Troubleshooting

### Common Issues and Solutions

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status exportco

# View detailed logs
sudo journalctl -u exportco -n 50

# Check if port is in use
sudo netstat -tlnp | grep :8000
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d hackathondb -c "SELECT 1;"

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Nginx Issues
```bash
# Check Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx
```

#### 4. Permission Issues
```bash
# Fix file permissions
sudo chown -R hackathon:hackathon /opt/exportco
sudo chmod -R 755 /opt/exportco
```

---

## 📊 Monitoring Commands

```bash
# Check service status
sudo systemctl status exportco

# View real-time logs
sudo journalctl -u exportco -f

# Check system resources
htop
df -h
free -h

# Check network connections
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80

# Check firewall status
sudo ufw status
```

---

## 🎉 Success!

Your Hackathon Service is now deployed and running at:

- **Main API**: http://101.50.2.59
- **API Documentation**: http://101.50.2.59/docs
- **ReDoc**: http://101.50.2.59/redoc

### Quick Reference Commands:

```bash
# Check service status
sudo systemctl status exportco

# View logs
sudo journalctl -u exportco -f

# Restart service
sudo systemctl restart exportco

# Update from GitHub
cd /opt/exportco && ./update.sh

# Check system resources
htop
```

### Next Steps:

1. **Set up SSL certificate** for HTTPS
2. **Configure domain name** (optional)
3. **Set up monitoring alerts**
4. **Configure automated backups**
5. **Set up CI/CD pipeline**

---

**Congratulations! Your Hackathon Service is now live and ready to serve requests! 🚀** 