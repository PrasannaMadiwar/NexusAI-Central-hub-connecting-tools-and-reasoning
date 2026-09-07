# NexusAI Production Multi-Tenant Backend Dockerfile
FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=10000

WORKDIR /app

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Render standard port (10000) and local port (8000)
EXPOSE 10000 8000

# Health check dynamically bound to active $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Start FastAPI server, dynamically binding to Render's allocated $PORT
CMD ["sh", "-c", "exec uvicorn nexusai.api.server:app --host 0.0.0.0 --port ${PORT:-10000}"]
