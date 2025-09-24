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
echo "Installing avahi-daemon for mDNS support..."
if [[ -f /etc/debian_version ]]; then
  sudo apt-get update
  sudo apt-get install -y avahi-daemon avahi-utils
elif [[ -f /etc/redhat-release ]]; then
  sudo yum install -y avahi avahi-tools
else
  echo "Please install avahi-daemon manually for your distribution."
fi

# Install nginx if not present
echo "Installing nginx..."
sudo apt-get install -y nginx

# Stop nginx before making changes
echo "Stopping nginx for configuration..."
sudo systemctl stop nginx

# Remove ALL default nginx configurations
echo "Removing all default nginx configurations..."
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-available/default
sudo rm -f /var/www/html/index.nginx-debian.html

# Disable any other potential default sites
sudo find /etc/nginx/sites-enabled/ -type l -delete
sudo find /etc/nginx/conf.d/ -name "*.conf" -delete

# Create a config for jukebox.local
echo "Creating nginx configuration..."
sudo tee /etc/nginx/sites-available/jukebox <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name jukebox.local localhost _;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the jukebox site
sudo ln -sf /etc/nginx/sites-available/jukebox /etc/nginx/sites-enabled/jukebox

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

# Enable and start nginx
echo "Enabling and starting nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx

echo "Enabling and starting avahi-daemon..."
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# 4. Set up systemd services
echo "Copying systemd service files..."
sudo cp -f services/jukebox-backend.service /etc/systemd/system/jukebox-backend.service
sudo cp -f services/jukebox-frontend.service /etc/systemd/system/jukebox-frontend.service

# Reload systemd and enable services for auto-start
echo "Configuring services for auto-start..."
sudo systemctl daemon-reload

# Stop services if running to restart them cleanly
sudo systemctl stop jukebox-frontend.service 2>/dev/null || true
sudo systemctl stop jukebox-backend.service 2>/dev/null || true

# Enable services to start at boot
sudo systemctl enable jukebox-frontend.service
sudo systemctl enable jukebox-backend.service

# Start services
sudo systemctl start jukebox-backend.service
sleep 3  # Give backend time to start
sudo systemctl start jukebox-frontend.service

# Wait a moment for services to initialize
sleep 5

# Check service status
echo "Checking service status..."
sudo systemctl status jukebox-frontend.service --no-pager || true
sudo systemctl status jukebox-backend.service --no-pager || true

# Verify nginx is working
echo "Verifying nginx configuration..."
sudo systemctl status nginx --no-pager || true

# Show enabled services
echo "Services enabled for auto-start:"
sudo systemctl is-enabled nginx
sudo systemctl is-enabled jukebox-frontend.service
sudo systemctl is-enabled jukebox-backend.service
sudo systemctl is-enabled avahi-daemon

echo "Setup complete!"
echo "Your server should now be discoverable as http://jukebox.local on your local network."
echo "All services are configured to start automatically on boot."
echo ""
echo "If you still see the nginx welcome page, try:"
echo "  sudo systemctl restart nginx"
echo ""
echo "To check service logs:"
echo "  sudo journalctl -u jukebox-frontend.service -f"
echo "  sudo journalctl -u jukebox-backend.service -f"
echo "  sudo journalctl -u nginx.service -f"