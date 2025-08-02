# Hackathon Service VPS Deployment Guide

This guide provides comprehensive instructions for deploying the Hackathon Service FastAPI application on a VPS with HTTPS support, automatic restart capabilities, and monitoring.

## Prerequisites

### VPS Requirements
- **OS**: Ubuntu 20.04 LTS or later (recommended)
- **RAM**: Minimum 1GB (2GB+ recommended)
- **Storage**: Minimum 5GB free space
- **CPU**: 1+ cores
- **Network**: Public IP address with ports 80 and 443 accessible

### Domain Requirements (for HTTPS)
- A registered domain name pointing to your VPS IP address
- DNS A record configured for your domain
- **Note**: HTTPS is not available for IP-only access (SSL certificates require domain names)

## Quick Start

### 1. Prepare Your VPS

Connect to your VPS via SSH and ensure you have a user with sudo privileges:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Create a new user (optional but recommended)
sudo adduser deploy
sudo usermod -aG sudo deploy
```

### 2. Configure Deployment Settings

Edit the `deploy.config` file with your specific settings:

```bash
# Edit the configuration file
nano deploy.config
```

**Required Settings:**
- `DOMAIN_NAME`: Your domain name (e.g., "api.yourdomain.com") or IP address
- `EMAIL`: Your email for SSL certificate notifications (only needed for domain-based HTTPS)

**Optional Settings:**
- `CONFIGURE_FIREWALL`: Set to "true" to enable UFW firewall
- `ENABLE_MONITORING`: Set to "true" for basic system monitoring
- `ENABLE_BACKUPS`: Set to "true" for automatic database backups

### 3. Run the Deployment Script

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

The script will:
- ✅ Check system requirements
- ✅ Install all dependencies (Python, PostgreSQL, Nginx, Miniconda)
- ✅ Configure firewall (if enabled)
- ✅ Set up database and user
- ✅ Deploy application code with conda environment
- ✅ Create systemd service for automatic restart
- ✅ Configure Nginx with HTTPS support
- ✅ Set up SSL certificate (if domain provided)
- ✅ Run database migrations
- ✅ Start all services
- ✅ Verify deployment

## Detailed Configuration

### Environment Variables

The deployment script creates a `.env` file with the following variables:

```env
# Database settings
POSTGRES_DB=hackathondb
POSTGRES_USER=maverick
POSTGRES_PASSWORD=Hackathon2025
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Production settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=1

# Cache settings
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# Query limits
MAX_QUERY_LIMIT=1000
QUERY_TIMEOUT=8

# Logging
LOG_LEVEL=INFO
```

### Conda Environment

The application uses a conda environment named `hackathon-env` with:
- **Python 3.11**: Latest stable Python version
- **Isolated Dependencies**: All packages installed in the conda environment
- **Easy Management**: Simple environment activation and package management

### Service Configuration

The application runs as a systemd service with the following features:

- **Automatic Restart**: Service restarts automatically if it crashes
- **Start on Boot**: Service starts automatically when the server boots
- **Security**: Runs as a dedicated user with limited privileges
- **Logging**: All logs are captured by systemd journal
- **Conda Integration**: Uses conda environment for Python execution

### Nginx Configuration

Nginx is configured with:
- **HTTPS Redirect**: All HTTP traffic is redirected to HTTPS (for domains only)
- **SSL/TLS**: Automatic SSL certificate management with Let's Encrypt (domains only)
- **Security Headers**: XSS protection, frame options, content security policy
- **Proxy Settings**: Proper headers for FastAPI behind proxy
- **Health Check**: Dedicated endpoint for health monitoring

## Post-Deployment

### Verify Deployment

Check if all services are running:

```bash
# Check application service
sudo systemctl status hackathon-service

# Check Nginx
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql
```

### Access Your Application

- **Local**: `http://localhost:8000`
- **External HTTP**: `http://your-domain.com` or `http://your-ip-address`
- **External HTTPS**: `https://your-domain.com` (only for domains, not IP addresses)

### Health Check

Test the application health endpoint:

```bash
curl http://your-domain.com/health
# or for IP access
curl http://your-ip-address/health
```

Expected response: `{"status": "healthy"}`

## Management Commands

### Service Management

```bash
# View service status
sudo systemctl status hackathon-service

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

### Logs

```bash
# View application logs
sudo journalctl -u hackathon-service -f

# View recent logs
sudo journalctl -u hackathon-service --since "1 hour ago"

# View error logs
sudo journalctl -u hackathon-service -p err
```

### Database Management

```bash
# Connect to database
sudo -u postgres psql hackathondb

# Run migrations
cd /opt/hackathon-service
sudo -u hackathon-service miniconda/envs/hackathon-env/bin/alembic upgrade head

# Create new migration
sudo -u hackathon-service miniconda/envs/hackathon-env/bin/alembic revision --autogenerate -m "description"
```

### Conda Environment Management

```bash
# Activate conda environment
source /opt/hackathon-service/miniconda/bin/activate hackathon-env

# Install new packages
pip install package-name

# Update requirements
pip install -r requirements.txt

# List installed packages
pip list
```

### SSL Certificate Management (Domain Only)

```bash
# Renew SSL certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

## Updates

### Application Updates

Use the update script for code updates:

```bash
# Make update script executable
chmod +x update.sh

# Run update
./update.sh
```

