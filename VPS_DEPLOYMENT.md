# VPS Deployment Guide for Hackathon Service

This guide will help you deploy the Hackathon Service API on your VPS with comprehensive logging and process management.

## Prerequisites

- Ubuntu/Debian VPS with root access
- At least 1GB RAM
- Python 3.8+ installed
- PostgreSQL database (can be on the same server or remote)

## Quick Deployment

### 1. Upload Files to VPS

First, upload your project files to the VPS:

```bash
# On your local machine, upload the project
scp -r . root@your-vps-ip:/root/hackathon-service/
```

### 2. Run Deployment Script

SSH into your VPS and run the deployment script:

```bash
ssh root@your-vps-ip
cd /root/hackathon-service
chmod +x deploy.sh
./deploy.sh
```

## Manual Deployment

If you prefer manual setup:

### 1. Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nginx curl wget git
```

### 2. Set Up Application

```bash
# Create application directory
mkdir -p /root/hackathon-service
cd /root/hackathon-service

# Copy your project files here
# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file with your database configuration:

```bash
cat > .env << 'EOF'
DATABASE_URL=postgresql://username:password@localhost:5432/hackathondb
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
EOF
```

### 4. Set Up Systemd Service

```bash
# Copy the service file
cp hackathon-service.service /etc/systemd/system/

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable hackathon-service
```

### 5. Configure Nginx (Optional)

```bash
# Create Nginx configuration
cat > /etc/nginx/sites-available/hackathon-service << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/hackathon-service /etc/nginx/sites-enabled/
systemctl restart nginx
```

## Service Management

### Using the Service Script

```bash
# Start the service
./hackathon-service.sh start

# Stop the service
./hackathon-service.sh stop

# Restart the service
./hackathon-service.sh restart

# Check status
./hackathon-service.sh status

# View logs
./hackathon-service.sh logs
./hackathon-service.sh logs api
./hackathon-service.sh logs error
```

### Using Systemd

```bash
# Start service
systemctl start hackathon-service

# Stop service
systemctl stop hackathon-service

# Restart service
systemctl restart hackathon-service

# Check status
systemctl status hackathon-service

# View logs
journalctl -u hackathon-service -f
```

## Logging

The service creates comprehensive logs in the `logs/` directory:

- `hackathon_service.log` - General application logs
- `hackathon_service_errors.log` - Error logs only
- `api_requests.log` - All API request logs with timing
- `uvicorn.log` - Uvicorn server logs

### Log Rotation

Logs are automatically rotated when they reach 10MB, keeping 5 backup files.

### Viewing Logs

```bash
# View real-time logs
tail -f logs/hackathon_service.log

# View API requests
tail -f logs/api_requests.log

# View errors
tail -f logs/hackathon_service_errors.log

# View uvicorn logs
tail -f logs/uvicorn.log
```

## Environment Variables

You can customize the service behavior with environment variables:

```bash
export PORT=9000
export HOST=0.0.0.0
export WORKERS=4
export ENVIRONMENT=production
./hackathon-service.sh start
```

## Monitoring

### Health Check

The service provides a health check endpoint:

```bash
curl http://your-vps-ip:8000/health
```

### API Documentation

Access the interactive API documentation:

```
http://your-vps-ip:8000/docs
```

### Process Monitoring

```bash
# Check if service is running
ps aux | grep uvicorn

# Check port usage
netstat -tlnp | grep 8000

# Check system resources
htop
```

## Troubleshooting

### Service Won't Start

1. Check logs:
```bash
journalctl -u hackathon-service -n 50
```

2. Check if port is in use:
```bash
netstat -tlnp | grep 8000
```

3. Check Python environment:
```bash
source venv/bin/activate
python -c "import app.main"
```

### Database Connection Issues

1. Verify database is running:
```bash
systemctl status postgresql
```

2. Test database connection:
```bash
psql -h localhost -U username -d hackathondb
```

3. Check database URL in `.env` file

### Permission Issues

```bash
# Fix ownership
chown -R root:root /root/hackathon-service

# Fix permissions
chmod +x hackathon-service.sh
chmod 755 /root/hackathon-service
```

### Firewall Issues

```bash
# Allow port 8000
ufw allow 8000/tcp

# Check firewall status
ufw status
```

## Security Considerations

1. **Change default passwords** in database configuration
2. **Use HTTPS** in production (set up SSL certificates)
3. **Configure firewall** to only allow necessary ports
4. **Regular updates** of system packages
5. **Monitor logs** for suspicious activity

## Backup

### Database Backup

```bash
# Create backup
pg_dump hackathondb > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql hackathondb < backup_file.sql
```

### Application Backup

```bash
# Backup application files
tar -czf hackathon-service-backup-$(date +%Y%m%d).tar.gz /root/hackathon-service/

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz /root/hackathon-service/logs/
```

## Performance Tuning

### Increase Workers

For better performance, increase the number of workers:

```bash
export WORKERS=8
./hackathon-service.sh restart
```

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX idx_export_data_date ON export_data(date);
CREATE INDEX idx_export_data_country ON export_data(country);
```

### System Optimization

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf
```

## Support

If you encounter issues:

1. Check the logs first
2. Verify all dependencies are installed
3. Ensure database is accessible
4. Check firewall and network configuration
5. Verify Python environment is correct

The service includes comprehensive logging to help diagnose any issues. 