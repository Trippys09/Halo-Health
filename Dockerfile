FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application (keep folder structure for imports)
COPY backend/ ./backend/

# Expose port (Render provides PORT env var)
EXPOSE 10000

# Start the application (use shell form to expand $PORT)
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}
