#!/usr/bin/env python3
"""
Production Server for TikTok Downloader
"""

# EVENTLET MONKEY PATCHING MUST BE FIRST!
import eventlet
eventlet.monkey_patch()

import os
from app import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting TikTok Downloader in PRODUCTION mode...")
    print(f"🌐 Server: http://{host}:{port}")
    print("🔧 Using eventlet for WebSocket support")
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        log_output=False,
        use_reloader=False
    )