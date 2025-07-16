"""
Debug version of main.py for Railway deployment
"""
import os
import sys
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("🔍 Debug: Starting application...")
print(f"🔍 Debug: Python version: {sys.version}")
print(f"🔍 Debug: PORT env var: {os.environ.get('PORT', 'Not Set')}")

# Create minimal FastAPI app
app = FastAPI(
    title="Eyeshades Chatbot - Debug Mode",
    description="Debug version to identify deployment issues",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Eyeshades Chatbot Debug Mode",
        "status": "running",
        "port": os.environ.get('PORT', 'Not Set'),
        "python_version": sys.version
    }

@app.get("/health")
async def health_check():
    try:
        env_vars = {
            "PORT": os.environ.get('PORT'),
            "OPENAI_API_KEY": "SET" if os.environ.get('OPENAI_API_KEY') else "NOT_SET",
            "SHOPIFY_SHOP_URL": "SET" if os.environ.get('SHOPIFY_SHOP_URL') else "NOT_SET",
            "SHOPIFY_ACCESS_TOKEN": "SET" if os.environ.get('SHOPIFY_ACCESS_TOKEN') else "NOT_SET"
        }
        
        return {
            "status": "healthy",
            "environment_variables": env_vars,
            "timestamp": "2025-07-16"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/chat")
async def simple_chat():
    return {
        "response": "Hello! I'm in debug mode. Environment check complete."
    }

if __name__ == "__main__":
    import uvicorn
    
    try:
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Debug: Starting server on port {port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Debug: Failed to start server: {e}")
        traceback.print_exc()
        sys.exit(1)
