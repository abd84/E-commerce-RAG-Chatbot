#!/bin/bash

# Get the port from environment variable, default to 8000
PORT=${PORT:-8000}

# Start the application
exec gunicorn --bind "0.0.0.0:$PORT" --workers 1 --worker-class uvicorn.workers.UvicornWorker main:app
