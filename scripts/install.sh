#!/bin/bash

# SloorJuke Installation Script
# This script sets up the virtual environment and installs dependencies

set -e  # Exit on any error

echo "🎵 Setting up SloorJuke..."

sudo chown -R $(whoami) examples/example-frontend/.next

# Install frontend dependencies and build
echo "🌐 Installing frontend dependencies and building production site..."
cd examples/example-frontend
npm install
npm run build
cd ../../

echo ""
echo "🎉 Installation complete!"

# Install VLC
echo "🎬 Installing VLC media player..."

if command -v vlc &> /dev/null; then
    echo "✅ VLC is already installed."
else
    echo "VLC is not installed. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "❌ Homebrew not found. Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
        brew install --cask vlc
    elif [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y vlc
    else
        echo "⚠️  Automatic VLC installation not supported on this OS. Please install VLC manually."
    fi
fi

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is required but not installed. Please install Python 3.7+ first."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✅ Found Python: $($PYTHON_CMD --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To get started:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the server: ./scripts/start_server.sh"
echo "   or run CLI mode: python main.py"
echo ""
echo "The API will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"