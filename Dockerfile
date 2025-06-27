FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory and non-root user
RUN mkdir -p /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application files
COPY jwt_mysql_automation_docker.py ./jwt_mysql_automation.py
COPY check_token_docker.py ./check_token.py

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python check_token.py || exit 1

# Default command
CMD ["python", "jwt_mysql_automation.py"]
