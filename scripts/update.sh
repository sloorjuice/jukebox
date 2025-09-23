#!/bin/bash

set -e

echo "Updating Repository..."
git pull

echo "Rebuilding Backend..."
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
