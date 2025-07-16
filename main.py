"""
RAG Eyeshades Chatbot - Main Application Entry Point

A sophisticated RAG chatbot for eyewear e-commerce websites built on Shopify.
Provides expert-level product recommendations and customer support for:
- Contact lenses (daily, weekly, monthly, specialty)
- Eyeglasses (frames, lenses, prescriptions)
- Sunglasses (UV protection, styles, sports)

Author: AI Assistant
Date: July 2025
"""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Import our modules
from rag_chatbot import RAGChatbot
from shopify_extractor import ShopifyExtractor
from vector_store import VectorStoreManager
from config import Settings

# Global instances
rag_chatbot = None
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global rag_chatbot
    
    logger.info("🚀 Starting RAG Eyeshades Chatbot...")
    
    try:
        # Initialize components
        logger.info("📊 Initializing vector store...")
        vector_store = VectorStoreManager()
        
        logger.info("🛒 Initializing Shopify extractor...")
        shopify_extractor = ShopifyExtractor()
        
        logger.info("🤖 Initializing RAG chatbot...")
        rag_chatbot = RAGChatbot(vector_store, shopify_extractor)
        
        # Load initial data
        logger.info("📥 Loading product data...")
        await rag_chatbot.initialize()
        
        logger.info("✅ RAG Eyeshades Chatbot initialized successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize chatbot: {e}")
        raise
    finally:
        logger.info("🔄 Shutting down RAG Eyeshades Chatbot...")

# Create FastAPI app
app = FastAPI(
    title="RAG Eyeshades Chatbot API",
    description="Intelligent chatbot for eyewear e-commerce with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
import json
cors_origins = json.loads(settings.API_CORS_ORIGINS) if settings.API_CORS_ORIGINS.startswith('[') else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API Routes
@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "RAG Eyeshades Chatbot API",
        "status": "running",
        "version": "1.0.0",
        "description": "Intelligent eyewear shopping assistant"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global rag_chatbot
    
    if rag_chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    return {
        "status": "healthy",
        "components": {
            "vector_store": "operational",
            "shopify_api": "connected",
            "openai_api": "connected"
        }
    }

@app.post("/chat")
async def chat_endpoint(request: dict):
    """Main chat endpoint for customer interactions"""
    global rag_chatbot
    
    if rag_chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        user_message = request.get("message", "")
        session_id = request.get("session_id", "default")
        
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Process the message through RAG pipeline
        response = await rag_chatbot.process_message(user_message, session_id)
        
        return {
            "response": response["message"],
            "products": response.get("recommended_products", []),
            "confidence": response.get("confidence", 0.0),
            "intent": response.get("intent", "general"),
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/products/search")
async def search_products(request: dict):
    """Search products using semantic similarity"""
    global rag_chatbot
    
    if rag_chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        query = request.get("query", "")
        limit = request.get("limit", 5)
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        products = await rag_chatbot.search_products(query, limit)
        
        return {
            "query": query,
            "products": products,
            "count": len(products)
        }
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/refresh-data")
async def refresh_data():
    """Admin endpoint to refresh product data from Shopify"""
    global rag_chatbot
    
    if rag_chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        await rag_chatbot.refresh_data()
        return {"message": "Data refreshed successfully"}
        
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh data")

@app.get("/admin/stats")
async def get_stats():
    """Admin endpoint to get chatbot statistics"""
    global rag_chatbot
    
    if rag_chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        stats = await rag_chatbot.get_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/chatbot.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=int(os.environ.get("PORT", settings.API_PORT)),
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
