# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal requirements for testing
COPY requirements_minimal.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main_simple.py main.py
COPY start.sh .

# Create necessary directories
RUN mkdir -p logs

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Use the start script
CMD ["./start.sh"]
