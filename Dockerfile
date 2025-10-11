FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY tools/ ./tools/
COPY src/ ./src/
COPY pyproject.toml .

# Install the package
RUN pip install -e .

# Expose ports
EXPOSE 7000 8000

# Environment variables
ENV PYTHONPATH=/app
ENV PORT=7000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7000/health || exit 1

# Start the bridge
CMD ["python", "tools/claude_tool_bridge.py"]