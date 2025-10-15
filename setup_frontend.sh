#!/bin/bash
# Setup script for STEEL frontend

set -e

echo "🔧 Setting up STEEL frontend..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo ""

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit frontend/.env to set your API configuration:"
    echo "   - REACT_APP_API_URL (default: http://localhost:8000)"
    echo "   - REACT_APP_API_KEY (if backend requires authentication)"
    echo ""
fi

echo "✅ Frontend setup complete!"
echo ""
echo "To start the development server:"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "The app will open at http://localhost:3000"
echo "Make sure the backend is running on http://localhost:8000"
