#!/bin/bash

# Fix NTP Service Issue Script
# This script resolves common NTP service problems during VPS setup

echo "🔧 Fixing NTP Service Issue..."
echo "================================"

# Stop any running NTP processes
echo "🛑 Stopping NTP services..."
sudo systemctl stop ntp 2>/dev/null || true
sudo systemctl stop systemd-timesyncd 2>/dev/null || true

# Kill any hanging NTP processes
echo "🔪 Killing hanging NTP processes..."
sudo pkill -f ntp 2>/dev/null || true
sudo pkill -f timesyncd 2>/dev/null || true

# Remove problematic NTP files
echo "🗑️ Cleaning up NTP files..."
sudo rm -f /var/lib/ntp/ntp.drift 2>/dev/null || true
sudo rm -f /var/lib/ntp/ntp.drift.old 2>/dev/null || true
sudo rm -f /var/lib/systemd/timesync/clock 2>/dev/null || true

# Reconfigure NTP
echo "⚙️ Reconfiguring NTP..."
sudo dpkg --configure -a
sudo apt-get install -f -y

# Try to install/configure NTP properly
echo "📦 Installing NTP properly..."
sudo apt-get update
sudo apt-get install -y ntp

# Configure NTP to use systemd-timesyncd instead (more reliable)
echo "🔄 Switching to systemd-timesyncd..."
sudo systemctl stop ntp
sudo systemctl disable ntp
sudo systemctl enable systemd-timesyncd
sudo systemctl start systemd-timesyncd

# Set timezone
echo "🕐 Setting timezone..."
sudo timedatectl set-timezone UTC

# Enable and start time synchronization
echo "⏰ Enabling time synchronization..."
sudo timedatectl set-ntp true

# Check status
echo "📊 Checking time synchronization status..."
sudo timedatectl status
sudo systemctl status systemd-timesyncd

echo ""
echo "✅ NTP issue should be resolved!"
echo ""
echo "📋 Next steps:"
echo "   1. Continue with your setup script"
echo "   2. If issues persist, try: sudo systemctl daemon-reload"
echo "   3. Check time sync: timedatectl status"
echo ""
echo "🔄 If you need to restart the setup:"
echo "   ./setup-root.sh" 