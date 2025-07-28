# VPS/VM Deployment Guide for Hackathon Service

This guide provides step-by-step instructions to deploy the Hackathon Service on a VM/VPS without nginx, using the provided shell script commands.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ VPS/VM
- Root or sudo access
- At least 2GB RAM
- At least 10GB storage
- Public IP address

## Step 1: Server Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Essential Packages
```bash
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

### 1.3 Install Python 3.10+
```bash
# Add deadsnakes PPA for Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip

# Set Python 3.10 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
sudo update-alternatives --config python3
```

### 1.4 Install PostgreSQL
```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Set up database
sudo -u postgres psql -c "CREATE DATABASE hackathondb;"
sudo -u postgres psql -c "CREATE USER maverick WITH PASSWORD 'Hackathon2025';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hackathondb TO maverick;"
sudo -u postgres psql -c "ALTER USER maverick CREATEDB;"
```

### 1.5 Install Redis (Optional, for caching)
```bash
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Step 2: Application Deployment

### 2.1 Create Application Directory
```bash
sudo mkdir -p /opt/hackathon-service
sudo chown $USER:$USER /opt/hackathon-service
cd /opt/hackathon-service
```

### 2.2 Clone or Upload Application
```bash
# Option 1: Clone from Git (if using Git)
git clone <your-repository-url> .

# Option 2: Upload files via SCP/SFTP
# Use your preferred method to upload the application files
```

### 2.3 Set Up Python Environment
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

### 2.4 Configure Environment Variables
```bash
# Copy environment template
cp env.example .env

# Edit environment file
nano .env
```

Update the `.env` file with your specific values:
```env
# Database Configuration
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
```

### 2.5 Set Up Database
```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations
alembic upgrade head
```

### 2.6 Make Script Executable
```bash
chmod +x hackathon-service.sh
```

## Step 3: Firewall Configuration

### 3.1 Configure UFW Firewall
```bash
# Install UFW if not installed
sudo apt install -y ufw

# Allow SSH
sudo ufw allow ssh

# Allow application port
sudo ufw allow 8000

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Step 4: Service Management

### 4.1 Test the Service
```bash
# Start the service
./hackathon-service.sh start

# Check status
./hackathon-service.sh status

# Check logs
./hackathon-service.sh logs
```

### 4.2 Test API Endpoints
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API docs
curl http://localhost:8000/docs
```

## Step 5: Production Deployment

### 5.1 Create Systemd Service (Optional)
Create a systemd service file for automatic startup:

```bash
sudo nano /etc/systemd/system/hackathon-service.service
```

Add the following content:
```ini
[Unit]
Description=Hackathon Service
After=network.target postgresql.service

[Service]
Type=forking
User=your-username
Group=your-username
WorkingDirectory=/opt/hackathon-service
Environment=PATH=/opt/hackathon-service/venv/bin
ExecStart=/opt/hackathon-service/hackathon-service.sh start
ExecStop=/opt/hackathon-service/hackathon-service.sh stop
ExecReload=/opt/hackathon-service/hackathon-service.sh restart
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hackathon-service
sudo systemctl start hackathon-service
```

### 5.2 Set Up Log Rotation
```bash
sudo nano /etc/logrotate.d/hackathon-service
```

Add the following content:
```
/opt/hackathon-service/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 your-username your-username
    postrotate
        systemctl reload hackathon-service
    endscript
}
```

## Step 6: Monitoring and Maintenance

### 6.1 Basic Monitoring Commands
```bash
# Check service status
./hackathon-service.sh status

# View logs
./hackathon-service.sh logs

# View specific log types
./hackathon-service.sh logs uvicorn
./hackathon-service.sh logs error

# Check system resources
htop
df -h
free -h
```

### 6.2 Database Backup
```bash
# Create backup script
nano /opt/hackathon-service/backup.sh
```

Add the following content:
```bash
#!/bin/bash
BACKUP_DIR="/opt/hackathon-service/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hackathondb_$DATE.sql"

mkdir -p "$BACKUP_DIR"
pg_dump -h localhost -U maverick hackathondb > "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "hackathondb_*.sql" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
```

Make it executable:
```bash
chmod +x /opt/hackathon-service/backup.sh
```

### 6.3 Set Up Cron Jobs
```bash
crontab -e
```

Add the following lines:
```cron
# Daily backup at 2 AM
0 2 * * * /opt/hackathon-service/backup.sh

# Log rotation (if not using systemd)
0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/hackathon-service
```

## Step 7: Security Considerations

### 7.1 Update Secret Keys
```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update the `SECRET_KEY` in your `.env` file with the generated key.

### 7.2 Secure Database
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/*/main/postgresql.conf

# Add these lines for better security:
# listen_addresses = 'localhost'
# max_connections = 100
# shared_buffers = 256MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 7.3 Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   ./hackathon-service.sh logs
   
   # Check if port is in use
   sudo netstat -tlnp | grep :8000
   
   # Kill process if needed
   sudo pkill -f uvicorn
   ```

2. **Database connection issues**
   ```bash
   # Test database connection
   psql -h localhost -U maverick -d hackathondb
   
   # Check PostgreSQL status
   sudo systemctl status postgresql
   ```

3. **Permission issues**
   ```bash
   # Fix ownership
   sudo chown -R $USER:$USER /opt/hackathon-service
   
   # Fix permissions
   chmod +x /opt/hackathon-service/hackathon-service.sh
   ```

### Service Commands Summary

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
./hackathon-service.sh logs uvicorn
./hackathon-service.sh logs error
```

## Access Your Application

Once deployed, your application will be available at:
- **Main API**: `http://your-server-ip:8000`
- **API Documentation**: `http://your-server-ip:8000/docs`
- **Health Check**: `http://your-server-ip:8000/health`

## Next Steps

1. Set up SSL/TLS certificates (recommended for production)
2. Configure domain name and DNS
3. Set up monitoring and alerting
4. Implement automated backups
5. Set up CI/CD pipeline for updates

## Support

For issues or questions:
1. Check the logs: `./hackathon-service.sh logs`
2. Verify environment variables in `.env`
3. Test database connectivity
4. Check firewall settings
5. Review system resources 