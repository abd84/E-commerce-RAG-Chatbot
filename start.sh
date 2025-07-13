#!/bin/bash

# Get the port from environment variable, default to 8000
export PORT=${PORT:-8000}
export HOST=${HOST:-0.0.0.0}

echo "Starting RAG Eyeshades Chatbot on $HOST:$PORT"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the application
exec python -m uvicorn main:app --host "$HOST" --port "$PORT" --workers 1
