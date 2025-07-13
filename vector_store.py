"""
Vector Store Manager for RAG Eyeshades Chatbot

This module manages ChromaDB vector storage for product embeddings,
handles similarity searches, and maintains the vector database
for efficient semantic retrieval.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings
import openai
import numpy as np

from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages ChromaDB vector storage and similarity search operations"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection names
        self.products_collection_name = settings.CHROMA_COLLECTION_PRODUCTS
        self.knowledge_collection_name = settings.CHROMA_COLLECTION_KNOWLEDGE
        self.faq_collection_name = settings.CHROMA_COLLECTION_FAQ
        
        # Initialize collections
        self.products_collection = None
        self.knowledge_collection = None
        self.faq_collection = None
        
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections"""
        try:
            # Products collection
            self.products_collection = self.chroma_client.get_or_create_collection(
                name=self.products_collection_name,
                metadata={"description": "Eyewear product embeddings from Shopify"}
            )
            
            # Knowledge collection
            self.knowledge_collection = self.chroma_client.get_or_create_collection(
                name=self.knowledge_collection_name,
                metadata={"description": "Eyewear domain knowledge and expertise"}
            )
            
            # FAQ collection
            self.faq_collection = self.chroma_client.get_or_create_collection(
                name=self.faq_collection_name,
                metadata={"description": "Frequently asked questions and answers"}
            )
            
            logger.info("✅ ChromaDB collections initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB collections: {e}")
            raise
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for given text using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            # Clean and prepare text
            cleaned_text = text.strip().replace("\n", " ")
            if not cleaned_text:
                raise ValueError("Empty text provided for embedding")
            
            # Create embedding
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model=self.embedding_model,
                input=cleaned_text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Created embedding for text: {cleaned_text[:100]}...")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            raise
    
    async def add_products(self, products: List[Dict[str, Any]]) -> bool:
        """
        Add product embeddings to the vector store
        
        Args:
            products: List of processed product dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not products:
                logger.warning("No products provided for embedding")
                return True
            
            # Prepare data for batch processing
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            logger.info(f"🔄 Processing {len(products)} products for vector storage...")
            
            for i, product in enumerate(products):
                try:
                    # Create unique ID
                    product_id = f"product_{product.get('id', i)}"
                    ids.append(product_id)
                    
                    # Get searchable content
                    searchable_content = product.get("searchable_content", "")
                    if not searchable_content:
                        logger.warning(f"No searchable content for product {product_id}")
                        continue
                    
                    # Create embedding
                    embedding = await self.create_embedding(searchable_content)
                    embeddings.append(embedding)
                    
                    # Prepare metadata
                    metadata = {
                        "product_id": str(product.get("id", "")),
                        "title": product.get("title", ""),
                        "product_type": product.get("product_type", ""),
                        "vendor": product.get("vendor", ""),
                        "eyewear_category": product.get("eyewear_category", "general"),
                        "price_min": min([v.get("price", 0) for v in product.get("variants", [])]) or 0,
                        "price_max": max([v.get("price", 0) for v in product.get("variants", [])]) or 0,
                        "available": any(v.get("available", False) for v in product.get("variants", [])),
                        "tags": ",".join(product.get("tags", [])),
                        "created_at": product.get("created_at", ""),
                        "updated_at": product.get("updated_at", "")
                    }
                    metadatas.append(metadata)
                    
                    # Store searchable content as document
                    documents.append(searchable_content)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(products)} products...")
                        
                except Exception as e:
                    logger.error(f"Error processing product {i}: {e}")
                    continue
            
            # Add to ChromaDB in batch
            if ids and embeddings:
                self.products_collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                
                logger.info(f"✅ Added {len(ids)} product embeddings to vector store")
                return True
            else:
                logger.warning("No valid products to add to vector store")
                return False
                
        except Exception as e:
            logger.error(f"Error adding products to vector store: {e}")
            return False
    
    async def search_products(
        self, 
        query: str, 
        n_results: int = 5,
        category_filter: Optional[str] = None,
        price_range: Optional[Tuple[float, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products using semantic similarity
        
        Args:
            query: Search query text
            n_results: Number of results to return
            category_filter: Filter by eyewear category
            price_range: Filter by price range (min, max)
            
        Returns:
            List of matching products with similarity scores
        """
        try:
            if not query.strip():
                return []
            
            # Create query embedding
            query_embedding = await self.create_embedding(query)
            
            # Prepare where clause for filtering
            where_clause = {}
            if category_filter:
                where_clause["eyewear_category"] = category_filter
            
            # Search in ChromaDB
            logger.info(f"🔍 Searching for: '{query}' in collection with {self.products_collection.count()} products")
            results = self.products_collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 50),  # Limit to prevent overwhelming results
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            logger.info(f"📊 Raw search results: {len(results.get('ids', [[]])[0]) if results else 0} items found")
            
            # Process results
            products = []
            if results and results["ids"]:
                for i in range(len(results["ids"][0])):
                    try:
                        metadata = results["metadatas"][0][i]
                        document = results["documents"][0][i]
                        distance = results["distances"][0][i]
                        similarity = 1 - distance  # Convert distance to similarity
                        
                        # Apply price filter if specified
                        if price_range:
                            min_price, max_price = price_range
                            product_price_min = metadata.get("price_min", 0)
                            product_price_max = metadata.get("price_max", 0)
                            
                            # Check if product price range overlaps with filter range
                            if (product_price_max < min_price or 
                                product_price_min > max_price):
                                continue
                        
                        # Only include results above similarity threshold (lowered for testing)
                        similarity_threshold = 0.3  # Temporarily lower threshold
                        if similarity >= similarity_threshold:
                            logger.debug(f"Product found: {metadata.get('title', '')} (similarity: {similarity:.3f})")
                            product = {
                                "product_id": metadata.get("product_id", ""),
                                "title": metadata.get("title", ""),
                                "description": metadata.get("description", ""),
                                "product_type": metadata.get("product_type", ""),
                                "vendor": metadata.get("vendor", ""),
                                "handle": metadata.get("handle", ""),
                                "category": metadata.get("eyewear_category", ""),
                                "price_range": {
                                    "min": metadata.get("price_min", 0),
                                    "max": metadata.get("price_max", 0)
                                },
                                "available": metadata.get("available", False),
                                "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                                "similarity_score": round(similarity, 3),
                                "searchable_content": document,
                                "created_at": metadata.get("created_at", ""),
                                "updated_at": metadata.get("updated_at", "")
                            }
                            products.append(product)
                            
                    except Exception as e:
                        logger.error(f"Error processing search result {i}: {e}")
                        continue
            
            # Sort by similarity score
            products.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            logger.info(f"🔍 Found {len(products)} products for query: '{query}'")
            return products[:n_results]
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    async def add_knowledge_base(self, knowledge_items: List[Dict[str, Any]]) -> bool:
        """
        Add eyewear domain knowledge to the vector store
        
        Args:
            knowledge_items: List of knowledge items with content and metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not knowledge_items:
                return True
            
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for i, item in enumerate(knowledge_items):
                try:
                    # Create embedding for knowledge content
                    content = item.get("content", "")
                    if not content:
                        continue
                    
                    embedding = await self.create_embedding(content)
                    
                    ids.append(f"knowledge_{i}")
                    embeddings.append(embedding)
                    documents.append(content)
                    metadatas.append({
                        "title": item.get("title", ""),
                        "category": item.get("category", ""),
                        "type": item.get("type", "knowledge"),
                        "source": item.get("source", "domain_expertise")
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing knowledge item {i}: {e}")
                    continue
            
            if ids:
                self.knowledge_collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                
                logger.info(f"✅ Added {len(ids)} knowledge items to vector store")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding knowledge base: {e}")
            return False
    
    async def search_knowledge(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search domain knowledge for relevant information
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant knowledge items
        """
        try:
            query_embedding = await self.create_embedding(query)
            
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "documents", "distances"]
            )
            
            knowledge_items = []
            if results and results["ids"]:
                for i in range(len(results["ids"][0])):
                    metadata = results["metadatas"][0][i]
                    document = results["documents"][0][i]
                    distance = results["distances"][0][i]
                    similarity = 1 - distance
                    
                    if similarity >= 0.5:  # Lower threshold for knowledge
                        knowledge_items.append({
                            "title": metadata.get("title", ""),
                            "content": document,
                            "category": metadata.get("category", ""),
                            "type": metadata.get("type", ""),
                            "similarity_score": round(similarity, 3)
                        })
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collections"""
        try:
            stats = {
                "products": {
                    "count": self.products_collection.count(),
                    "name": self.products_collection_name
                },
                "knowledge": {
                    "count": self.knowledge_collection.count(),
                    "name": self.knowledge_collection_name
                },
                "faq": {
                    "count": self.faq_collection.count(),
                    "name": self.faq_collection_name
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    async def clear_products(self) -> bool:
        """Clear all products from the vector store"""
        try:
            # Delete and recreate the products collection
            self.chroma_client.delete_collection(self.products_collection_name)
            self.products_collection = self.chroma_client.create_collection(
                name=self.products_collection_name,
                metadata={"description": "Eyewear product embeddings from Shopify"}
            )
            
            logger.info("✅ Cleared all products from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing products: {e}")
            return False
    
    async def initialize_domain_knowledge(self):
        """Initialize the vector store with domain knowledge"""
        try:
            from config import EYEWEAR_CATEGORIES
            
            knowledge_items = []
            
            # Convert domain knowledge to searchable items
            for category, subcategories in EYEWEAR_CATEGORIES.items():
                for subcat, details in subcategories.items():
                    if isinstance(details, dict):
                        if "description" in details:
                            content = f"{category} {subcat}: {details['description']}"
                            if "benefits" in details:
                                content += f" Benefits: {', '.join(details['benefits'])}"
                            if "use_cases" in details:
                                content += f" Best for: {', '.join(details['use_cases'])}"
                            
                            knowledge_items.append({
                                "title": f"{category.replace('_', ' ').title()} - {subcat.replace('_', ' ').title()}",
                                "content": content,
                                "category": category,
                                "type": "product_knowledge",
                                "source": "domain_expertise"
                            })
                        
                        # Handle nested dictionaries (like materials, styles, etc.)
                        for key, value in details.items():
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    content = f"{category} {subcat} {key} {sub_key}: {sub_value}"
                                    knowledge_items.append({
                                        "title": f"{category.replace('_', ' ').title()} - {sub_key.replace('_', ' ').title()}",
                                        "content": content,
                                        "category": category,
                                        "type": "technical_knowledge",
                                        "source": "domain_expertise"
                                    })
            
            # Add the knowledge to vector store
            await self.add_knowledge_base(knowledge_items)
            logger.info(f"✅ Initialized domain knowledge with {len(knowledge_items)} items")
            
        except Exception as e:
            logger.error(f"Error initializing domain knowledge: {e}")


# Example usage and testing
async def main():
    """Test the vector store manager"""
    vector_store = VectorStoreManager()
    
    # Initialize domain knowledge
    await vector_store.initialize_domain_knowledge()
    
    # Test embedding creation
    test_embedding = await vector_store.create_embedding("daily contact lenses for dry eyes")
    print(f"✅ Created embedding with {len(test_embedding)} dimensions")
    
    # Test knowledge search
    knowledge_results = await vector_store.search_knowledge("contact lens care")
    print(f"🔍 Found {len(knowledge_results)} knowledge items")
    
    # Get stats
    stats = vector_store.get_collection_stats()
    print(f"📊 Vector store stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
