"""Gunicorn configuration for Render deployment."""
import multiprocessing
import os

# Bind to the port Render provides
bind = f"0.0.0.0:{os.getenv('PORT', '8002')}"

# Worker configuration
workers = int(os.getenv("WEB_CONCURRENCY", 1))
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "newsbridge-api"

# Preload app for better performance
preload_app = True
