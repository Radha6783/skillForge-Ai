# =============================================================================
# SkillForge AI — Backend Dockerfile
# Base: python:3.12-slim
# Installs dependencies, copies application code, exposes port 8000.
# Startup is handled by entrypoint.sh which runs migrations then uvicorn.
# =============================================================================

FROM python:3.12-slim

# Install system dependencies needed by psycopg2 and pg_isready (postgresql-client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy and install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application (respects .dockerignore)
COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose the application port
EXPOSE 8000

# Use entrypoint.sh to handle migrations then start uvicorn
ENTRYPOINT ["./entrypoint.sh"]
