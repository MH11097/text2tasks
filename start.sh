#!/bin/bash

echo "🚀 Text2Tasks - Clean Architecture Startup"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📋 Copying .env.example to .env..."
    cp .env.example .env
    echo "✏️  Please edit .env with your actual values (OpenAI API key, etc.)"
    echo ""
fi

# Check Python version
echo "🐍 Python version:"
python3 --version

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if database exists, if not create it
if [ ! -f app.db ]; then
    echo "🗄️  Database not found, it will be created on first run..."
fi

echo ""
echo "✅ Setup complete!"
echo "🌐 Starting server at http://localhost:8000"
echo "📁 Static files served from /static/"
echo "🔗 API documentation at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python3 main.py