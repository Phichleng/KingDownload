# gunicorn_config.py
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = 1  # Reduced for free tier stability
worker_class = 'eventlet'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Process naming
proc_name = 'tiktok_downloader'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (optional)
# keyfile = None
# certfile = None

# Preload app for faster startup
preload_app = True

# Max requests for worker recycling (memory management)
max_requests = 1000
max_requests_jitter = 100