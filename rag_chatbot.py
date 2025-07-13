"""
RAG Chatbot Core Engine for Eyewear E-commerce

This is the main RAG chatbot engine that orchestrates all components:
- Intent classification and understanding
- Context retrieval from vector stores
- Response generation with domain expertise
- Conversation memory and personalization
- Product recommendations and comparisons
"""

import asyncio
import json
import requests
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import re

import openai
from config import settings, INTENT_PATTERNS, RESPONSE_TEMPLATES, EYEWEAR_CATEGORIES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history and context for personalization"""
    
    def __init__(self, max_length: int = 10):
        self.conversations = {}
        self.max_length = max_length
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "messages": [],
                "created_at": datetime.now(),
                "last_active": datetime.now(),
                "preferences": {},
                "context": {}
            }
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[session_id]["messages"].append(message)
        self.conversations[session_id]["last_active"] = datetime.now()
        
        # Keep only the last max_length messages
        if len(self.conversations[session_id]["messages"]) > self.max_length:
            self.conversations[session_id]["messages"] = \
                self.conversations[session_id]["messages"][-self.max_length:]
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return self.conversations.get(session_id, {}).get("messages", [])
    
    def get_conversation_context(self, session_id: str) -> str:
        """Get formatted conversation context for RAG"""
        messages = self.get_conversation_history(session_id)
        if not messages:
            return ""
        
        context_parts = []
        for msg in messages[-5:]:  # Last 5 messages for context
            role = "Customer" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def update_preferences(self, session_id: str, preferences: Dict):
        """Update user preferences based on conversation"""
        if session_id in self.conversations:
            self.conversations[session_id]["preferences"].update(preferences)
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Remove old conversations to save memory"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, conv in self.conversations.items():
            if conv["last_active"] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.conversations[session_id]


class IntentClassifier:
    """Classifies user intents for better response handling"""
    
    def __init__(self):
        self.intent_keywords = INTENT_PATTERNS
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """
        Enhanced intent classification with contextual understanding
        
        Args:
            message: User message text
            
        Returns:
            Tuple of (intent, confidence_score)
        """
        message_lower = message.lower()
        intent_scores = {}
        
        # Enhanced intent detection with specific product mentions
        # Check for specific product searches
        if any(word in message_lower for word in ["show me", "find", "looking for", "need", "want", "search"]):
            if any(word in message_lower for word in ["collection", "all", "options", "available"]):
                return "browse_products", 0.9
            else:
                return "specific_product", 0.8
        
        # Check for collections/category browsing
        if any(word in message_lower for word in ["collection", "catalog", "all", "what do you have", "options", "available"]):
            return "browse_products", 0.9
        
        # Check for specific product names or brands
        brands = ["ray-ban", "oakley", "acuvue", "biofinity", "dailies", "gucci", "prada", "versace"]
        if any(brand in message_lower for brand in brands):
            return "specific_product", 0.8
        
        # Check for product types with context
        if any(word in message_lower for word in ["contact", "lens", "contacts"]):
            if any(word in message_lower for word in ["daily", "weekly", "monthly", "toric", "multifocal"]):
                return "specific_product", 0.8
            return "product_info", 0.7
            
        if any(word in message_lower for word in ["sunglasses", "sunglass"]):
            if any(word in message_lower for word in ["aviator", "wayfarer", "sport", "driving"]):
                return "specific_product", 0.8
            return "product_info", 0.7
            
        if any(word in message_lower for word in ["glasses", "eyeglasses", "frames"]):
            if any(word in message_lower for word in ["progressive", "bifocal", "reading", "prescription"]):
                return "specific_product", 0.8
            return "product_info", 0.7
        
        # Calculate scores for other intents
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    # Weight longer keywords more heavily
                    score += len(keyword.split())
            
            if score > 0:
                # Normalize by message length
                intent_scores[intent] = score / len(message_lower.split())
        
        # Return the highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[best_intent] * 2, 1.0)  # Cap at 1.0
            return best_intent, confidence
        
        return "general", 0.5
    
    def extract_product_preferences(self, message: str) -> Dict[str, Any]:
        """Extract product preferences from user message"""
        preferences = {}
        message_lower = message.lower()
        
        # Extract eyewear category
        if any(word in message_lower for word in ["contact", "lens", "contacts"]):
            preferences["category"] = "contact_lenses"
        elif any(word in message_lower for word in ["sunglasses", "sunglass"]):
            preferences["category"] = "sunglasses"
        elif any(word in message_lower for word in ["glasses", "eyeglasses", "frames"]):
            preferences["category"] = "eyeglasses"
        
        # Extract price preferences
        price_patterns = [
            r'pkr\s*(\d+(?:\.\d{2})?)',  # PKR 50.00
            r'rs\s*(\d+(?:\.\d{2})?)',   # Rs 50.00
            r'(\d+)\s*pkr',              # 50 PKR
            r'(\d+)\s*rupees?',          # 50 rupees
            r'under\s+(?:pkr|rs)?\s*(\d+)', # under PKR 50
            r'below\s+(?:pkr|rs)?\s*(\d+)', # below Rs 50
            r'less\s+than\s+(?:pkr|rs)?\s*(\d+)', # less than PKR 50
            r'\$(\d+(?:\.\d{2})?)',      # $50.00 (legacy support)
            r'(\d+)\s*dollar',           # 50 dollar (legacy support)
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                try:
                    price = float(matches[0])
                    if "under" in message_lower or "below" in message_lower or "less than" in message_lower:
                        preferences["max_price"] = price
                    else:
                        preferences["target_price"] = price
                except ValueError:
                    continue
        
        # Extract brand preferences
        brands = ["ray-ban", "oakley", "gucci", "prada", "versace", "acuvue", "biofinity", "dailies"]
        for brand in brands:
            if brand in message_lower:
                preferences.setdefault("brands", []).append(brand)
        
        # Extract style preferences
        styles = ["aviator", "wayfarer", "round", "square", "cat-eye", "sport", "oversized"]
        for style in styles:
            if style in message_lower:
                preferences.setdefault("styles", []).append(style)
        
        return preferences


class RAGChatbot:
    """Main RAG chatbot engine for eyewear e-commerce"""
    
    def __init__(self, vector_store_manager, shopify_extractor):
        self.vector_store = vector_store_manager
        self.shopify_extractor = shopify_extractor
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.conversation_memory = ConversationMemory(settings.CONVERSATION_MEMORY_LENGTH)
        self.intent_classifier = IntentClassifier()
        
        # System prompt for the chatbot
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the chatbot"""
        return f"""You are a professional eyewear consultant for {settings.STORE_NAME}. You help customers find contact lenses, eyeglasses, and sunglasses with expert recommendations.

**STORE INFORMATION:**
- Name: {settings.STORE_NAME}
- Website: {settings.STORE_WEBSITE}
- Email: {settings.STORE_EMAIL}
- Phone: {settings.STORE_PHONE}
- Address: {settings.STORE_ADDRESS}
- Business Hours: {settings.STORE_BUSINESS_HOURS}
- Return Policy: {settings.STORE_RETURN_POLICY}
- Shipping Info: {settings.STORE_SHIPPING_INFO}
- Payment Methods: {settings.STORE_PAYMENT_METHODS}
- Bank Details: {settings.STORE_BANK_DETAILS}

**COLLECTION URLS (use these exact links):**
Premium Sunglasses (>4000 PKR): https://eyeshades.pk/collections/premium-sunglasses
Budget Sunglasses (<4000 PKR): https://eyeshades.pk/collections/budget-sunglasses
Men Sunglasses: https://eyeshades.pk/collections/men-sunglasses
Women Sunglasses: https://eyeshades.pk/collections/women-sunglasses
Premium Eyeglasses (>4000 PKR): https://eyeshades.pk/collections/premium-eyeglasses
Budget Eyeglasses (<4000 PKR): https://eyeshades.pk/collections/budget-eyeglasses
Men Eyeglasses: https://eyeshades.pk/collections/men-eyeglasses
Women Eyeglasses: https://eyeshades.pk/collections/women-eyeglasses
Kids Eyewear: https://eyeshades.pk/collections/kids
Transparent Eyeglasses: https://eyeshades.pk/collections/transparent-eyeglasses
Originals (Authentic): https://eyeshades.pk/collections/originals
Contact Lenses - Color: https://eyeshades.pk/collections/color-contact-lens
Contact Lenses - Transparent: https://eyeshades.pk/collections/transparent-contact-lens
Contact Lenses - Toric Color: https://eyeshades.pk/collections/color-toric-contact-lens
Contact Lenses - Toric Transparent: https://eyeshades.pk/collections/transparent-toric-contact-lens
Bella Lens: https://eyeshades.pk/collections/bella-lens
Eyesoft Lens: https://eyeshades.pk/collections/eyesoft-lens

**MANDATORY RESPONSE FORMAT:**
ALWAYS format your responses like this:

Here are great options for you:

• **[Product Name]** for **PKR [Price]** - https://eyeshades.pk/products/[handle]
• **[Product Name]** for **PKR [Price]** - https://eyeshades.pk/products/[handle]

Browse more: [Collection Name](https://eyeshades.pk/collections/[collection-slug])

**ABSOLUTE REQUIREMENTS:**
- ONLY mention products EXACTLY as provided in the context
- NEVER create, invent, or make up ANY product names, prices, or details
- ALL prices must use "PKR" prefix (e.g., PKR 2,500)
- ALWAYS format product names in **bold**
- ALWAYS use bullet points (•) for product lists
- ALWAYS include product links with correct handles
- ALWAYS include relevant collection links at the end
- Keep responses to 2-3 products maximum
- End with a relevant collection link

**DELIVERY INFORMATION:**
Free delivery on orders above PKR 3,000. Small delivery fee applies for orders below PKR 3,000.

**FORBIDDEN ACTIONS:**
- Never make up product names or prices
- Never use generic descriptions as real products
- Never mention brands not in the provided context
- Never format responses as plain text without bullet points
- Never omit product links or collection links

**FOR STORE QUESTIONS:** Use exact information from STORE INFORMATION section above.
"""
    
    async def initialize(self):
        """Initialize the chatbot with data loading"""
        try:
            logger.info("🔄 Initializing RAG Chatbot...")
            
            # Test Shopify connection
            if not await self.shopify_extractor.test_connection():
                logger.error("❌ Failed to connect to Shopify API")
                return False
            
            # Initialize domain knowledge in vector store
            await self.vector_store.initialize_domain_knowledge()
            
            # Load initial product data
            await self.refresh_data()
            
            logger.info("✅ RAG Chatbot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Chatbot: {e}")
            return False
    
    async def refresh_data(self):
        """Refresh product data from Shopify"""
        try:
            logger.info("🔄 Refreshing product data from Shopify...")
            
            # Fetch products from Shopify
            raw_products = await self.shopify_extractor.fetch_all_products()
            
            if not raw_products:
                logger.warning("No products fetched from Shopify")
                return
            
            # Process products for RAG
            processed_products = []
            for product in raw_products:
                processed = self.shopify_extractor.process_product_for_rag(product)
                if processed:
                    processed_products.append(processed)
            
            # Clear existing products and add new ones
            await self.vector_store.clear_products()
            success = await self.vector_store.add_products(processed_products)
            
            if success:
                logger.info(f"✅ Successfully refreshed {len(processed_products)} products")
            else:
                logger.error("❌ Failed to refresh product data")
                
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
    
    async def process_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Process user message through the RAG pipeline
        
        Args:
            message: User message text
            session_id: Conversation session identifier
            
        Returns:
            Response dictionary with message, products, and metadata
        """
        try:
            # Add user message to conversation memory
            self.conversation_memory.add_message(session_id, "user", message)
            
            # Classify intent
            intent, intent_confidence = self.intent_classifier.classify_intent(message)
            
            # Extract preferences
            preferences = self.intent_classifier.extract_product_preferences(message)
            if preferences:
                self.conversation_memory.update_preferences(session_id, preferences)
            
            # Get conversation context
            conversation_context = self.conversation_memory.get_conversation_context(session_id)
            
            # Search for relevant products
            products = await self.search_products(message, limit=settings.TOP_K_RESULTS)
            
            # Search for relevant knowledge
            knowledge = await self.vector_store.search_knowledge(message, n_results=3)
            
            # Generate response
            response_text = await self._generate_response(
                user_message=message,
                intent=intent,
                products=products,
                knowledge=knowledge,
                conversation_context=conversation_context,
                preferences=preferences
            )
            
            # Add assistant response to conversation memory
            self.conversation_memory.add_message(
                session_id, 
                "assistant", 
                response_text,
                {
                    "intent": intent,
                    "intent_confidence": intent_confidence,
                    "products_found": len(products),
                    "knowledge_used": len(knowledge)
                }
            )
            
            return {
                "message": response_text,
                "recommended_products": products[:3],  # Top 3 recommendations
                "intent": intent,
                "confidence": intent_confidence,
                "session_id": session_id,
                "products_count": len(products),
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request right now. Please try again or contact customer support.",
                "recommended_products": [],
                "intent": "error",
                "confidence": 0.0,
                "session_id": session_id
            }
    
    async def search_products(
        self, 
        query: str, 
        limit: int = 5,
        category_filter: Optional[str] = None,
        price_range: Optional[Tuple[float, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with hybrid approach: vector search + keyword matching for night vision glasses
        """
        logger.info(f"🔍 Enhanced hybrid search for: '{query}' (limit: {limit})")
        
        # Enhanced query processing for better search
        enhanced_query = query.lower()
        
        # Extract category from query if not provided
        if not category_filter:
            if any(word in enhanced_query for word in ["contact", "lens", "contacts"]):
                category_filter = "contact_lenses"
            elif any(word in enhanced_query for word in ["sunglasses", "sunglass"]):
                category_filter = "sunglasses"  
            elif any(word in enhanced_query for word in ["glasses", "eyeglasses", "frames"]):
                category_filter = "eyeglasses"
        
        # Special handling for night vision queries - use direct keyword search first
        if any(term in enhanced_query for term in ["night vision", "night glasses", "driving glasses"]):
            logger.info("🌙 Detected night vision query - using hybrid search approach")
            keyword_results = await self._search_night_vision_products(query)
            if keyword_results:
                logger.info(f"✅ Found {len(keyword_results)} night vision products via keyword search")
                return keyword_results[:limit]
        
        # Expand query with synonyms and related terms
        query_expansions = []
        
        # Add synonyms for better matching
        if "daily" in enhanced_query:
            query_expansions.extend(["daily", "1-day", "disposable"])
        if "weekly" in enhanced_query:
            query_expansions.extend(["weekly", "weekly disposable", "2-week"])
        if "monthly" in enhanced_query:
            query_expansions.extend(["monthly", "monthly disposable", "30-day"])
        if "sunglasses" in enhanced_query:
            query_expansions.extend(["sunglasses", "sun glasses", "shades"])
        if "prescription" in enhanced_query:
            query_expansions.extend(["prescription", "Rx", "corrective"])
        
        # Add gender-specific terms for collection matching
        if any(word in enhanced_query for word in ["men", "man", "male", "boys"]):
            query_expansions.extend(["men", "male"])
        if any(word in enhanced_query for word in ["women", "woman", "female", "girls"]):
            query_expansions.extend(["women", "female"])
        if any(word in enhanced_query for word in ["kids", "children", "baby"]):
            query_expansions.extend(["kids", "children", "baby"])
        
        # Add specialty lens terms
        if any(word in enhanced_query for word in ["computer", "blue light", "screen"]):
            query_expansions.extend(["computer", "blue light"])
        if any(word in enhanced_query for word in ["progressive", "multifocal", "reading"]):
            query_expansions.extend(["progressive", "multifocal"])
        if any(word in enhanced_query for word in ["transition", "photochromic", "adaptive"]):
            query_expansions.extend(["transition", "photochromic"])
        if any(word in enhanced_query for word in ["night", "vision", "driving", "low light"]):
            query_expansions.extend(["night", "vision", "night vision", "driving glasses", "ray-ban aviator"])
        if any(word in enhanced_query for word in ["anti", "glare", "reflection"]):
            query_expansions.extend(["anti-glare", "anti-reflective"])
        
        # Create expanded search query
        if query_expansions:
            expanded_query = f"{query} {' '.join(query_expansions)}"
        else:
            expanded_query = query
        
        # Adjust limit based on query type
        if any(word in enhanced_query for word in ["collection", "all", "available", "options"]):
            limit = min(limit * 2, 10)  # Show more for browsing queries
        
        # Get products from vector store
        products = await self.vector_store.search_products(
            query=expanded_query,
            n_results=limit * 3,  # Get more results for better reranking
            category_filter=category_filter,
            price_range=price_range
        )
        
        # Apply title-based boosting for better relevance
        boosted_products = self._apply_title_boosting(products, query)
        
        # Take top results after boosting
        products = boosted_products[:limit]
        
        # Enhance products with collection URLs and better organization
        enhanced_products = []
        for product in products:
            enhanced_product = product.copy()
            
            # Extract collections from tags
            collections = self._extract_collections_from_tags(product.get('tags', []))
            enhanced_product['collections'] = collections
            
            # Generate collection URLs
            if collections:
                collection_urls = []
                for collection in collections:
                    # Convert collection name to URL-friendly format
                    url_collection = collection.lower().replace(' ', '-').replace('_', '-')
                    collection_url = f"https://eyeshades.pk/collections/{url_collection}"
                    collection_urls.append({
                        'name': collection,
                        'url': collection_url
                    })
                enhanced_product['collection_urls'] = collection_urls
            
            # Generate product URL
            if product.get('handle'):
                enhanced_product['product_url'] = f"https://eyeshades.pk/products/{product['handle']}"
            
            enhanced_products.append(enhanced_product)
        
        return enhanced_products
    
    def _apply_title_boosting(self, products: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Apply enhanced title-based boosting to prioritize products with exact matches in titles
        """
        query_words = set(word.lower().strip() for word in query.split())
        query_lower = query.lower()
        
        # Keywords that should get extra boost
        priority_keywords = {'night', 'vision', 'driving', 'computer', 'blue', 'light', 'anti-glare', 'transition', 'ray-ban', 'aviator'}
        
        for product in products:
            title = product.get('title', '').lower()
            description = product.get('description', '').lower()
            original_score = product.get('similarity_score', 0)
            boost = 0
            
            # Maximum boost for exact "night vision" products
            if 'night vision' in query_lower:
                if 'night vision' in title:
                    boost += 0.5  # Major boost for exact title match
                    logger.info(f"🎯 MAJOR boost +0.5 for 'night vision' in title: {product.get('title', '')}")
                elif 'night' in title and 'vision' in (title + ' ' + description):
                    boost += 0.3  # Good boost for related match
                    logger.info(f"🎯 Good boost +0.3 for night+vision match: {product.get('title', '')}")
                elif 'night' in title or 'vision' in title:
                    boost += 0.2  # Moderate boost for partial match
                    logger.info(f"🎯 Moderate boost +0.2 for partial match: {product.get('title', '')}")
            
            # Brand-specific boosts
            if any(brand in query_lower for brand in ['ray-ban', 'rayban']):
                if any(brand in title for brand in ['ray-ban', 'rayban']):
                    boost += 0.3
                    logger.info(f"🎯 Brand boost +0.3 for Ray-Ban: {product.get('title', '')}")
            
            # Style-specific boosts
            if 'aviator' in query_lower and 'aviator' in title:
                boost += 0.2
                logger.info(f"🎯 Style boost +0.2 for Aviator: {product.get('title', '')}")
            
            # Boost for individual priority keyword matches
            for word in query_words:
                if word in title and word in priority_keywords:
                    boost += 0.1
                    logger.info(f"🎯 Keyword boost +0.1 for '{word}' in: {product.get('title', '')}")
            
            # Additional boost for high-value products (night vision glasses are premium)
            if 'night vision' in query_lower:
                price_range = product.get('price_range', {})
                min_price = price_range.get('min', 0)
                if min_price > 5000:  # Premium products
                    boost += 0.1
                    logger.info(f"🎯 Premium boost +0.1 for high-value product: {product.get('title', '')}")
            
            # Apply boost to similarity score
            if boost > 0:
                new_score = min(1.0, original_score + boost)
                product['similarity_score'] = new_score
                logger.info(f"📈 Boosted score: {original_score:.3f} -> {new_score:.3f} for {product.get('title', '')}")
        
        # Re-sort by updated similarity scores
        products.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        return products
    
    async def _search_night_vision_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Direct keyword-based search for night vision products
        This bypasses vector search for better precision on night vision queries
        """
        try:
            # Use the existing vector store's products collection
            collection = self.vector_store.products_collection
            
            # Get all products and filter by keywords
            all_items = collection.get()
            night_vision_products = []
            
            # Keywords that indicate night vision products
            night_vision_keywords = ['night vision', 'night', 'vision', 'driving glasses', 'yellow lens']
            brand_keywords = ['ray-ban', 'rayban']
            
            query_lower = query.lower()
            
            for i, doc in enumerate(all_items['documents']):
                doc_lower = doc.lower()
                score = 0
                
                # High priority: exact "night vision" match
                if 'night vision' in doc_lower:
                    score += 10
                    logger.info(f"🎯 Found 'night vision' in: {doc[:100]}...")
                
                # Medium priority: individual keywords
                if 'night' in doc_lower and 'ray-ban' in doc_lower:
                    score += 8
                elif 'night' in doc_lower:
                    score += 3
                elif 'vision' in doc_lower and any(brand in doc_lower for brand in brand_keywords):
                    score += 5
                
                # Brand boost
                if any(brand in doc_lower for brand in brand_keywords):
                    score += 2
                
                # Query-specific matching
                query_words = query_lower.split()
                for word in query_words:
                    if word in doc_lower and word in ['night', 'vision', 'driving', 'glasses']:
                        score += 1
                
                if score >= 3:  # Minimum threshold
                    metadata = all_items['metadatas'][i] if all_items['metadatas'] else {}
                    
                    # Parse the document to extract product information
                    product_info = self._parse_product_document(doc, metadata)
                    product_info['keyword_score'] = score
                    product_info['similarity_score'] = 1.0 - (0.05 * (10 - score))  # Convert to similarity score
                    
                    night_vision_products.append(product_info)
            
            # Sort by keyword score (highest first)
            night_vision_products.sort(key=lambda x: x.get('keyword_score', 0), reverse=True)
            
            logger.info(f"🌙 Keyword search found {len(night_vision_products)} night vision products")
            for product in night_vision_products[:3]:
                logger.info(f"   - {product.get('title', 'Unknown')} (score: {product.get('keyword_score', 0)})")
            
            return night_vision_products
            
        except Exception as e:
            logger.error(f"Error in night vision keyword search: {e}")
            return []
    
    def _parse_product_document(self, document: str, metadata: Dict) -> Dict[str, Any]:
        """
        Parse a product document string to extract structured information
        """
        try:
            product_info = {
                'title': 'Unknown Product',
                'vendor': '',
                'description': '',
                'price_range': {'min': 0, 'max': 0},
                'handle': '',
                'tags': [],
                'available': True,
                'category': '',
                'product_type': ''
            }
            
            # Parse the document (format: "Product: Title | Type: ... | Brand: ... | Description: ... | Tags: ... | Price: ...")
            if ' | ' in document:
                parts = document.split(' | ')
                for part in parts:
                    if part.startswith('Product: '):
                        product_info['title'] = part.replace('Product: ', '').strip()
                    elif part.startswith('Brand: '):
                        product_info['vendor'] = part.replace('Brand: ', '').strip()
                    elif part.startswith('Type: '):
                        product_info['product_type'] = part.replace('Type: ', '').strip()
                    elif part.startswith('Description: '):
                        product_info['description'] = part.replace('Description: ', '').strip()
                    elif part.startswith('Tags: '):
                        tags_str = part.replace('Tags: ', '').strip()
                        product_info['tags'] = [tag.strip() for tag in tags_str.split(',')]
                    elif part.startswith('Price: PKR '):
                        price_str = part.replace('Price: PKR ', '').strip()
                        try:
                            if '-' in price_str:
                                min_price, max_price = price_str.split('-')
                                product_info['price_range'] = {
                                    'min': float(min_price.strip()),
                                    'max': float(max_price.strip())
                                }
                            else:
                                price = float(price_str)
                                product_info['price_range'] = {'min': price, 'max': price}
                        except ValueError:
                            pass
            
            # Generate handle from title
            if product_info['title']:
                handle = product_info['title'].lower()
                handle = handle.replace(' ', '-').replace('&', 'and')
                # Remove special characters except hyphens
                import re
                handle = re.sub(r'[^\w\-]', '', handle)
                product_info['handle'] = handle
            
            # Set category based on product type
            if product_info['product_type']:
                if 'contact' in product_info['product_type'].lower():
                    product_info['category'] = 'contact_lenses'
                elif 'sunglass' in product_info['product_type'].lower():
                    product_info['category'] = 'sunglasses'
                elif 'eyeglass' in product_info['product_type'].lower():
                    product_info['category'] = 'eyeglasses'
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error parsing product document: {e}")
            return {
                'title': 'Unknown Product',
                'vendor': '',
                'description': document[:100] + '...' if len(document) > 100 else document,
                'price_range': {'min': 0, 'max': 0},
                'handle': 'unknown',
                'tags': [],
                'available': True,
                'category': '',
                'product_type': ''
            }
    
    def _extract_collections_from_tags(self, tags: List[str]) -> List[str]:
        """Extract collection names from product tags"""
        collections = []
        
        # Define collection mapping based on observed tag patterns
        collection_mapping = {
            'men eyeglasses': 'Men Eyeglasses',
            'women eyeglasses': 'Women Eyeglasses', 
            'men sunglasses': 'Men Sunglasses',
            'women sunglasses': 'Women Sunglasses',
            'babyboy eyeglasses': 'Kids Eyeglasses',
            'babygirl eyeglasses': 'Kids Eyeglasses',
            'computer': 'Computer Glasses',
            'progressive': 'Progressive Lenses',
            'transition': 'Transition Lenses',
            'contact lens': 'Contact Lenses',
            'night vision': 'Night Vision Glasses',
            'driving': 'Driving Glasses',
            'anti glare': 'Anti-Glare Glasses'
        }
        
        # Also check for main categories
        main_categories = {
            'Eyeglasses': 'Eyeglasses',
            'sunglasses': 'Sunglasses',
            'contact lens': 'Contact Lenses'
        }
        
        for tag in tags:
            tag_lower = tag.lower()
            
            # Check exact matches first
            if tag_lower in collection_mapping:
                collection_name = collection_mapping[tag_lower]
                if collection_name not in collections:
                    collections.append(collection_name)
            
            # Check main categories
            elif tag in main_categories:
                collection_name = main_categories[tag]
                if collection_name not in collections:
                    collections.append(collection_name)
            
            # Check for special tags
            elif tag.startswith('tag__hot_'):
                collections.append('Best Selling')
            elif 'POWER UPTO' in tag:
                collections.append('Prescription Lenses')
        
        return collections
    
    async def _generate_response(
        self,
        user_message: str,
        intent: str,
        products: List[Dict[str, Any]],
        knowledge: List[Dict[str, Any]],
        conversation_context: str,
        preferences: Dict[str, Any]
    ) -> str:
        """Generate contextually aware response using OpenAI with RAG context"""
        try:
            # Build context for the LLM based on intent
            context_parts = []
            
            # Add conversation context if available
            if conversation_context:
                context_parts.append(f"CONVERSATION HISTORY:\n{conversation_context}")
            
            # Enhanced product information formatting based on intent
            if products:
                if intent == "browse_products":
                    # Show collection/category view with enhanced collection info
                    product_info = []
                    collections_seen = set()
                    
                    # Show up to 5 products with collection information
                    for i, product in enumerate(products[:5], 1):
                        info = f"• **{product['title']}**"
                        if product.get('vendor'):
                            info += f" by {product['vendor']}"
                        if product.get('price_range'):
                            price_min = product['price_range']['min']
                            price_max = product['price_range']['max']
                            if price_min == price_max:
                                info += f" for **PKR {price_min}**"
                            else:
                                info += f" for **PKR {price_min}-{price_max}**"
                        
                        # Add product handle for link generation
                        if product.get('handle'):
                            info += f" - https://eyeshades.pk/products/{product['handle']}"
                        
                        # Add collection information
                        if product.get('collections'):
                            collections = product['collections'][:2]  # Show max 2 collections
                            info += f" | Collections: {', '.join(collections)}"
                            collections_seen.update(collections)
                        
                        if product.get('available'):
                            info += " ✓ Available"
                        product_info.append(info)
                    
                    context_parts.append(f"AVAILABLE PRODUCTS:\n" + "\n".join(product_info))
                    
                    # Add collection summary with URLs
                    if collections_seen:
                        collection_urls = []
                        for collection in sorted(collections_seen):
                            collection_slug = collection.lower().replace(' ', '-').replace('&', 'and')
                            collection_urls.append(f"[{collection}](https://eyeshades.pk/collections/{collection_slug})")
                        context_parts.append(f"BROWSE COLLECTIONS: {', '.join(collection_urls)}")
                
                elif intent == "specific_product":
                    # Show specific product details with collection context
                    product_info = []
                    for i, product in enumerate(products[:3], 1):
                        info = f"• **{product['title']}**"
                        if product.get('vendor'):
                            info += f" by {product['vendor']}"
                        if product.get('price_range'):
                            price_min = product['price_range']['min']
                            price_max = product['price_range']['max']
                            if price_min == price_max:
                                info += f" for **PKR {price_min}**"
                            else:
                                info += f" for **PKR {price_min}-{price_max}**"
                        
                        # Add product handle for link generation
                        if product.get('handle'):
                            info += f" - https://eyeshades.pk/products/{product['handle']}"
                        
                        # Add collection and category info
                        details = []
                        if product.get('category'):
                            details.append(product['category'].replace('_', ' ').title())
                        if product.get('collections'):
                            details.append(f"Collections: {', '.join(product['collections'][:2])}")
                        if details:
                            info += f" ({', '.join(details)})"
                        
                        if product.get('available'):
                            info += " ✓ In Stock"
                        if product.get('description'):
                            # Add key features from description
                            desc = product['description'][:100] + "..." if len(product['description']) > 100 else product['description']
                            info += f"\n   Features: {desc}"
                        product_info.append(info)
                    
                    context_parts.append(f"MATCHING PRODUCTS:\n" + "\n".join(product_info))
                
                else:
                    # Default product view - show 5 relevant products with collections
                    product_info = []
                    collections_mentioned = set()
                    
                    for i, product in enumerate(products[:5], 1):
                        info = f"• **{product['title']}**"
                        if product.get('vendor'):
                            info += f" by {product['vendor']}"
                        if product.get('price_range'):
                            price_min = product['price_range']['min']
                            price_max = product['price_range']['max']
                            if price_min == price_max:
                                info += f" for **PKR {price_min}**"
                            else:
                                info += f" for **PKR {price_min}-{price_max}**"
                        
                        # Add product handle for link generation
                        if product.get('handle'):
                            info += f" - https://eyeshades.pk/products/{product['handle']}"
                        
                        # Add collection information for context
                        if product.get('collections'):
                            main_collection = product['collections'][0]  # Show primary collection
                            info += f" | {main_collection}"
                            collections_mentioned.add(main_collection)
                        
                        if product.get('available'):
                            info += " ✓ Available"
                        product_info.append(info)
                    
                    context_parts.append(f"RELEVANT PRODUCTS (Top 5):\n" + "\n".join(product_info))
                    
                    # Add collections context if we have multiple collections
                    if len(collections_mentioned) > 1:
                        context_parts.append(f"COLLECTIONS FEATURED: {', '.join(sorted(collections_mentioned))}")
            
            # Add domain knowledge
            if knowledge:
                knowledge_info = []
                for item in knowledge:
                    knowledge_info.append(f"- {item['title']}: {item['content']}")
                context_parts.append(f"DOMAIN KNOWLEDGE:\n" + "\n".join(knowledge_info))
            
            # Add user preferences
            if preferences:
                pref_text = []
                for key, value in preferences.items():
                    if isinstance(value, list):
                        pref_text.append(f"{key}: {', '.join(value)}")
                    else:
                        pref_text.append(f"{key}: {value}")
                context_parts.append(f"USER PREFERENCES:\n" + "\n".join(pref_text))
            
            # Combine context with enhanced product information
            if products or knowledge:
                full_context = self._build_enhanced_product_context(products, knowledge, intent)
            else:
                # Check if we should use Google search fallback
                # Use fallback only if no products found and query seems like it should have results
                should_use_fallback = (
                    len(user_message.split()) > 2 and  # More than 2 words
                    any(keyword in user_message.lower() for keyword in [
                        'what', 'how', 'why', 'when', 'where', 'tell me', 'explain', 
                        'difference', 'compare', 'benefit', 'advantage', 'best'
                    ]) and
                    any(keyword in user_message.lower() for keyword in [
                        'glasses', 'lens', 'contact', 'vision', 'eye', 'optical', 'sunglasses'
                    ])
                )
                
                if should_use_fallback:
                    logger.info(f"Using Google search fallback for query: {user_message}")
                    fallback_info = await self._google_search_fallback(user_message)
                    full_context = fallback_info
                else:
                    full_context = "No specific context available."
            
            # Create intent-specific prompts with strict validation
            if intent == "browse_products":
                if not products:
                    prompt = f"""The customer wants to browse products but NO PRODUCTS are provided in context.

CUSTOMER MESSAGE: "{user_message}"

REQUIRED RESPONSE: Say you don't have specific products to show right now, but offer to help them browse collections. DO NOT mention any specific product names or prices.

RESPONSE:"""
                else:
                    prompt = f"""The customer wants to browse our product collection. Show them what we have available.

CONTEXT:
{full_context}

CUSTOMER MESSAGE: "{user_message}"

CRITICAL RULES:
- ONLY mention products EXACTLY as listed in AVAILABLE PRODUCTS context above
- NEVER create or invent product names or prices
- Use ONLY PKR currency from the provided data
- If context shows no products, do NOT make up examples

RESPONSE:"""
            
            elif intent == "specific_product":
                if not products:
                    prompt = f"""The customer is asking about specific products but NO MATCHING PRODUCTS are provided in context.

CUSTOMER MESSAGE: "{user_message}"

REQUIRED RESPONSE: Say you don't see that specific product right now and suggest browsing collections. DO NOT invent any product names or prices.

RESPONSE:"""
                else:
                    prompt = f"""The customer is asking about specific products. Give them detailed, helpful information.

CONTEXT:
{full_context}

CUSTOMER MESSAGE: "{user_message}"

CRITICAL RULES:
- ONLY mention products EXACTLY as listed in MATCHING PRODUCTS context above  
- NEVER create or invent product names or prices
- Use ONLY PKR currency from the provided data
- Reference exact product titles and prices from context only

RESPONSE:"""
            
            else:
                if not products:
                    prompt = f"""Give a helpful response but NO PRODUCTS are provided in context.

CUSTOMER MESSAGE: "{user_message}"

CRITICAL RULES:
- DO NOT mention any specific product names or prices
- DO NOT create examples or fictional products
- Offer to help browse collections instead
- Keep response helpful but general

RESPONSE:"""
                else:
                    prompt = f"""Give a helpful, friendly response based on the customer's question.

CONTEXT:
{full_context}

CUSTOMER MESSAGE: "{user_message}"

CRITICAL RULES:
- ONLY reference products EXACTLY as listed in context above
- NEVER create or invent product names or prices  
- Use ONLY PKR currency from provided data
- If suggesting products, use only those from the context

RESPONSE:"""
            
            # Generate response using OpenAI
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again or let me know if you need help with a specific eyewear product."
    
    async def _google_search_fallback(self, query: str) -> str:
        """
        Perform Google search as fallback when no relevant products/knowledge found
        This should be used sparingly and only for eyewear-related queries
        """
        try:
            # Only use for eyewear-related queries
            eyewear_keywords = [
                'glasses', 'sunglasses', 'contact', 'lens', 'vision', 'eye', 
                'optical', 'prescription', 'frame', 'eyewear', 'sight'
            ]
            
            query_lower = query.lower()
            if not any(keyword in query_lower for keyword in eyewear_keywords):
                return "I specialize in eyewear products. Please ask me about glasses, contact lenses, or sunglasses."
            
            # Enhance query with eyewear context
            enhanced_query = f"{query} eyewear glasses contact lenses"
            
            # Use DuckDuckGo as a simple alternative to Google API
            search_url = f"https://api.duckduckgo.com/"
            params = {
                'q': enhanced_query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract relevant information
                        result_text = ""
                        if data.get('Abstract'):
                            result_text = data['Abstract']
                        elif data.get('RelatedTopics'):
                            # Get first few related topics
                            topics = data['RelatedTopics'][:3]
                            texts = []
                            for topic in topics:
                                if isinstance(topic, dict) and topic.get('Text'):
                                    texts.append(topic['Text'])
                            result_text = " ".join(texts)
                        
                        if result_text:
                            # Clean and limit the text
                            cleaned_text = result_text[:500] + "..." if len(result_text) > 500 else result_text
                            return f"Based on general eyewear knowledge: {cleaned_text}\n\nFor specific product recommendations, please let me know what type of eyewear you're looking for!"
                        
            return "I don't have specific information about that topic. Please ask me about our contact lenses, eyeglasses, or sunglasses!"
            
        except Exception as e:
            logger.error(f"Error in Google search fallback: {e}")
            return "I specialize in eyewear products from our store. Please ask me about glasses, contact lenses, or sunglasses!"
    
    def _build_enhanced_product_context(self, products: List[Dict], knowledge: List[Dict], intent: str) -> str:
        """Build enhanced product context including descriptions and specifications"""
        context_parts = []
        
        if products:
            context_parts.append("AVAILABLE PRODUCTS:")
            for i, product in enumerate(products[:5], 1):
                product_info = f"{i}. **{product.get('title', 'Unknown Product')}**"
                
                # Add vendor
                if product.get('vendor'):
                    product_info += f" by {product['vendor']}"
                
                # Add price
                price_range = product.get('price_range', {})
                if price_range:
                    min_price = price_range.get('min', 0)
                    max_price = price_range.get('max', 0)
                    if min_price == max_price:
                        product_info += f" - PKR {min_price}"
                    else:
                        product_info += f" - PKR {min_price}-{max_price}"
                
                # Add product URL
                if product.get('handle'):
                    product_info += f" - https://eyeshades.pk/products/{product['handle']}"
                
                # Add enhanced product details (description/specifications)
                details = []
                
                # Add category and type
                if product.get('category'):
                    details.append(f"Category: {product['category']}")
                if product.get('product_type'):
                    details.append(f"Type: {product['product_type']}")
                
                # Add description if available
                if product.get('description'):
                    desc = product['description']
                    # Limit description length for readability
                    if len(desc) > 150:
                        desc = desc[:150] + "..."
                    details.append(f"Description: {desc}")
                
                # Extract specifications from searchable content
                if product.get('searchable_content'):
                    content = product['searchable_content']
                    # Extract key details from searchable content
                    if any(keyword in content.lower() for keyword in ['diameter', 'base curve', 'power', 'axis', 'material', 'uv', 'specification']):
                        # Try to extract specifications
                        lines = content.split('|')
                        spec_lines = [line.strip() for line in lines if any(keyword in line.lower() 
                                     for keyword in ['diameter', 'base curve', 'power', 'axis', 'material', 'uv', 'available options'])]
                        if spec_lines:
                            details.extend(spec_lines[:2])  # Add up to 2 specification lines
                
                # Add collections
                if product.get('collections'):
                    collections = product['collections'][:2]
                    details.append(f"Collections: {', '.join(collections)}")
                
                # Add availability
                if product.get('available'):
                    details.append("✓ Available")
                
                if details:
                    product_info += f"\n   Details: {' | '.join(details)}"
                
                context_parts.append(product_info)
        
        # Add knowledge base information
        if knowledge:
            context_parts.append("\nRELEVANT EYEWEAR KNOWLEDGE:")
            for item in knowledge[:3]:
                if item.get('content'):
                    context_parts.append(f"• {item['content']}")
        
        return "\n".join(context_parts)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get chatbot statistics and performance metrics"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            product_count = await self.shopify_extractor.get_product_count()
            
            # Count active conversations
            active_conversations = len([
                conv for conv in self.conversation_memory.conversations.values()
                if (datetime.now() - conv["last_active"]).total_seconds() < 3600  # Active in last hour
            ])
            
            stats = {
                "vector_store": vector_stats,
                "shopify_products": product_count,
                "active_conversations": active_conversations,
                "total_conversations": len(self.conversation_memory.conversations),
                "system_status": "operational",
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}


# Example usage and testing
async def main():
    """Test the RAG chatbot"""
    from vector_store import VectorStoreManager
    from shopify_extractor import ShopifyExtractor
    
    # Initialize components
    vector_store = VectorStoreManager()
    shopify_extractor = ShopifyExtractor()
    chatbot = RAGChatbot(vector_store, shopify_extractor)
    
    # Initialize the chatbot
    if await chatbot.initialize():
        print("✅ Chatbot initialized successfully")
        
        # Test some conversations
        test_messages = [
            "I'm looking for daily contact lenses for dry eyes",
            "What sunglasses would you recommend for driving?",
            "I need progressive lenses for reading and computer work",
            "Compare the different types of contact lenses",
            "What's the best UV protection for outdoor sports?"
        ]
        
        for message in test_messages:
            print(f"\n👤 Customer: {message}")
            response = await chatbot.process_message(message, "test_session")
            print(f"🤖 Assistant: {response['message']}")
            if response['recommended_products']:
                print(f"📦 Recommended products: {len(response['recommended_products'])}")
        
        # Get statistics
        stats = await chatbot.get_statistics()
        print(f"\n📊 Chatbot statistics: {stats}")
    else:
        print("❌ Failed to initialize chatbot")


if __name__ == "__main__":
    asyncio.run(main())
