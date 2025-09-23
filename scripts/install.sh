#!/bin/bash

# SloorJuke Installation Script
# This script sets up the virtual environment and installs dependencies

set -e  # Exit on any error

echo "🎵 Setting up SloorJuke..."

# Install frontend dependencies and build
echo "🌐 Installing frontend dependencies and building production site..."
cd examples/example-frontend
npm install
npm run build
cd ../../

echo ""
echo "🎉 Installation complete!"

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