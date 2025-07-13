"""
Shopify Data Extractor for RAG Eyeshades Chatbot

This module handles all interactions with the Shopify API to fetch product data,
process it for the RAG system, and keep the vector store synchronized with
real-time inventory and pricing         # Variant information
        if product_data.get("variants"):
            prices = [v["price"] for v in product_data["variants"] if v["price"] > 0]
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                if min_price == max_price:
                    content_parts.append(f"Price: PKR {min_price}")
                else:
                    content_parts.append(f"Price Range: PKR {min_price} - PKR {max_price}")n.
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShopifyExtractor:
    """Handles Shopify API integration for product data extraction"""
    
    def __init__(self):
        self.shop_url = settings.SHOPIFY_SHOP_URL
        self.access_token = settings.SHOPIFY_ACCESS_TOKEN
        self.api_version = settings.SHOPIFY_API_VERSION
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"
        
        # Headers for Shopify API requests
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    async def fetch_all_products(self, limit: int = 250) -> List[Dict[str, Any]]:
        """
        Fetch all products from Shopify with pagination
        
        Args:
            limit: Number of products per page (max 250)
            
        Returns:
            List of product dictionaries
        """
        all_products = []
        page_info = None
        
        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    url = f"{self.base_url}/products.json?limit={limit}"
                    if page_info:
                        url += f"&page_info={page_info}"
                    
                    async with session.get(url, headers=self.headers) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch products: {response.status}")
                            break
                        
                        data = await response.json()
                        products = data.get("products", [])
                        
                        if not products:
                            break
                        
                        all_products.extend(products)
                        logger.info(f"Fetched {len(products)} products (Total: {len(all_products)})")
                        
                        # Check for pagination
                        link_header = response.headers.get("Link", "")
                        if "rel=\"next\"" not in link_header:
                            break
                        
                        # Extract page_info for next page
                        page_info = self._extract_page_info(link_header)
                        if not page_info:
                            break
            
            logger.info(f"Successfully fetched {len(all_products)} total products")
            return all_products
            
        except Exception as e:
            logger.error(f"Error fetching products from Shopify: {e}")
            return []
    
    def _extract_page_info(self, link_header: str) -> Optional[str]:
        """Extract page_info from Link header for pagination"""
        try:
            for link in link_header.split(","):
                if "rel=\"next\"" in link:
                    url_part = link.split(";")[0].strip("<> ")
                    if "page_info=" in url_part:
                        return url_part.split("page_info=")[1]
            return None
        except Exception:
            return None
    
    async def fetch_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific product by ID
        
        Args:
            product_id: Shopify product ID
            
        Returns:
            Product dictionary or None if not found
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/products/{product_id}.json"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("product")
                    else:
                        logger.warning(f"Product {product_id} not found: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            return None
    
    def process_product_for_rag(self, product: Dict[str, Any], collections: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Process raw Shopify product data for RAG system
        
        Args:
            product: Raw Shopify product data
            collections: List of collections this product belongs to
            
        Returns:
            Processed product data optimized for RAG
        """
        try:
            # Extract basic product information
            product_data = {
                "id": str(product.get("id", "")),
                "title": product.get("title", ""),
                "description": self._clean_html(product.get("body_html", "")),
                "vendor": product.get("vendor", ""),
                "product_type": product.get("product_type", ""),
                "tags": product.get("tags", "").split(",") if product.get("tags") else [],
                "handle": product.get("handle", ""),
                "created_at": product.get("created_at", ""),
                "updated_at": product.get("updated_at", ""),
                "published_at": product.get("published_at", ""),
                "status": product.get("status", ""),
                "images": [],
                "variants": [],
                "options": product.get("options", []),
                "seo_title": product.get("seo_title", ""),
                "seo_description": product.get("seo_description", "")
            }
            
            # Process images
            for image in product.get("images", []):
                product_data["images"].append({
                    "id": str(image.get("id", "")),
                    "src": image.get("src", ""),
                    "alt": image.get("alt", ""),
                    "width": image.get("width", 0),
                    "height": image.get("height", 0)
                })
            
            # Process variants
            for variant in product.get("variants", []):
                variant_data = {
                    "id": str(variant.get("id", "")),
                    "title": variant.get("title", ""),
                    "price": float(variant.get("price", 0)),
                    "compare_at_price": float(variant.get("compare_at_price", 0)) if variant.get("compare_at_price") else None,
                    "sku": variant.get("sku", ""),
                    "barcode": variant.get("barcode", ""),
                    "inventory_quantity": variant.get("inventory_quantity", 0),
                    "inventory_management": variant.get("inventory_management", ""),
                    "available": variant.get("available", False),
                    "weight": variant.get("weight", 0),
                    "weight_unit": variant.get("weight_unit", ""),
                    "option1": variant.get("option1", ""),
                    "option2": variant.get("option2", ""),
                    "option3": variant.get("option3", "")
                }
                product_data["variants"].append(variant_data)
            
            # Create searchable content for embedding
            searchable_content = self._create_searchable_content(product_data)
            product_data["searchable_content"] = searchable_content
            
            # Categorize product for domain-specific handling
            category = self._categorize_product(product_data)
            product_data["eyewear_category"] = category
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error processing product {product.get('id', 'unknown')}: {e}")
            return {}
    
    def _clean_html(self, html_content: str) -> str:
        """Remove HTML tags and clean up text content"""
        if not html_content:
            return ""
        
        # Simple HTML tag removal (for production, use a proper HTML parser)
        import re
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
    
    def _create_searchable_content(self, product_data: Dict[str, Any]) -> str:
        """
        Create comprehensive searchable content for embedding
        
        Args:
            product_data: Processed product data
            
        Returns:
            Combined searchable text
        """
        content_parts = []
        
        # Basic product info
        if product_data.get("title"):
            content_parts.append(f"Product: {product_data['title']}")
        
        if product_data.get("product_type"):
            content_parts.append(f"Type: {product_data['product_type']}")
        
        if product_data.get("vendor"):
            content_parts.append(f"Brand: {product_data['vendor']}")
        
        if product_data.get("description"):
            content_parts.append(f"Description: {product_data['description']}")
        
        # Tags and categories
        if product_data.get("tags"):
            content_parts.append(f"Tags: {', '.join(product_data['tags'])}")
        
        # Variant information
        if product_data.get("variants"):
            prices = [v["price"] for v in product_data["variants"] if v["price"] > 0]
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                if min_price == max_price:
                    content_parts.append(f"Price: PKR {min_price}")
                else:
                    content_parts.append(f"Price range: PKR {min_price} - PKR {max_price}")
            
            # Available options
            options = []
            for variant in product_data["variants"]:
                for i in range(1, 4):
                    option_value = variant.get(f"option{i}")
                    if option_value and option_value not in options:
                        options.append(option_value)
            if options:
                content_parts.append(f"Available options: {', '.join(options)}")
        
        # SEO content
        if product_data.get("seo_description"):
            content_parts.append(f"Features: {product_data['seo_description']}")
        
        return " | ".join(content_parts)
    
    def _categorize_product(self, product_data: Dict[str, Any]) -> str:
        """
        Categorize product into eyewear types
        
        Args:
            product_data: Processed product data
            
        Returns:
            Category string
        """
        title = product_data.get("title", "").lower()
        product_type = product_data.get("product_type", "").lower()
        tags = [tag.lower().strip() for tag in product_data.get("tags", [])]
        description = product_data.get("description", "").lower()
        
        # Combine all text for analysis
        all_text = f"{title} {product_type} {' '.join(tags)} {description}"
        
        # Contact lenses detection
        contact_keywords = ["contact", "lens", "daily", "weekly", "monthly", "toric", "multifocal", "colored"]
        if any(keyword in all_text for keyword in contact_keywords):
            return "contact_lenses"
        
        # Sunglasses detection
        sunglasses_keywords = ["sunglasses", "sunglass", "uv protection", "polarized", "aviator", "wayfarer"]
        if any(keyword in all_text for keyword in sunglasses_keywords):
            return "sunglasses"
        
        # Eyeglasses detection
        eyeglasses_keywords = ["eyeglasses", "glasses", "frames", "prescription", "reading", "progressive", "bifocal"]
        if any(keyword in all_text for keyword in eyeglasses_keywords):
            return "eyeglasses"
        
        # Default category
        return "general_eyewear"
    
    async def get_product_count(self) -> int:
        """Get total number of products in the store"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/products/count.json"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("count", 0)
                    else:
                        logger.error(f"Failed to get product count: {response.status}")
                        return 0
                        
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0
    
    async def test_connection(self) -> bool:
        """Test Shopify API connection"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/shop.json"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        logger.info("Shopify API connection successful")
                        return True
                    else:
                        logger.error(f"Shopify API connection failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error testing Shopify connection: {e}")
            return False
    
    async def fetch_all_collections(self) -> List[Dict[str, Any]]:
        """
        Fetch all collections from Shopify
        
        Returns:
            List of collection dictionaries
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/custom_collections.json"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch custom collections: {response.status}")
                        return []
                    
                    data = await response.json()
                    custom_collections = data.get("custom_collections", [])
                
                # Also fetch smart collections
                url = f"{self.base_url}/smart_collections.json"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        smart_collections = data.get("smart_collections", [])
                    else:
                        smart_collections = []
                
                all_collections = custom_collections + smart_collections
                logger.info(f"Fetched {len(all_collections)} collections ({len(custom_collections)} custom, {len(smart_collections)} smart)")
                return all_collections
                
        except Exception as e:
            logger.error(f"Error fetching collections: {e}")
            return []

    async def fetch_products_in_collection(self, collection_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all products in a specific collection
        
        Args:
            collection_id: Shopify collection ID
            
        Returns:
            List of product dictionaries in the collection
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/collections/{collection_id}/products.json"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        products = data.get("products", [])
                        logger.info(f"Fetched {len(products)} products from collection {collection_id}")
                        return products
                    else:
                        logger.warning(f"Failed to fetch products for collection {collection_id}: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching products for collection {collection_id}: {e}")
            return []

    async def get_product_collections_map(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create a mapping of product IDs to their collections
        
        Returns:
            Dictionary mapping product_id -> list of collections
        """
        product_collections = {}
        
        try:
            # Get all collections
            collections = await self.fetch_all_collections()
            
            # For each collection, get its products and map them
            for collection in collections:
                collection_id = str(collection.get("id", ""))
                collection_info = {
                    "id": collection_id,
                    "title": collection.get("title", ""),
                    "handle": collection.get("handle", ""),
                    "description": collection.get("description", ""),
                    "url": f"eyeshades.pk/collections/{collection.get('handle', '')}"
                }
                
                # Get products in this collection
                products_in_collection = await self.fetch_products_in_collection(collection_id)
                
                for product in products_in_collection:
                    product_id = str(product.get("id", ""))
                    if product_id not in product_collections:
                        product_collections[product_id] = []
                    product_collections[product_id].append(collection_info)
            
            logger.info(f"Created collection mapping for {len(product_collections)} products")
            return product_collections
            
        except Exception as e:
            logger.error(f"Error creating product collections map: {e}")
            return {}

# Example usage and testing
async def main():
    """Test the Shopify extractor"""
    extractor = ShopifyExtractor()
    
    # Test connection
    if await extractor.test_connection():
        print("✅ Shopify connection successful")
        
        # Get product count
        count = await extractor.get_product_count()
        print(f"📊 Total products in store: {count}")
        
        # Fetch a few products
        products = await extractor.fetch_all_products(limit=5)
        print(f"📦 Fetched {len(products)} products for testing")
        
        # Process one product
        if products:
            processed = extractor.process_product_for_rag(products[0])
            print(f"🔄 Processed product: {processed.get('title', 'Unknown')}")
            print(f"📝 Searchable content: {processed.get('searchable_content', '')[:200]}...")
    else:
        print("❌ Shopify connection failed")


if __name__ == "__main__":
    asyncio.run(main())
