# GitHub Copilot Instructions for RAG Eyeshades Chatbot

This file provides context and guidance for GitHub Copilot when working with the RAG Eyeshades Chatbot project.

## Project Overview

This is a sophisticated RAG (Retrieval-Augmented Generation) chatbot system designed for eyewear e-commerce websites. The system provides intelligent customer support and product recommendations for contact lenses, eyeglasses, and sunglasses.

## Architecture Components

### Core Files
- `main.py` - FastAPI application server with REST endpoints
- `rag_chatbot.py` - Main RAG engine with conversation management
- `vector_store.py` - ChromaDB vector database management
- `shopify_extractor.py` - Shopify API integration for product data
- `config.py` - Configuration management and domain knowledge

### Data Flow
1. Product data from Shopify API → Processing → Vector embeddings → ChromaDB
2. User query → Intent classification → Vector search → Context assembly → LLM response
3. Conversation memory → Preference learning → Personalized recommendations

## Key Technologies
- **FastAPI** for REST API
- **ChromaDB** for vector storage
- **OpenAI GPT-4** for response generation
- **OpenAI text-embedding-ada-002** for embeddings
- **LangChain** for RAG orchestration
- **Shopify API** for product data
- **Google Sheets API** for supplementary data

## Domain Knowledge

### Contact Lenses
- Daily: Single-use, maximum hygiene, convenient
- Weekly: Balanced cost/convenience, cleaning required
- Monthly: Most economical, consistent care needed
- Toric: For astigmatism correction
- Multifocal: For presbyopia and age-related vision

### Eyeglasses
- Frame materials: Acetate (durable), Metal (lightweight), Titanium (premium)
- Lens types: Single vision, Bifocal, Progressive
- Coatings: Anti-reflective, Blue light, Photochromic

### Sunglasses
- UV protection: UV400 blocks 100% harmful rays
- Categories: 0-4 protection levels
- Styles: Aviator, Wayfarer, Round, Sport, Oversized

## Development Guidelines

### Code Style
- Use async/await for all I/O operations
- Include comprehensive error handling and logging
- Add type hints for all function parameters and returns
- Follow PEP 8 naming conventions
- Include docstrings for all classes and functions

### Error Handling
- Always wrap API calls in try-catch blocks
- Log errors with appropriate context
- Return meaningful error messages to users
- Implement graceful degradation for service failures

### Performance Considerations
- Use batch operations for vector database updates
- Implement pagination for large data sets
- Cache frequently accessed data
- Optimize embedding generation for large product catalogs

### Security Best Practices
- Never commit API keys or credentials
- Use environment variables for all sensitive data
- Implement rate limiting for API endpoints
- Validate and sanitize all user inputs

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock external API calls
- Verify error handling paths
- Test edge cases and boundary conditions

### Integration Tests
- Test API endpoints end-to-end
- Verify database operations
- Test with real (but limited) data
- Validate conversation flows

### Performance Tests
- Load testing for concurrent users
- Vector search performance benchmarks
- Memory usage monitoring
- Response time optimization

## Common Patterns

### Async Database Operations
```python
async def add_products(self, products: List[Dict]) -> bool:
    try:
        # Process products in batches
        embeddings = await self.create_embeddings_batch(products)
        self.collection.add(embeddings)
        return True
    except Exception as e:
        logger.error(f"Failed to add products: {e}")
        return False
```

### Error Handling with Logging
```python
try:
    result = await api_call()
    logger.info(f"Operation successful: {result}")
    return result
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Response Generation Pattern
```python
context = await self.build_context(query, products, knowledge)
response = await self.generate_response(context)
self.memory.add_message(session_id, "assistant", response)
return response
```

## Environment Setup

### Required Environment Variables
```env
OPENAI_API_KEY=sk-...
SHOPIFY_SHOP_URL=store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_...
CHROMA_DB_PATH=./chroma_db
```

### Development Workflow
1. Set up virtual environment
2. Install dependencies from requirements.txt
3. Configure .env file with API keys
4. Run setup.py to initialize the system
5. Start development server with python main.py

## API Design Patterns

### Endpoint Structure
- `/chat` - Main conversation endpoint
- `/products/search` - Product search functionality
- `/admin/*` - Administrative operations
- `/health` - System health checks

### Request/Response Format
```json
{
  "message": "user query",
  "session_id": "unique_identifier",
  "metadata": {}
}
```

### Error Response Format
```json
{
  "error": "error_type",
  "message": "human_readable_message",
  "details": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Deployment Considerations

### Production Setup
- Use production-grade ASGI server (gunicorn + uvicorn)
- Implement proper logging and monitoring
- Set up health checks and metrics
- Configure CORS for frontend domains
- Use secrets management for API keys

### Scaling
- ChromaDB can be replaced with Pinecone for larger scale
- Implement Redis for conversation memory in multi-instance setup
- Use load balancer for multiple application instances
- Consider CDN for static assets

## Troubleshooting Guide

### Common Issues
1. **OpenAI API errors** - Check rate limits and API key validity
2. **Shopify connection issues** - Verify shop URL and access token
3. **Vector search performance** - Check embedding dimensions and collection size
4. **Memory usage** - Monitor conversation memory cleanup

### Debug Tools
- Check `/health` endpoint for system status
- Review logs in `logs/chatbot.log`
- Use `/admin/stats` for system metrics
- Monitor ChromaDB collection statistics

## Future Enhancements

### Planned Features
- Multi-language support
- Image-based product search
- Voice interface integration
- Advanced analytics dashboard
- Custom training on store-specific data

### Technical Improvements
- Streaming responses for better UX
- Improved intent classification models
- Enhanced conversation memory
- Real-time learning from user interactions

This documentation should help GitHub Copilot provide more accurate and context-aware suggestions when working with this codebase.
