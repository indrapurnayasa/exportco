# VPS/VM Deployment with HTTPS Guide

Complete guide for deploying Hackathon Service on VPS/VM with HTTPS support.

## 🚀 **Quick Start (All-in-One)**

### **Step 1: Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip software-properties-common

# Install Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install Redis (optional)
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### **Step 2: Application Deployment**
```bash
# Create application directory
sudo mkdir -p /opt/hackathon-service
sudo chown $USER:$USER /opt/hackathon-service
cd /opt/hackathon-service

# Upload your application files here
# (Use SCP, SFTP, or Git)

# Setup conda environment
conda create -n hackathon-env python=3.10 -y
conda activate hackathon-env
pip install -r requirements.txt

# Setup database
sudo -u postgres psql -c "CREATE DATABASE hackathondb;"
sudo -u postgres psql -c "CREATE USER maverick WITH PASSWORD 'Hackathon2025';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;"

# Run migrations
alembic upgrade head

# Make scripts executable
chmod +x hackathon-service.sh
```

### **Step 3: HTTPS Setup**
```bash
# Setup Direct HTTPS (No Nginx Required)
chmod +x setup-https-direct.sh
./setup-https-direct.sh

# Start HTTPS service
./start-https.sh
```

### **Step 4: Start Service**
```bash
# Start the service
./hackathon-service.sh start

# Test HTTPS endpoints (replace YOUR_SERVER_IP with your actual IP)
curl -k https://YOUR_SERVER_IP:8443/health
curl -k https://YOUR_SERVER_IP:8443/docs
```

## 🔧 **Detailed Setup**

### **Option A: Direct HTTPS (No Nginx Required) - RECOMMENDED**

This option runs HTTPS directly with FastAPI/Uvicorn without requiring nginx. Perfect for your use case!

#### **1. Setup Direct HTTPS**
```bash
# Setup HTTPS directly with FastAPI
chmod +x setup-https-direct.sh
./setup-https-direct.sh
```

#### **2. Start HTTPS Service**
```bash
# Start the HTTPS service
./start-https.sh

# Check status
./status-https.sh

# Stop service
./stop-https.sh
```

#### **3. Access Your HTTPS API**
```bash
# Test endpoints (replace YOUR_SERVER_IP with your actual IP)
curl -k https://YOUR_SERVER_IP:8443/health
curl -k https://YOUR_SERVER_IP:8443/docs
curl -k https://YOUR_SERVER_IP:8443/api/v1/users
```

#### **4. Your HTTPS Endpoints**
- **Health Check**: `https://YOUR_SERVER_IP:8443/health`
- **API Docs**: `https://YOUR_SERVER_IP:8443/docs`
- **Main API**: `https://YOUR_SERVER_IP:8443/`

### **Option B: Production HTTPS (Nginx + Let's Encrypt)**

#### **1. Domain Setup**
```bash
# Point your domain to your server's IP
# Add A record: api.yourdomain.com → YOUR_SERVER_IP
```

#### **2. Automated HTTPS Setup**
```bash
# Run the automated setup
sudo chmod +x setup-https.sh
sudo ./setup-https.sh
# Enter your domain when prompted
```

#### **3. Service Management**
```bash
# Start service
./hackathon-service.sh start

# Check status
./hackathon-service.sh status

# View logs
./hackathon-service.sh logs
```

### **Option B: Development HTTPS (Self-Signed)**

#### **1. Quick Development Setup**
```bash
# Generate self-signed certificate
chmod +x setup-https-dev.sh
./setup-https-dev.sh

# Start HTTPS service
./start-https.sh

# Test
curl -k https://localhost:8443/health
```

#### **2. Access Development HTTPS**
- **Health Check**: `https://localhost:8443/health`
- **API Docs**: `https://localhost:8443/docs`
- **Main API**: `https://localhost:8443/`

## 🌐 **Access Your API**

### **Production HTTPS (Direct FastAPI)**
```bash
# Health Check (replace YOUR_SERVER_IP with your actual IP)
curl -k https://YOUR_SERVER_IP:8443/health

# API Documentation
curl -k https://YOUR_SERVER_IP:8443/docs

# Test endpoints
curl -k https://YOUR_SERVER_IP:8443/api/v1/users
curl -k https://YOUR_SERVER_IP:8443/api/v1/komoditi
```

### **Development HTTPS (Self-Signed)**
```bash
# Health Check (ignore SSL warning)
curl -k https://localhost:8443/health

# API Documentation
curl -k https://localhost:8443/docs

# Test endpoints
curl -k https://localhost:8443/api/v1/users
```

## 🔒 **Security Configuration**

### **Firewall Setup**
```bash
# Allow necessary ports
sudo ufw allow ssh
sudo ufw allow 8443
sudo ufw allow 8000
sudo ufw --force enable
```

### **SSL Certificate Renewal**
```bash
# Manual renewal (self-signed)
./setup-https-direct.sh
```

## 📊 **Monitoring & Maintenance**

### **Service Management**
```bash
# Check service status
./hackathon-service.sh status

# View logs
./hackathon-service.sh logs
./hackathon-service.sh logs uvicorn

# Restart service
./hackathon-service.sh restart
```

### **Database Backup**
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/hackathon-service/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hackathondb_$DATE.sql"

mkdir -p "$BACKUP_DIR"
pg_dump -h localhost -U maverick hackathondb > "$BACKUP_FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "hackathondb_*.sql" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
EOF

chmod +x backup.sh

# Add to cron
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/hackathon-service/backup.sh") | crontab -
```

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Service Won't Start**
   ```bash
   # Check logs
   ./hackathon-service.sh logs
   
   # Check database connection
   psql -h localhost -U maverick -d hackathondb
   
   # Check if port is in use
   sudo netstat -tlnp | grep :8000
   ```

2. **HTTPS Not Working**
   ```bash
   # Check nginx status
   sudo systemctl status nginx
   
   # Check SSL certificate
   sudo certbot certificates
   
   # Test nginx config
   sudo nginx -t
   ```

3. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Test connection
   psql -h localhost -U maverick -d hackathondb -c "SELECT 1;"
   ```

### **Log Locations**
```bash
# Application logs
tail -f /opt/hackathon-service/logs/uvicorn.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u nginx
sudo journalctl -u postgresql
```

## 📝 **Quick Reference**

### **Essential Commands**
```bash
# Start service
./hackathon-service.sh start

# Stop service
./hackathon-service.sh stop

# Restart service
./hackathon-service.sh restart

# Check status
./hackathon-service.sh status

# View logs
./hackathon-service.sh logs
```

### **HTTPS URLs**
- **Production (IP)**: `https://YOUR_SERVER_IP/health` (use -k flag)
- **Production (Domain)**: `https://your-domain.com/health`
- **Development**: `https://localhost:8443/health`

### **Testing Commands**
```bash
# Test HTTP
curl http://localhost:8000/health

# Test HTTPS (production - IP)
curl -k https://YOUR_SERVER_IP/health

# Test HTTPS (production - domain)
curl https://your-domain.com/health

# Test HTTPS (development)
curl -k https://localhost:8443/health
```

## 🔐 **Security Checklist**

- [ ] Firewall configured (UFW)
- [ ] SSL certificate installed
- [ ] Automatic certificate renewal set up
- [ ] Database backups configured
- [ ] Service monitoring in place
- [ ] Log rotation configured
- [ ] Strong passwords set
- [ ] Regular security updates

## 📞 **Support**

For issues:
1. Check service logs: `./hackathon-service.sh logs`
2. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Verify database connection
4. Test SSL certificate: `sudo certbot certificates`
5. Check firewall rules: `sudo ufw status` 