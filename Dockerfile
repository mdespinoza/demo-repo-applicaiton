# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies needed for compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code and datasets
COPY app/ ./app/
COPY datasets/ ./datasets/
COPY .env.example ./.env.example

# Create cache directory
RUN mkdir -p data_cache

# Production environment defaults
ENV DASH_ENV=production \
    DASH_HOST=0.0.0.0 \
    DASH_PORT=8050 \
    DASH_DEBUG=false \
    DASH_LOG_LEVEL=WARNING \
    DASH_LOG_FORMAT=json \
    GUNICORN_WORKERS=4 \
    GUNICORN_TIMEOUT=120 \
    PYTHONUNBUFFERED=1

EXPOSE 8050

# Run with gunicorn in production
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.main:server"]
