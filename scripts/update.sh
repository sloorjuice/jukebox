#!/bin/bash

set -e

source venv/bin/activate
pip install -r requirements.txt

sudo chown -R $(whoami) examples/example-frontend/.next
sudo usermod -a -G audio jukebox

echo "Updating Repository..."
git pull

echo "Rebuilding Frontend..."
cd examples/example-frontend/
npm install
npm run build
cd ../../

echo "Updating services..."
sudo cp -f services/jukebox-backend.service /etc/systemd/system/jukebox-backend.service
sudo cp -f services/jukebox-frontend.service /etc/systemd/system/jukebox-frontend.service

sudo systemctl daemon-reload
sudo systemctl restart jukebox-frontend.service
sudo systemctl restart jukebox-backend.service

echo "Update complete!"
