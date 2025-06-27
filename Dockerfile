# Simple, reliable production Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory and non-root user
RUN mkdir -p /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application files
COPY jwt_mysql_automation_docker.py ./jwt_mysql_automation.py
COPY check_token_docker.py ./check_token.py

# Fix ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose health check port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Add labels for better container management
LABEL maintainer="kronotitans" \
      description="JWT MySQL Automation Service" \
      version="1.0" \
      org.opencontainers.image.source="https://github.com/kronotitans/jwt-mysql-automation"

# Default command
CMD ["python", "jwt_mysql_automation.py"]
