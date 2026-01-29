FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy source and install
COPY pyproject.toml .
COPY barb/ ./barb/
COPY assistant/ ./assistant/
COPY config/ ./config/
COPY api/ ./api/
COPY scripts/ ./scripts/
RUN pip install --no-cache-dir .

# Create data directory
RUN mkdir -p /app/data

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
