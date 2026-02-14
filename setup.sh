#!/bin/bash

# Restaurant Backend - Quick Setup Script
# This script sets up the development environment

set -e

echo "🚀 Restaurant Backend - Quick Setup"
echo "===================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3.12 --version || {
    echo "❌ Python 3.12 not found. Please install Python 3.12+"
    exit 1
}

# Create virtual environment
echo "✓ Creating virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Setup environment file
echo "✓ Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ℹ️  Created .env file. Edit it with your settings:"
    echo "     - Change SECRET_KEY to a random string"
    echo "     - Update payment credentials if needed"
fi

# Create directories
echo "✓ Creating required directories..."
mkdir -p uploads logs

# Initialize database
echo "✓ Initializing database..."
python manage.py create-data

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Edit .env file with your configuration"
echo "  2. Run: python -m uvicorn app.main:app --reload"
echo "  3. Open: http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Project overview"
echo "  - API_INTEGRATION.md - API usage guide"
echo "  - DEPLOYMENT.md - Production deployment"
echo ""
echo "🐳 Or use Docker:"
echo "  docker-compose up -d"
echo ""
