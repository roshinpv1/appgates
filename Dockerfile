# CodeGates API Server Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional API dependencies for production
RUN pip install --no-cache-dir \
    gunicorn==21.2.0 \
    redis==5.0.1

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/temp /app/reports

# Create non-root user
RUN useradd --create-home --shell /bin/bash codegates && \
    chown -R codegates:codegates /app
USER codegates

# Expose port (FastAPI runs on 8000 by default)
EXPOSE 8000

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command - run FastAPI server
CMD ["python", "start_server.py"] 