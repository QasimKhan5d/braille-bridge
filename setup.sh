#!/bin/bash

echo "🚀 Setting up Braille Bridge Development Environment"
echo "=================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup Backend
echo ""
echo "🔧 Setting up Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your configuration"
fi

cd ..

# Setup Frontend
echo ""
echo "🔧 Setting up Frontend..."
cd frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "1. Backend: cd backend && source venv/bin/activate && python app/run.py"
echo "2. Frontend: cd frontend && npm run dev"
echo ""
echo "For more information, see the README files in each directory."
