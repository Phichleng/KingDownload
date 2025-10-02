#!/bin/bash

# TikTok Downloader Production Startup Script

echo "🚀 Starting TikTok Downloader in Production Mode..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set production environment variables
export DEBUG=false
export PORT=5000
export HOST=0.0.0.0

# Start the server with Gunicorn (recommended for production)
echo "🌐 Starting Gunicorn server..."
gunicorn -c gunicorn_config.py "app:app"

# Alternative: Start with eventlet directly
# echo "🌐 Starting with eventlet..."
# python server.py

# Alternative: Start with Flask development server (not recommended for production)
# echo "🌐 Starting Flask development server..."
# python app.py