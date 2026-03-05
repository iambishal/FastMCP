# ===================================
# Multi-stage Dockerfile for Production
# ===================================

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ===================================
# Stage 2: Production stage
# ===================================
FROM python:3.11-slim

# Set labels for container metadata
LABEL maintainer="your-email@example.com"
LABEL version="1.0.0"
LABEL description="Production-grade FastMCP Server"

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/mcpuser/.local

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R mcpuser:mcpuser /app

# Copy application code
COPY --chown=mcpuser:mcpuser ./src ./src

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/mcpuser/.local/bin:$PATH \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    LOG_FILE=/app/logs/app.log \
    LOG_MAX_BYTES=10485760 \
    LOG_BACKUP_COUNT=5 \
    PORT=8000

# Switch to non-root user
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "src/main.py"]
