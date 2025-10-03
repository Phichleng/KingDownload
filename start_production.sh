#!/bin/bash

# TikTok Downloader Production Startup Script for Render

echo "🚀 Starting TikTok Downloader in Production Mode..."
echo "🔧 Environment: $NODE_ENV"
echo "🌐 Port: $PORT"

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Start the server with Gunicorn
echo "🌐 Starting Gunicorn server with eventlet workers..."
exec gunicorn -c gunicorn_config.py "app:app"