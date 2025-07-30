# Hackathon Service Deployment Guide

This guide explains how to deploy the Hackathon Service using the `deploy.sh` script with nginx auto-start functionality.

## Overview

The `deploy.sh` script provides a complete deployment solution that:

- ✅ Sets up system dependencies (Python, Docker, nginx)
- ✅ Creates a dedicated system user for the service
- ✅ Configures nginx as a reverse proxy
- ✅ Sets up systemd service for auto-start
- ✅ Configures firewall rules
- ✅ Creates backup and monitoring scripts
- ✅ Sets up log rotation

## Prerequisites

- Ubuntu/Debian server (tested on Ubuntu 20.04+)
- Root access (sudo privileges)
- Domain name pointing to your server (for SSL setup)

## Quick Start

### 1. Basic Deployment

```bash
# Clone the repository
git clone <your-repo-url>
cd hackathon-service

# Run the deployment script
sudo ./deploy.sh deploy
```

### 2. Update Domain Configuration

Edit the `deploy.sh` script and update the domain name:

```bash
# Change this line in deploy.sh
DOMAIN_NAME="your-domain.com"  # Change to your actual domain
```

### 3. Setup SSL (Optional)

After updating the domain name, run:

```bash
sudo ./deploy.sh ssl
```

## Script Options

The deployment script supports multiple operations:

```bash
# Deploy the complete service
sudo ./deploy.sh deploy

# Update the service (pull latest code and restart)
sudo ./deploy.sh update

# Restart the service
sudo ./deploy.sh restart

# Check service status
sudo ./deploy.sh status

# View service logs
sudo ./deploy.sh logs

# Create a backup
sudo ./deploy.sh backup

# Run monitoring script
sudo ./deploy.sh monitor

# Show help
./deploy.sh help
```

## What the Script Does

### 1. System Setup
- Updates system packages
- Installs Python 3, pip, and Miniconda
- Creates conda environment (hackathon-env)
- Installs uvicorn for FastAPI in conda environment
- Installs nginx web server
- Installs additional tools (curl, wget, git, unzip)

### 2. Application Setup
- Creates a dedicated user `hackathon-service`
- Sets up application directory at `/opt/hackathon-service`
- Copies all application files
- Creates logs and backups directories

### 3. Service Configuration
- Creates systemd service file for auto-start (runs uvicorn in conda environment)
- Configures nginx as reverse proxy
- Sets up firewall rules (SSH, HTTP, HTTPS)
- Creates backup and monitoring scripts
- Configures log rotation

### 4. Nginx Configuration
The script creates an nginx configuration that:
- Redirects HTTP to HTTPS
- Proxies requests to the FastAPI application
- Includes security headers
- Enables gzip compression
- Handles static files
- Provides health check endpoint

## Service Management

### Check Service Status
```bash
sudo systemctl status hackathon-service
```

### View Service Logs
```bash
sudo journalctl -u hackathon-service -f
```

### Restart Service
```bash
sudo systemctl restart hackathon-service
```

### Enable/Disable Auto-start
```bash
# Enable auto-start
sudo systemctl enable hackathon-service

# Disable auto-start
sudo systemctl disable hackathon-service
```

## Monitoring and Maintenance

### Automatic Monitoring
The script creates a monitoring script at `/opt/hackathon-service/monitor.sh` that shows:
- Service status
- Docker container status
- Nginx status
- Application health
- System resources (disk, memory)
- Recent logs

### Backup System
The script creates a backup script at `/opt/hackathon-service/backup.sh` that:
- Creates compressed backups
- Excludes logs and temporary files
- Keeps only the last 7 backups
- Automatically cleans old backups

### Log Rotation
Logs are automatically rotated daily and kept for 7 days.

## Configuration Files

### Nginx Configuration
- Location: `/etc/nginx/sites-available/hackathon-service`
- Enabled at: `/etc/nginx/sites-enabled/hackathon-service`

### Systemd Service
- Location: `/etc/systemd/system/hackathon-service.service`

### Application Directory
- Location: `/opt/hackathon-service/`
- User: `hackathon-service`
- Group: `hackathon-service`

## Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status hackathon-service

# View detailed logs
sudo journalctl -u hackathon-service -f

# Check conda environment and Python processes
ps aux | grep -E "(uvicorn|conda.*hackathon-env)" | grep -v grep

# Test conda environment manually
/opt/miniconda3/bin/conda run -n hackathon-env uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Nginx Issues
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx status
sudo systemctl status nginx

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Port Conflicts
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Check what's using port 80
sudo lsof -i :80
```

### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Test SSL configuration
sudo nginx -t
```

## Security Considerations

1. **Firewall**: The script configures UFW firewall to allow only necessary ports
2. **User Isolation**: The service runs under a dedicated user account
3. **Security Headers**: Nginx is configured with security headers
4. **SSL**: HTTPS redirection is configured (requires SSL certificates)

## Performance Optimization

The deployment includes several performance optimizations:

1. **Gzip Compression**: Enabled for text-based content
2. **Proxy Caching**: Configured for better performance
3. **Connection Keep-alive**: Enabled for persistent connections
4. **Worker Processes**: FastAPI runs with multiple workers

## Environment Variables

Make sure to configure the following environment variables in your `.env` file:

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Backup and Recovery

### Manual Backup
```bash
sudo /opt/hackathon-service/backup.sh
```

### Restore from Backup
```bash
# Stop the service
sudo systemctl stop hackathon-service

# Extract backup
sudo tar -xzf /opt/hackathon-service/backups/hackathon_backup_YYYYMMDD_HHMMSS.tar.gz -C /opt/hackathon-service/

# Restart the service
sudo systemctl start hackathon-service
```

## Support

If you encounter issues:

1. Check the service logs: `sudo journalctl -u hackathon-service -f`
2. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Run the monitoring script: `sudo /opt/hackathon-service/monitor.sh`
4. Verify system resources: `htop`, `df -h`, `free -h`

## License

This deployment script is provided as-is for the Hackathon Service project. 