The update script will:
- ✅ Backup current application
- ✅ Update application code
- ✅ Update Python dependencies in conda environment
- ✅ Run database migrations
- ✅ Restart services
- ✅ Verify deployment

### Manual Updates

For manual updates:

```bash
# Stop service
sudo systemctl stop hackathon-service

# Update code
sudo cp -r . /opt/hackathon-service/
sudo chown -R hackathon-service:hackathon-service /opt/hackathon-service/

# Update dependencies
sudo -u hackathon-service /opt/hackathon-service/miniconda/envs/hackathon-env/bin/pip install -r /opt/hackathon-service/requirements.txt

# Run migrations
cd /opt/hackathon-service
sudo -u hackathon-service miniconda/envs/hackathon-env/bin/alembic upgrade head

# Start service
sudo systemctl start hackathon-service
```

## Monitoring

### System Monitoring

If monitoring is enabled, check system status:

```bash
# Run monitoring script
sudo /opt/monitor.sh

# View monitoring logs
sudo tail -f /var/log/monitor.log
```

### Application Monitoring

Monitor application performance:

```bash
# Check application response time
curl -w "@-" -o /dev/null -s "http://your-domain.com/health" <<'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check service logs
sudo journalctl -u hackathon-service -n 50

# Check if port is in use
sudo netstat -tlnp | grep :8000

# Check file permissions
sudo ls -la /opt/hackathon-service/

# Check conda environment
sudo -u hackathon-service /opt/hackathon-service/miniconda/envs/hackathon-env/bin/python --version
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connection
sudo -u postgres psql -c "\l"

# Check user permissions
sudo -u postgres psql -c "\du"
```

#### 3. SSL Certificate Issues (Domain Only)

```bash
# Check certificate status
sudo certbot certificates

# Test SSL configuration
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

#### 4. Conda Environment Issues

```bash
# Check conda installation
sudo -u hackathon-service /opt/hackathon-service/miniconda/bin/conda --version

# List conda environments
sudo -u hackathon-service /opt/hackathon-service/miniconda/bin/conda env list

# Recreate environment if needed
sudo -u hackathon-service /opt/hackathon-service/miniconda/bin/conda env remove -n hackathon-env
sudo -u hackathon-service /opt/hackathon-service/miniconda/bin/conda create -n hackathon-env python=3.11 -y
```

#### 5. Memory Issues

```bash
# Check memory usage
free -h

# Check swap
swapon --show

# Check process memory usage
ps aux --sort=-%mem | head -10
```

### Performance Optimization

#### 1. Adjust Uvicorn Workers

Edit the systemd service file:

```bash
sudo nano /etc/systemd/system/hackathon-service.service
```

Change the `--workers` parameter based on your CPU cores:
- 1-2 cores: `--workers 2`
- 4+ cores: `--workers 4`

#### 2. Database Optimization

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Check current settings
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;
```

#### 3. Nginx Optimization

Edit Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/hackathon-service
```

Add performance settings:

```nginx
# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

# Increase buffer sizes
proxy_buffer_size 128k;
proxy_buffers 4 256k;
proxy_busy_buffers_size 256k;
```

## Security Considerations

### Firewall Configuration

The deployment script can configure UFW firewall with:
- SSH access (port 22)
- HTTP access (port 80)
- HTTPS access (port 443)

### SSL/TLS Security (Domain Only)

- Automatic SSL certificate renewal
- HTTP to HTTPS redirect
- Security headers enabled
- HSTS (HTTP Strict Transport Security)

### Application Security

- Dedicated service user
- Limited file system access
- No root privileges
- Secure environment variables

## Backup and Recovery

### Database Backups

If backups are enabled, they are stored in `/opt/backups/` with:
- Daily automatic backups
- 7-day retention (configurable)
- Compressed format (.sql.gz)

### Manual Backup

```bash
# Create database backup
sudo -u postgres pg_dump hackathondb > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
sudo -u postgres psql hackathondb < backup_file.sql
```

### Application Backup

```bash
# Backup application files
sudo tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt hackathon-service

# Restore application
sudo tar -xzf app_backup_file.tar.gz -C /opt/
sudo chown -R hackathon-service:hackathon-service /opt/hackathon-service/
```

## IP-Only Access Limitations

### HTTPS Limitations

When using only an IP address (no domain name):
- **No HTTPS**: SSL certificates cannot be issued for IP addresses
- **HTTP Only**: Application will be accessible via HTTP only
- **Security**: Consider using a domain name for production deployments

### Workarounds

For IP-only deployments:
1. **Use HTTP**: Accept HTTP-only access for development/testing
2. **Add Domain**: Purchase a domain name and point it to your IP
3. **Self-Signed Certificate**: Use self-signed certificates (not recommended for production)

## Integration with Vercel Frontend

### CORS Configuration

The application is configured to accept requests from any origin. For production, you may want to restrict this to your Vercel domain:

```python
# In app/main.py, update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables for Frontend

Update your Vercel frontend environment variables:

```env
# For domain-based deployment
NEXT_PUBLIC_API_URL=https://your-api-domain.com

# For IP-only deployment
NEXT_PUBLIC_API_URL=http://your-ip-address
```

## Support

For issues or questions:

1. Check the logs: `sudo journalctl -u hackathon-service -f`
2. Verify configuration: `sudo systemctl status hackathon-service`
3. Test connectivity: `curl -f http://your-domain.com/health` or `curl -f http://your-ip-address/health`

## License

This deployment guide is part of the Hackathon Service project. 