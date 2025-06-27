# Multi-stage build for production optimization
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim AS production

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create logs directory and non-root user
RUN mkdir -p /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application files
COPY jwt_mysql_automation_docker.py ./jwt_mysql_automation.py
COPY check_token_docker.py ./check_token.py

# Copy environment template and create production .env if it doesn't exist
COPY .env.example ./.env.example
RUN if [ ! -f .env ]; then cp .env.example .env; fi

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
