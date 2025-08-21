#!/bin/bash

echo "🚀 Text2Tasks - Clean Architecture Startup"
echo "==========================================="

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📋 Copying .env.example to .env..."
    cp .env.example .env
    echo "✏️  Please edit .env with your actual values (OpenAI API key, etc.)"
    echo ""
fi

# Backend Setup
echo "🔧 Setting up Backend..."
echo "========================"

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
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if database exists, if not create it
if [ ! -f app.db ]; then
    echo "🗄️  Database not found, it will be created on first run..."
fi

# Frontend Setup
echo ""
echo "⚛️  Setting up Frontend..."
echo "========================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js to run the frontend."
    echo "📥 You can download it from: https://nodejs.org/"
    echo "🔄 Starting backend only..."
    FRONTEND_AVAILABLE=false
else
    echo "📦 Node.js version:"
    node --version
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo "❌ npm is not installed."
        FRONTEND_AVAILABLE=false
    else
        echo "📦 npm version:"
        npm --version
        
        # Install frontend dependencies
        echo "📚 Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
        FRONTEND_AVAILABLE=true
    fi
fi

echo ""
echo "✅ Setup complete!"
echo "=================="
echo "🌐 Backend: http://localhost:8000"
echo "📁 Static files: http://localhost:8000/static/"
echo "🔗 API docs: http://localhost:8000/docs"

if [ "$FRONTEND_AVAILABLE" = true ]; then
    echo "⚛️  Frontend: http://localhost:5173"
fi

echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Start backend in background
echo "🚀 Starting Backend..."
python3 -m app.main &
BACKEND_PID=$!

# Start frontend if available
if [ "$FRONTEND_AVAILABLE" = true ]; then
    echo "🚀 Starting Frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

# Wait for processes
wait