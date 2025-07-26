#!/bin/bash

# VPS Setup Script for Hackathon Service (Root Version)
# For VPS IP: 101.50.2.59

set -e

echo "🔧 VPS Setup Script for Hackathon Service (Root Version)"
echo "========================================================"

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt install -y \
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
timedatectl set-timezone UTC

# Configure NTP
echo "⏰ Configuring NTP..."
systemctl enable ntp
systemctl start ntp

# Set up firewall
echo "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
echo "🛡️ Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Create fail2ban jail for SSH
tee /etc/fail2ban/jail.local > /dev/null << EOF
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

systemctl restart fail2ban

# Create application user
echo "👤 Creating application user..."
useradd -m -s /bin/bash hackathon || echo "User hackathon already exists"
usermod -aG sudo hackathon

# Set up SSH key authentication (if you have SSH keys)
echo "🔑 Setting up SSH security..."
if [ -f /root/.ssh/id_rsa.pub ]; then
    mkdir -p /home/hackathon/.ssh
    cp /root/.ssh/id_rsa.pub /home/hackathon/.ssh/authorized_keys
    chown -R hackathon:hackathon /home/hackathon/.ssh
    chmod 700 /home/hackathon/.ssh
    chmod 600 /home/hackathon/.ssh/authorized_keys
    echo "✅ SSH key copied to hackathon user"
else
    echo "⚠️  No SSH public key found. Please set up SSH keys for secure access."
fi

# Configure SSH security
echo "🔒 Configuring SSH security..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
tee -a /etc/ssh/sshd_config > /dev/null << EOF

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

systemctl restart ssh

# Set up log rotation
echo "📋 Setting up log rotation..."
tee /etc/logrotate.d/hackathon-service > /dev/null << EOF
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
mkdir -p /opt/hackathon-service
mkdir -p /var/log/hackathon-service
mkdir -p /var/backups/hackathon-service
chown hackathon:hackathon /opt/hackathon-service
chown hackathon:hackathon /var/log/hackathon-service
chown hackathon:hackathon /var/backups/hackathon-service

# Set up monitoring script
echo "📊 Setting up basic monitoring..."
tee /usr/local/bin/monitor-service.sh > /dev/null << 'EOF'
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

chmod +x /usr/local/bin/monitor-service.sh

# Add monitoring to crontab for hackathon user
(crontab -u hackathon -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-service.sh") | crontab -u hackathon -

# Create backup script
echo "💾 Setting up backup script..."
tee /usr/local/bin/backup-service.sh > /dev/null << 'EOF'
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

chmod +x /usr/local/bin/backup-service.sh

# Add backup to crontab for hackathon user (daily at 2 AM)
(crontab -u hackathon -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-service.sh") | crontab -u hackathon -

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
echo "   1. Switch to hackathon user: su - hackathon"
echo "   2. Run the deployment script: ./deploy-github.sh"
echo "   3. Test SSH access with the new configuration"
echo "   4. Monitor the system logs"
echo "   5. Configure SSL certificate for HTTPS (recommended)"
echo ""
echo "⚠️  Important security notes:"
echo "   - SSH root login is disabled"
echo "   - Password authentication is disabled"
echo "   - Only SSH key authentication is allowed"
echo "   - Make sure you have SSH keys set up before disconnecting"
echo ""
echo "👤 Switch to hackathon user:"
echo "   su - hackathon" 