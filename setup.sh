#!/bin/bash

# VPS Setup Script for Hackathon Service
# For VPS IP: 101.50.2.59

set -e

echo "🔧 VPS Setup Script for Hackathon Service"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. Use a regular user with sudo privileges."
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    zip \
    tree \
    net-tools \
    ufw \
    fail2ban \
    logrotate \
    ntp

# Configure timezone (adjust as needed)
echo "🕐 Setting timezone..."
sudo timedatectl set-timezone UTC

# Configure NTP
echo "⏰ Configuring NTP..."
sudo systemctl enable ntp
sudo systemctl start ntp

# Set up firewall
echo "🔥 Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Configure fail2ban
echo "🛡️ Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create fail2ban jail for SSH
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

sudo systemctl restart fail2ban

# Create application user (optional)
echo "👤 Creating application user..."
sudo useradd -m -s /bin/bash hackathon || echo "User hackathon already exists"
sudo usermod -aG sudo hackathon

# Set up SSH key authentication (if you have SSH keys)
echo "🔑 Setting up SSH security..."
if [ -f ~/.ssh/id_rsa.pub ]; then
    sudo mkdir -p /home/hackathon/.ssh
    sudo cp ~/.ssh/id_rsa.pub /home/hackathon/.ssh/authorized_keys
    sudo chown -R hackathon:hackathon /home/hackathon/.ssh
    sudo chmod 700 /home/hackathon/.ssh
    sudo chmod 600 /home/hackathon/.ssh/authorized_keys
    echo "✅ SSH key copied to hackathon user"
else
    echo "⚠️  No SSH public key found. Please set up SSH keys for secure access."
fi

# Configure SSH security
echo "🔒 Configuring SSH security..."
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
sudo tee -a /etc/ssh/sshd_config > /dev/null << EOF

# Security settings
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
AllowTcpForwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

sudo systemctl restart ssh

# Set up log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/hackathon-service > /dev/null << EOF
/var/log/hackathon-service/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 hackathon hackathon
    postrotate
        systemctl reload hackathon-service
    endscript
}
EOF

# Create application directories
echo "📁 Creating application directories..."
sudo mkdir -p /opt/hackathon-service
sudo mkdir -p /var/log/hackathon-service
sudo mkdir -p /var/backups/hackathon-service
sudo chown $USER:$USER /opt/hackathon-service
sudo chown $USER:$USER /var/log/hackathon-service
sudo chown $USER:$USER /var/backups/hackathon-service

# Set up monitoring script
echo "📊 Setting up basic monitoring..."
sudo tee /usr/local/bin/monitor-service.sh > /dev/null << 'EOF'
#!/bin/bash

# Basic service monitoring script
SERVICE_NAME="hackathon-service"
LOG_FILE="/var/log/hackathon-service/monitor.log"

# Check if service is running
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): Service $SERVICE_NAME is down! Attempting restart..." >> $LOG_FILE
    systemctl restart $SERVICE_NAME
    
    # Check if restart was successful
    sleep 5
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): Service $SERVICE_NAME restarted successfully" >> $LOG_FILE
    else
        echo "$(date): Failed to restart $SERVICE_NAME" >> $LOG_FILE
    fi
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage is high: ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "$(date): Memory usage is high: ${MEMORY_USAGE}%" >> $LOG_FILE
fi
EOF

sudo chmod +x /usr/local/bin/monitor-service.sh

# Add monitoring to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-service.sh") | crontab -

# Create backup script
echo "💾 Setting up backup script..."
sudo tee /usr/local/bin/backup-service.sh > /dev/null << 'EOF'
#!/bin/bash

# Backup script for hackathon service
BACKUP_DIR="/var/backups/hackathon-service"
DATE=$(date +%Y%m%d_%H%M%S)
SERVICE_DIR="/opt/hackathon-service"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C $SERVICE_DIR .

# Backup database (if PostgreSQL is running)
if systemctl is-active --quiet postgresql; then
    sudo -u postgres pg_dump hackathondb > $BACKUP_DIR/db_backup_$DATE.sql
    gzip $BACKUP_DIR/db_backup_$DATE.sql
fi

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

sudo chmod +x /usr/local/bin/backup-service.sh

# Add backup to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-service.sh") | crontab -

echo ""
echo "✅ VPS setup completed successfully!"
echo ""
echo "📋 Summary of what was configured:"
echo "   - System packages updated"
echo "   - Firewall (UFW) configured"
echo "   - Fail2ban installed and configured"
echo "   - SSH security hardened"
echo "   - Application directories created"
echo "   - Monitoring script installed"
echo "   - Backup script installed"
echo ""
echo "🔧 Next steps:"
echo "   1. Run the deployment script: ./deploy.sh"
echo "   2. Test SSH access with the new configuration"
echo "   3. Monitor the system logs"
echo "   4. Set up SSL certificate for HTTPS"
echo ""
echo "⚠️  Important security notes:"
echo "   - SSH root login is disabled"
echo "   - Password authentication is disabled"
echo "   - Only SSH key authentication is allowed"
echo "   - Make sure you have SSH keys set up before disconnecting" 