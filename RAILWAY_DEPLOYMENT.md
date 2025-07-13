# Railway Deployment Guide for RAG Eyeshades Chatbot

This guide will help you deploy your RAG Eyeshades Chatbot to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Required API Keys**:
   - OpenAI API key
   - Shopify store credentials

## Step 1: Prepare Your Repository

Your repository now includes all necessary Railway configuration files:

- `railway.json` - Railway service configuration
- `Procfile` - Process definition for Railway
- `runtime.txt` - Python version specification
- `nixpacks.toml` - Nixpacks build configuration
- `start.sh` - Startup script
- `.env.production` - Environment variables template

## Step 2: Deploy to Railway

### Option A: Deploy from GitHub (Recommended)

1. **Connect GitHub to Railway**:
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your RAG Eyeshades repository

2. **Configure Environment Variables**:
   - In Railway dashboard, go to your project
   - Click on the "Variables" tab
   - Add the following environment variables:

   ```env
   # Required Variables
   OPENAI_API_KEY=sk-your-openai-api-key-here
   SHOPIFY_SHOP_URL=your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=shpat_your-access-token-here
   
   # Optional but Recommended
   OPENAI_MODEL=gpt-4-turbo-preview
   API_SECRET_KEY=your-secure-random-key-here
   API_CORS_ORIGINS=["https://your-domain.com", "https://eyeshades.pk"]
   LOG_LEVEL=INFO
   ```

### Option B: Deploy with Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Initialize and Deploy**:
   ```bash
   railway init
   railway up
   ```

## Step 3: Environment Variables Setup

Add these environment variables in your Railway dashboard:

### Required Variables:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_your-access-token-here
```

### Store Configuration:
```env
STORE_NAME=Eyeshades
STORE_WEBSITE=https://eyeshades.pk
STORE_EMAIL=info@eyeshades.pk
STORE_PHONE=+92-XXX-XXXXXXX
STORE_ADDRESS=Your Store Address
STORE_BUSINESS_HOURS=9 AM - 6 PM, Monday to Saturday
```

### Advanced Configuration:
```env
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_MAX_TOKENS=500
API_SECRET_KEY=your-secure-secret-key
API_CORS_ORIGINS=["https://eyeshades.pk", "https://your-domain.com"]
LOG_LEVEL=INFO
CHROMA_DB_PATH=./chroma_db
```

## Step 4: Verify Deployment

1. **Check Build Logs**:
   - In Railway dashboard, click on "Deployments"
   - Monitor the build process
   - Ensure no errors in the logs

2. **Test API Endpoints**:
   - Visit your Railway app URL
   - Test these endpoints:
     - `GET /` - Health check
     - `GET /health` - Detailed health status
     - `POST /chat` - Chat functionality

3. **Test Chat Functionality**:
   ```bash
   curl -X POST "https://your-app.railway.app/chat" \
        -H "Content-Type: application/json" \
        -d '{
          "message": "Hi, I need contact lenses",
          "session_id": "test-session"
        }'
   ```

## Step 5: Monitor and Maintain

1. **View Logs**:
   - Railway dashboard > "Observability" tab
   - Monitor application logs for errors

2. **Resource Usage**:
   - Check CPU and memory usage
   - Scale up if needed

3. **Environment Updates**:
   - Update environment variables as needed
   - Redeploy when configuration changes

## Troubleshooting

### Common Issues:

1. **Build Failures**:
   - Check `requirements.txt` for conflicting dependencies
   - Ensure Python version compatibility (3.11 specified)

2. **Environment Variable Errors**:
   - Verify all required variables are set
   - Check for typos in variable names

3. **API Connection Issues**:
   - Verify OpenAI API key is valid
   - Check Shopify credentials and permissions

4. **Memory Issues**:
   - ChromaDB can use significant memory
   - Consider upgrading Railway plan if needed

### Log Commands:
```bash
# View recent logs
railway logs

# Follow logs in real-time
railway logs --follow
```

## Performance Optimization

1. **Vector Database**:
   - ChromaDB will persist data between deployments
   - Consider external vector DB for production scale

2. **Caching**:
   - Implement Redis for conversation memory
   - Cache frequently accessed data

3. **Monitoring**:
   - Set up health checks
   - Monitor response times

## Security Considerations

1. **Environment Variables**:
   - Never commit API keys to code
   - Use Railway's encrypted environment variables

2. **CORS Configuration**:
   - Update `API_CORS_ORIGINS` with your actual domain
   - Restrict to necessary origins only

3. **API Security**:
   - Consider rate limiting
   - Implement authentication for admin endpoints

## Support

If you encounter issues:

1. Check Railway documentation: [docs.railway.app](https://docs.railway.app)
2. Review build logs for specific error messages
3. Ensure all environment variables are correctly set
4. Test locally before deploying

Your RAG Eyeshades Chatbot should now be successfully deployed on Railway! 🎉
