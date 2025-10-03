# Gunicorn configuration file for QuMail production deployment

import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WEB_CONCURRENCY', '2'))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, with up to 50 random jitter
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "qumail"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/tmp/gunicorn.pid"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None