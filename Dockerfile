# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies in one layer and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt \
    && find /root/.local -type f -name "*.pyc" -delete \
    && find /root/.local -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Production stage - use alpine for smaller size
FROM python:3.11-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    && adduser -D -h /home/app -s /bin/sh app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy application code with proper ownership
COPY --chown=app:app src/ ./src/
COPY --chown=app:app static/ ./static/

# Create directory for SQLite database with proper permissions
RUN mkdir -p /app/data && chown app:app /app/data

# Switch to non-root user
USER app

# Environment variables
ENV PYTHONPATH=/app
ENV PATH=/home/app/.local/bin:$PATH
ENV DB_URL=sqlite:///./data/app.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Security labels
LABEL \
    org.opencontainers.image.title="AI Work OS" \
    org.opencontainers.image.description="Minimal AI Work OS for document processing and task management" \
    org.opencontainers.image.vendor="AI Work OS Team" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.source="https://github.com/your-org/ai-work-os" \
    security.scan.enabled="true"

# Expose port
EXPOSE 8000

# Health check - use curl instead of requests to avoid dependency
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/healthz || exit 1

# Run the application
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000"]