#!/bin/bash

set -e

echo "Setting up SloorJuke services..."

# 1. Set the hostname to 'jukebox'
echo "Setting hostname to 'jukebox'..."
sudo hostnamectl set-hostname jukebox

# 2. Ensure /etc/hosts has an entry for jukebox.local
if ! grep -q "jukebox.local" /etc/hosts; then
  echo "127.0.0.1 jukebox.local" | sudo tee -a /etc/hosts
fi

# 3. Install and configure avahi-daemon for mDNS (.local) discovery
if ! command -v avahi-daemon &> /dev/null; then
  echo "Installing avahi-daemon for mDNS support..."
  if [[ -f /etc/debian_version ]]; then
    sudo apt-get update
    sudo apt-get install -y avahi-daemon avahi-utils
  elif [[ -f /etc/redhat-release ]]; then
    sudo yum install -y avahi avahi-tools
  else
    echo "Please install avahi-daemon manually for your distribution."
  fi
fi

# Install nginx if not present
sudo apt-get install -y nginx

# Create a config for jukebox.local
sudo tee /etc/nginx/sites-available/jukebox <<EOF
server {
    listen 80;
    server_name jukebox.local;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/jukebox /etc/nginx/sites-enabled/jukebox
sudo systemctl reload nginx

echo "Enabling and starting avahi-daemon..."
sudo systemctl enable avahi-daemon
sudo systemctl restart avahi-daemon

# 4. Set up systemd services
echo "Copying systemd service files..."
sudo cp -f services/jukebox-backend.service /etc/systemd/system/jukebox-backend.service
sudo cp -f services/jukebox-frontend.service /etc/systemd/system/jukebox-frontend.service

sudo systemctl daemon-reload
sudo systemctl start jukebox-frontend.service
sudo systemctl start jukebox-backend.service

echo "Setup complete!"
echo "Your server should now be discoverable as http://jukebox.local on your local network."