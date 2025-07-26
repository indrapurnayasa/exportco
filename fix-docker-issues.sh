#!/bin/bash

echo "🔧 Fixing Docker and docker-compose issues..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run this script as root. Use a regular user with sudo privileges."
    exit 1
fi

echo "📦 Installing Docker Compose..."

# Install docker-compose using apt
sudo apt update
sudo apt install -y docker-compose

# Verify installation
echo "✅ Docker Compose version:"
docker-compose --version

echo "🔐 Fixing Docker permissions..."

# Add user to docker group
sudo usermod -aG docker $USER

# Create docker group if it doesn't exist
sudo groupadd docker 2>/dev/null || true

# Add user to docker group
sudo usermod -aG docker $USER

# Set proper permissions for docker socket
sudo chmod 666 /var/run/docker.sock

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

echo "🔄 Please log out and log back in, or run: newgrp docker"
echo "Then try the deployment commands again."

echo "📋 Quick test commands:"
echo "docker --version"
echo "docker-compose --version"
echo "docker ps" 