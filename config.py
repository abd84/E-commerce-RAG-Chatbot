"""
Configuration Management for RAG Eyeshades Chatbot

This module handles all configuration settings, environment variables,
and application constants for the eyewear chatbot system.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="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", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=500, env="OPENAI_MAX_TOKENS")

    # Shopify Configuration
    SHOPIFY_SHOP_URL: str = Field(default="9159b3-2.myshopify.com", env="SHOPIFY_SHOP_URL")
    SHOPIFY_ACCESS_TOKEN: str = Field(default="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", env="SHOPIFY_ACCESS_TOKEN")
    SHOPIFY_API_VERSION: str = Field(default="2023-10", env="SHOPIFY_API_VERSION")
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_CREDENTIALS_FILE: str = Field(default="credentials.json", env="GOOGLE_SHEETS_CREDENTIALS_FILE")
    GOOGLE_SHEETS_PRODUCT_SHEET_ID: Optional[str] = Field(default=None, env="GOOGLE_SHEETS_PRODUCT_SHEET_ID")
    GOOGLE_SHEETS_FAQ_SHEET_ID: Optional[str] = Field(default=None, env="GOOGLE_SHEETS_FAQ_SHEET_ID")
    GOOGLE_SHEETS_KNOWLEDGE_SHEET_ID: Optional[str] = Field(default=None, env="GOOGLE_SHEETS_KNOWLEDGE_SHEET_ID")
    GOOGLE_SERVICE_ACCOUNT_FILE: str = Field(default="credentials/service-account.json", env="GOOGLE_SERVICE_ACCOUNT_FILE")
    GOOGLE_SHEETS_CONTACT_LENSES_SHEET_ID: str = Field(default="", env="GOOGLE_SHEETS_CONTACT_LENSES_SHEET_ID")
    GOOGLE_SHEETS_SUNGLASSES_SHEET_ID: str = Field(default="", env="GOOGLE_SHEETS_SUNGLASSES_SHEET_ID")
    GOOGLE_SHEETS_EYEGLASSES_SHEET_ID: str = Field(default="", env="GOOGLE_SHEETS_EYEGLASSES_SHEET_ID")
    GOOGLE_SHEETS_FAQ_SHEET_ID: str = Field(default="", env="GOOGLE_SHEETS_FAQ_SHEET_ID")

    # ChromaDB Configuration
    CHROMA_DB_PATH: str = Field(default="./chroma_db", env="CHROMA_DB_PATH")
    CHROMA_COLLECTION_PRODUCTS: str = Field(default="eyewear_products", env="CHROMA_COLLECTION_PRODUCTS")
    CHROMA_COLLECTION_KNOWLEDGE: str = Field(default="eyewear_knowledge", env="CHROMA_COLLECTION_KNOWLEDGE")
    CHROMA_COLLECTION_FAQ: str = Field(default="eyewear_faq", env="CHROMA_COLLECTION_FAQ")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="PORT")  # Railway uses PORT env var
    API_RELOAD: bool = Field(default=False, env="API_RELOAD")  # Disable reload in production
    API_SECRET_KEY: str = Field(default="your-secret-key", env="API_SECRET_KEY")
    API_CORS_ORIGINS: str = Field(default='["*"]', env="API_CORS_ORIGINS")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/chatbot.log", env="LOG_FILE")
    
    # RAG Configuration
    MAX_CONTEXT_LENGTH: int = Field(default=4000, env="MAX_CONTEXT_LENGTH")
    TOP_K_RESULTS: int = Field(default=5, env="TOP_K_RESULTS")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    CONVERSATION_MEMORY_LENGTH: int = Field(default=10, env="CONVERSATION_MEMORY_LENGTH")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Store Information
    STORE_NAME: str = Field(default="Eyeshades", env="STORE_NAME")
    STORE_WEBSITE: str = Field(default="https://eyeshades.pk", env="STORE_WEBSITE")
    STORE_EMAIL: str = Field(default="eyeshades.pk@gmail.com", env="STORE_EMAIL")
    STORE_PHONE: str = Field(default="+92 320 4510453", env="STORE_PHONE")
    STORE_ADDRESS: str = Field(default="1: Johar Town Phase 1, G1 market, opp. INT School of Choueifat, Phase 1 Johar Town, Lahore, 54615, Pakistan; 2: Shah Alam market, Shop 4, Sufi M. Aslam Optical Market, 5/6 Shah Alam Gate, Sector A1 Sector A 1 Lahore, Punjab 54100", env="STORE_ADDRESS")
    STORE_BUSINESS_HOURS: str = Field(default="Mon-Fri: 10AM-10PM, Sat: 10AM-9PM, Sun: Closed", env="STORE_BUSINESS_HOURS")
    STORE_DESCRIPTION: str = Field(default="We are one of the leading retailers in the optical industry, serving for over 22 years. Explore our extensive range of branded and premium-quality eyewear, including contact lenses, sunglasses, and eyeglasses for men, women and kids. Our comprehensive online store caters to all your eyewear needs with a best-price guarantee. Ensuring affordability is our top priority, and we offer nationwide delivery across Pakistan, with free shipping to all cities on orders above 3000.", env="STORE_DESCRIPTION")
    STORE_SPECIALTIES: str = Field(default="Contact Lenses, Prescription Eyeglasses, Designer Sunglasses, Eye Exams", env="STORE_SPECIALTIES")
    STORE_RETURN_POLICY: str = Field(default="7 days return and refund policy. For more info visit https://eyeshades.pk/policies/refund-policy. Opened contact lenses cannot be returned", env="STORE_RETURN_POLICY")
    STORE_SHIPPING_INFO: str = Field(default="Free delivery on orders above 3000 PKR. For more info visit https://eyeshades.pk/pages/shipping-and-delivery", env="STORE_SHIPPING_INFO")
    STORE_ORDER_TRACKING_URL: str = Field(default="https://eyeshades.pk/pages/track-order", env="STORE_ORDER_TRACKING_URL")
    STORE_PAYMENT_METHODS: str = Field(default="Bank transfer, Cash on delivery", env="STORE_PAYMENT_METHODS")
    STORE_BANK_DETAILS: str = Field(default="Kashif Javaid, Meezan Bank, 02020103622814", env="STORE_BANK_DETAILS")


    # Environment/Debug
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Eyewear Domain Knowledge Constants
EYEWEAR_CATEGORIES = {
    "contact_lenses": {
        "daily": {
            "description": "Single-use contact lenses for daily wear",
            "benefits": ["Maximum hygiene", "No cleaning required", "Fresh lens daily"],
            "use_cases": ["Active lifestyle", "Occasional wear", "Travel"]
        },
        "weekly": {
            "description": "Contact lenses replaced every week",
            "benefits": ["Good hygiene", "Cost-effective", "Convenient"],
            "use_cases": ["Regular wear", "Budget-conscious", "Balanced lifestyle"]
        },
        "monthly": {
            "description": "Contact lenses replaced every month",
            "benefits": ["Most economical", "Durable", "Wide variety"],
            "use_cases": ["Daily wear", "Long-term users", "Prescription stability"]
        },
        "toric": {
            "description": "Specialized lenses for astigmatism correction",
            "benefits": ["Astigmatism correction", "Stable vision", "Comfortable fit"],
            "use_cases": ["Astigmatism", "Irregular cornea", "Clear vision needs"]
        },
        "multifocal": {
            "description": "Lenses for presbyopia and age-related vision changes",
            "benefits": ["Multiple focal points", "No reading glasses", "Seamless transition"],
            "use_cases": ["Presbyopia", "Age 40+", "Near/far vision needs"]
        }
    },
    "eyeglasses": {
        "frames": {
            "materials": {
                "acetate": "Durable, hypoallergenic, variety of colors",
                "metal": "Lightweight, adjustable, professional look",
                "titanium": "Ultra-light, corrosion-resistant, premium quality",
                "plastic": "Affordable, lightweight, colorful options"
            },
            "styles": {
                "full_rim": "Complete frame around lens, maximum durability",
                "semi_rimless": "Frame on top only, modern aesthetic",
                "rimless": "No frame around lens, minimalist look"
            }
        },
        "lenses": {
            "types": {
                "single_vision": "One prescription power throughout lens",
                "bifocal": "Two distinct viewing areas for near/far",
                "progressive": "Gradual transition between viewing zones"
            },
            "coatings": {
                "anti_reflective": "Reduces glare, improves clarity",
                "blue_light": "Filters blue light from screens",
                "photochromic": "Darkens in sunlight, clear indoors",
                "scratch_resistant": "Protects lens surface from damage"
            }
        }
    },
    "sunglasses": {
        "protection": {
            "uv400": "Blocks 100% of UV rays up to 400nm",
            "polarized": "Reduces glare from reflective surfaces",
            "category_levels": {
                "0": "Very light tint, fashion/indoor use",
                "1": "Light tint, slight sun protection",
                "2": "Medium tint, good sun protection",
                "3": "Dark tint, strong sun protection",
                "4": "Very dark, extreme conditions (not for driving)"
            }
        },
        "styles": {
            "aviator": "Classic teardrop shape, versatile",
            "wayfarer": "Rectangular frame, timeless style",
            "round": "Circular lenses, vintage appeal",
            "sport": "Wraparound design, active lifestyle",
            "oversized": "Large lenses, fashion statement"
        }
    }
}

# Common customer intents and responses
INTENT_PATTERNS = {
    "product_search": ["looking for", "need", "want", "show me", "find"],
    "browse_products": ["collection", "catalog", "all", "what do you have", "options", "available", "browse"],
    "specific_product": ["brand", "model", "acuvue", "ray-ban", "oakley", "daily", "weekly", "monthly"],
    "product_info": ["contact", "lens", "sunglasses", "glasses", "eyeglasses", "frames"],
    "comparison": ["vs", "versus", "compare", "difference", "better"],
    "recommendation": ["recommend", "suggest", "best", "advice", "help choose"],
    "technical_support": ["prescription", "fit", "problem", "issue", "how to"],
    "purchase_intent": ["buy", "order", "price", "cost", "checkout", "cart"],
    "general": ["hello", "hi", "help", "thanks", "thank you"]
}

# Response templates for different scenarios
RESPONSE_TEMPLATES = {
    "greeting": "Hello! I'm your eyewear specialist. How can I help you find the perfect contact lenses, eyeglasses, or sunglasses today?",
    "product_not_found": "I couldn't find exactly what you're looking for, but here are some similar options that might interest you:",
    "need_more_info": "To give you the best recommendation, could you tell me more about:",
    "prescription_required": "For prescription eyewear, I'd recommend consulting with an eye care professional to ensure the best fit and vision correction."
}

# Export settings instance
settings = Settings()
