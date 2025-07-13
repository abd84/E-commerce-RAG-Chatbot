"""
Setup and Installation Script for RAG Eyeshades Chatbot

This script handles the initial setup, configuration, and testing
of the RAG chatbot system for eyewear e-commerce.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def print_banner():
    """Print the setup banner"""
    print("""
🤖 RAG Eyeshades Chatbot Setup
==============================

Setting up your intelligent eyewear shopping assistant...
""")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3.8, 0):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "chroma_db",
        "data",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Created necessary directories")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        # Copy example to .env
        with open(env_example, 'r') as source:
            content = source.read()
        
        with open(env_file, 'w') as target:
            target.write(content)
        
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys and configuration")
    elif env_file.exists():
        print("✅ Environment file already exists")
    else:
        print("❌ No .env.example file found")

def check_api_keys():
    """Check if required API keys are configured"""
    required_vars = [
        "OPENAI_API_KEY",
        "SHOPIFY_SHOP_URL",
        "SHOPIFY_ACCESS_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing or placeholder values for: {', '.join(missing_vars)}")
        print("   Please update your .env file with actual values")
        return False
    
    print("✅ All required API keys are configured")
    return True

async def test_connections():
    """Test API connections"""
    print("🔗 Testing API connections...")
    
    try:
        # Test OpenAI connection
        import openai
        from config import settings
        
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Simple test embedding
        await asyncio.to_thread(
            client.embeddings.create,
            model="text-embedding-ada-002",
            input="test"
        )
        print("✅ OpenAI API connection successful")
        
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False
    
    try:
        # Test Shopify connection
        from shopify_extractor import ShopifyExtractor
        
        extractor = ShopifyExtractor()
        if await extractor.test_connection():
            print("✅ Shopify API connection successful")
        else:
            print("❌ Shopify API connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Shopify connection error: {e}")
        return False
    
    return True

async def initialize_vector_store():
    """Initialize the vector store with domain knowledge"""
    print("🧠 Initializing vector store with domain knowledge...")
    
    try:
        from vector_store import VectorStoreManager
        
        vector_store = VectorStoreManager()
        await vector_store.initialize_domain_knowledge()
        
        stats = vector_store.get_collection_stats()
        print(f"✅ Vector store initialized with {stats['knowledge']['count']} knowledge items")
        
    except Exception as e:
        print(f"❌ Vector store initialization failed: {e}")
        return False
    
    return True

async def load_initial_data():
    """Load initial product data from Shopify"""
    print("📊 Loading initial product data...")
    
    try:
        from shopify_extractor import ShopifyExtractor
        from vector_store import VectorStoreManager
        
        # Initialize components
        extractor = ShopifyExtractor()
        vector_store = VectorStoreManager()
        
        # Fetch and process products
        products = await extractor.fetch_all_products(limit=50)  # Start with 50 products
        if not products:
            print("⚠️  No products found in Shopify store")
            return True
        
        processed_products = []
        for product in products:
            processed = extractor.process_product_for_rag(product)
            if processed:
                processed_products.append(processed)
        
        # Add to vector store
        success = await vector_store.add_products(processed_products)
        if success:
            print(f"✅ Loaded {len(processed_products)} products into vector store")
        else:
            print("❌ Failed to load products into vector store")
            return False
            
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False
    
    return True

async def test_chatbot():
    """Test the complete chatbot functionality"""
    print("🤖 Testing chatbot functionality...")
    
    try:
        from rag_chatbot import RAGChatbot
        from vector_store import VectorStoreManager
        from shopify_extractor import ShopifyExtractor
        
        # Initialize chatbot
        vector_store = VectorStoreManager()
        shopify_extractor = ShopifyExtractor()
        chatbot = RAGChatbot(vector_store, shopify_extractor)
        
        if not await chatbot.initialize():
            print("❌ Chatbot initialization failed")
            return False
        
        # Test a simple query
        response = await chatbot.process_message("Hello, I'm looking for contact lenses", "test_session")
        
        if response and response.get("message"):
            print("✅ Chatbot test successful")
            print(f"   Response: {response['message'][:100]}...")
            return True
        else:
            print("❌ Chatbot test failed - no response generated")
            return False
            
    except Exception as e:
        print(f"❌ Chatbot test failed: {e}")
        return False

def print_startup_instructions():
    """Print instructions for starting the application"""
    print("""
🚀 Setup Complete!

To start your RAG Eyeshades Chatbot:

1. Make sure your .env file has the correct API keys:
   - OPENAI_API_KEY
   - SHOPIFY_SHOP_URL  
   - SHOPIFY_ACCESS_TOKEN

2. Start the application:
   python main.py

3. Open your browser to:
   http://localhost:8000

4. API endpoints:
   - Chat: POST /chat
   - Search: POST /products/search
   - Health: GET /health
   - Stats: GET /admin/stats

5. API Documentation:
   http://localhost:8000/docs

Happy chatting! 🤖👓
""")

async def main():
    """Main setup function"""
    print_banner()
    
    # Basic setup
    check_python_version()
    create_directories()
    install_dependencies()
    setup_environment()
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check configuration
    if not check_api_keys():
        print("\n⚠️  Setup completed with warnings. Please configure your API keys before running the application.")
        return
    
    # Test connections and initialize
    connections_ok = await test_connections()
    if not connections_ok:
        print("\n❌ Setup failed due to connection issues. Please check your API keys and try again.")
        return
    
    vector_store_ok = await initialize_vector_store()
    if not vector_store_ok:
        print("\n❌ Setup failed during vector store initialization.")
        return
    
    data_loaded = await load_initial_data()
    if not data_loaded:
        print("\n⚠️  Setup completed but failed to load initial data. You can load data later.")
    
    chatbot_ok = await test_chatbot()
    if not chatbot_ok:
        print("\n❌ Setup completed but chatbot test failed.")
        return
    
    print_startup_instructions()

if __name__ == "__main__":
    asyncio.run(main())
