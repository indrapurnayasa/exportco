# Deployment Guide for Hackathon Service

This guide will help you deploy your Hackathon Service on your VPS with IP `101.50.2.59`.

## Prerequisites

- Access to your VPS via SSH
- Sudo privileges on the VPS
- Your application files ready for deployment

## Step 1: Initial VPS Setup

### 1.1 Connect to your VPS
```bash
ssh root@101.50.2.59
# or if you have a different user
ssh your-username@101.50.2.59
```

### 1.2 Create a deployment user (recommended)
```bash
# Create a new user for deployment
sudo adduser hackathon
sudo usermod -aG sudo hackathon

# Switch to the new user
su - hackathon
```

### 1.3 Set up SSH keys (if not already done)
```bash
# On your local machine, generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy your public key to the VPS
ssh-copy-id hackathon@101.50.2.59
```

## Step 2: Upload Your Application

### 2.1 Upload files to VPS
You have several options:

**Option A: Using SCP**
```bash
# From your local machine
scp -r /path/to/your/hackathon-service hackathon@101.50.2.59:/home/hackathon/
```

**Option B: Using Git (if your code is in a repository)**
```bash
# On the VPS
cd /home/hackathon
git clone https://github.com/your-username/hackathon-service.git
```

**Option C: Using rsync**
```bash
# From your local machine
rsync -avz --exclude='venv' --exclude='__pycache__' /path/to/your/hackathon-service/ hackathon@101.50.2.59:/home/hackathon/hackathon-service/
```

## Step 3: Run the Setup Script

### 3.1 Make scripts executable and run setup
```bash
cd /home/hackathon/hackathon-service
chmod +x setup.sh
chmod +x deploy.sh

# Run the setup script
./setup.sh
```

This script will:
- Update system packages
- Install required dependencies
- Configure firewall and security
- Set up monitoring and backup scripts
- Create necessary directories

## Step 4: Deploy the Application

### 4.1 Run the deployment script
```bash
./deploy.sh
```

This script will:
- Install Python dependencies
- Set up PostgreSQL database
- Create environment configuration
- Run database migrations
- Create systemd service
- Set up Nginx reverse proxy
- Start the application

## Step 5: Verify Deployment

### 5.1 Check service status
```bash
sudo systemctl status hackathon-service
```

### 5.2 Check if the application is accessible
```bash
# Test the API
curl http://101.50.2.59/api/v1/

# Test the documentation
curl http://101.50.2.59/docs
```

### 5.3 Check logs
```bash
# View application logs
sudo journalctl -u hackathon-service -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Step 6: Configure Environment Variables

### 6.1 Update the .env file
```bash
sudo nano /opt/hackathon-service/.env
```

Make sure to update these important variables:
```env
# Update with your actual OpenAI API key
OPENAI_API_KEY=your-actual-openai-api-key-here

# Update the secret key (should be auto-generated)
SECRET_KEY=your-generated-secret-key

# Database configuration (should be correct for local PostgreSQL)
DATABASE_URL=postgresql://maverick:maverick1946@localhost:5432/hackathondb
```

### 6.2 Restart the service after changes
```bash
sudo systemctl restart hackathon-service
```

## Step 7: Set Up SSL Certificate (Recommended)

### 7.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 7.2 Obtain SSL certificate
```bash
sudo certbot --nginx -d your-domain.com
# If you don't have a domain, you can use the IP (not recommended for production)
```

## Step 8: Monitoring and Maintenance

### 8.1 Check service health
```bash
# Check if service is running
sudo systemctl is-active hackathon-service

# Check resource usage
htop

# Check disk space
df -h

# Check memory usage
free -h
```

### 8.2 View monitoring logs
```bash
# View monitoring script logs
tail -f /var/log/hackathon-service/monitor.log

# View backup logs
tail -f /var/log/cron
```

### 8.3 Manual backup
```bash
# Run backup manually
/usr/local/bin/backup-service.sh
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Service won't start
```bash
# Check service status
sudo systemctl status hackathon-service

# View detailed logs
sudo journalctl -u hackathon-service -n 50

# Check if port is in use
sudo netstat -tlnp | grep :8000
```

#### 2. Database connection issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d hackathondb -c "SELECT 1;"

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Nginx issues
```bash
# Check Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx
```

#### 4. Permission issues
```bash
# Fix file permissions
sudo chown -R hackathon:hackathon /opt/hackathon-service
sudo chmod -R 755 /opt/hackathon-service
```

## Useful Commands

### Service Management
```bash
# Start service
sudo systemctl start hackathon-service

# Stop service
sudo systemctl stop hackathon-service

# Restart service
sudo systemctl restart hackathon-service

# Enable auto-start
sudo systemctl enable hackathon-service

# Disable auto-start
sudo systemctl disable hackathon-service
```

### Log Management
```bash
# View real-time logs
sudo journalctl -u hackathon-service -f

# View last 100 lines
sudo journalctl -u hackathon-service -n 100

# View logs since yesterday
sudo journalctl -u hackathon-service --since yesterday
```

### Database Management
```bash
# Connect to database
sudo -u postgres psql -d hackathondb

# Run migrations
cd /opt/hackathon-service
source venv/bin/activate
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"
```

## Security Considerations

1. **Firewall**: UFW is configured to allow only necessary ports (22, 80, 443)
2. **Fail2ban**: Protects against brute force attacks
3. **SSH Security**: Root login disabled, password authentication disabled
4. **Regular Updates**: Keep system packages updated
5. **Backups**: Automated daily backups with 7-day retention
6. **Monitoring**: Automated service monitoring with auto-restart

## Performance Optimization

1. **Database**: PostgreSQL is configured with connection pooling
2. **Caching**: Application-level caching is enabled
3. **Rate Limiting**: API rate limiting is configured
4. **Log Rotation**: Logs are automatically rotated to prevent disk space issues

## Backup and Recovery

### Automatic Backups
- Location: `/var/backups/hackathon-service/`
- Frequency: Daily at 2 AM
- Retention: 7 days
- Includes: Application files and database dump

### Manual Backup
```bash
/usr/local/bin/backup-service.sh
```

### Restore from Backup
```bash
# Restore application files
cd /opt/hackathon-service
tar -xzf /var/backups/hackathon-service/app_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore database
sudo -u postgres psql hackathondb < /var/backups/hackathon-service/db_backup_YYYYMMDD_HHMMSS.sql.gz
```

## Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u hackathon-service -f`
2. Verify configuration: Check the `.env` file and service configuration
3. Test connectivity: Use `curl` to test API endpoints
4. Check system resources: Use `htop` and `df -h`

Your service should now be accessible at:
- **Main API**: http://101.50.2.59
- **API Documentation**: http://101.50.2.59/docs
- **ReDoc Documentation**: http://101.50.2.59/redoc 