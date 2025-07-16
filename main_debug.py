#!/usr/bin/env python3
"""
Debug version of main.py for Railway deployment troubleshooting
"""
import os
import sys
import logging
from datetime import datetime
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables and system status"""
    logger.info("=== ENVIRONMENT VARIABLES ===")
    
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY", "SHOPIFY_SHOP_URL", "SHOPIFY_ACCESS_TOKEN"]
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"✓ {var}: {'*' * min(len(value), 20)}...")
        else:
            logger.error(f"✗ {var}: NOT SET")
    
    # Check PORT variable
    port = os.environ.get("PORT")
    logger.info(f"PORT: {port}")
    
    # System information
    logger.info("=== SYSTEM INFORMATION ===")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # List files in current directory
    try:
        files = os.listdir('.')
        logger.info(f"Files in current directory: {files[:10]}...")  # Show first 10 files
    except Exception as e:
        logger.error(f"Could not list files: {e}")

def create_simple_app():
    """Create a simple FastAPI app for debugging"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        import uvicorn
        
        app = FastAPI(title="RAG Eyeshades Debug", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {"message": "RAG Eyeshades Debug API", "status": "running", "timestamp": datetime.now().isoformat()}
        
        @app.get("/health")
        async def health_check():
            logger.info("Health check request received")
            try:
                # Basic health check
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "port": os.environ.get("PORT", "8000"),
                    "env_vars_set": {
                        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
                        "SHOPIFY_SHOP_URL": bool(os.environ.get("SHOPIFY_SHOP_URL")),
                        "SHOPIFY_ACCESS_TOKEN": bool(os.environ.get("SHOPIFY_ACCESS_TOKEN"))
                    }
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
        
        @app.post("/chat")
        async def chat_debug(request: dict):
            logger.info(f"Chat request received: {request}")
            return {
                "response": "Debug mode: Chat functionality temporarily disabled. Environment setup in progress.",
                "timestamp": datetime.now().isoformat(),
                "debug": True
            }
        
        return app, uvicorn
        
    except Exception as e:
        logger.error(f"Failed to create app: {e}")
        raise

def main():
    """Main function"""
    logger.info("=== RAG EYESHADES DEBUG MODE ===")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    
    # Check environment
    check_environment()
    
    try:
        # Create simple app
        app, uvicorn = create_simple_app()
        
        # Get port
        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Starting server on port {port}")
        
        # Start server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            access_log=True,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
