#!/bin/bash

# Railway startup script for RAG Eyeshades Chatbot

echo "🚀 Starting RAG Eyeshades Chatbot on Railway..."

# Create necessary directories
mkdir -p logs
mkdir -p chroma_db

# Check environment variables
echo "📋 Checking environment variables..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    exit 1
fi

if [ -z "$SHOPIFY_SHOP_URL" ]; then
    echo "❌ SHOPIFY_SHOP_URL not set"
    exit 1
fi

if [ -z "$SHOPIFY_ACCESS_TOKEN" ]; then
    echo "❌ SHOPIFY_ACCESS_TOKEN not set"
    exit 1
fi

echo "✅ Environment variables configured"

# Start the application
echo "🚀 Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
