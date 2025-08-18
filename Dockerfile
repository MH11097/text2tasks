# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy application code
COPY src/ ./src/
COPY static/ ./static/

# Create directory for SQLite database
RUN mkdir -p /app/data && chown app:app /app/data

# Switch to non-root user
USER app

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Environment variables
ENV PYTHONPATH=/app
ENV DB_URL=sqlite:///./data/app.db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/healthz', timeout=10)"

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]