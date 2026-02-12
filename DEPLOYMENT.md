# Deployment Guide

This guide covers deploying the Multi-Domain Analytics Dashboard to production environments using Docker, Kubernetes, or bare-metal servers.

## Prerequisites

- Python 3.10+ (tested on 3.10 and 3.12)
- Docker 20.10+ (for containerized deployment)
- kubectl + a Kubernetes cluster (for K8s deployment)
- Datasets placed in the `datasets/` directory

## Environment Variables

All configuration is driven by environment variables. Copy `.env.example` to `.env` and customize:

| Variable | Default (dev) | Production | Description |
|----------|--------------|------------|-------------|
| `DASH_ENV` | `development` | `production` | Environment name |
| `DASH_HOST` | `127.0.0.1` | `0.0.0.0` | Bind address |
| `DASH_PORT` | `8050` | `8050` | Listen port |
| `DASH_DEBUG` | `true` | `false` | Enable Dash debug mode |
| `DASH_LOG_LEVEL` | `DEBUG` | `WARNING` | Python log level |
| `DASH_LOG_FORMAT` | `text` | `json` | Log format (`text` or `json`) |
| `GUNICORN_WORKERS` | `4` | `4` | Gunicorn worker count |
| `GUNICORN_TIMEOUT` | `120` | `120` | Gunicorn request timeout (seconds) |
| `SENTRY_DSN` | *(unset)* | *(your DSN)* | Optional Sentry error tracking |
| `SENTRY_TRACES_RATE` | *(unset)* | `0.1` | Sentry trace sample rate |

### Production Recommendations

- Set `GUNICORN_WORKERS` to `2 * CPU_CORES + 1` for CPU-bound workloads.
- Keep `GUNICORN_TIMEOUT` at 120s to allow for initial data loading and ECG precomputation.
- Use `DASH_LOG_FORMAT=json` for structured logging compatible with ELK, Splunk, or CloudWatch.

## Docker Deployment

### Build the Image

```bash
docker build -t analytics-dashboard:latest .
```

The Dockerfile uses a multi-stage build:
1. **Builder stage** — installs system compilers and pip dependencies
2. **Runtime stage** — copies only the installed packages, app code, and datasets into a lean Python 3.12-slim image

### Run with Docker

```bash
docker run -d \
  --name dashboard \
  -p 8050:8050 \
  -e DASH_ENV=production \
  -e DASH_LOG_FORMAT=json \
  -e DASH_LOG_LEVEL=WARNING \
  analytics-dashboard:latest
```

### Run with Docker Compose (Development)

```bash
docker-compose up
```

Docker Compose mounts `app/`, `datasets/`, and `data_cache/` as volumes for live reloading and overrides the entrypoint to use the Dash dev server instead of Gunicorn.

### Run with Docker Compose (Production Override)

Create a `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  dashboard:
    build: .
    ports:
      - "8050:8050"
    environment:
      - DASH_ENV=production
      - DASH_HOST=0.0.0.0
      - DASH_DEBUG=false
      - DASH_LOG_LEVEL=WARNING
      - DASH_LOG_FORMAT=json
    restart: unless-stopped
```

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

See the `k8s/` directory for ready-to-use manifests:

- `k8s/configmap.yaml` — environment configuration
- `k8s/deployment.yaml` — Deployment with health checks and HPA
- `k8s/service.yaml` — ClusterIP Service

### Quick Start

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check rollout status
kubectl rollout status deployment/analytics-dashboard

# Access via port-forward (for testing)
kubectl port-forward svc/analytics-dashboard 8050:8050
```

### Scaling

The Deployment includes a HorizontalPodAutoscaler that scales between 2 and 8 replicas based on CPU utilization (target: 70%).

```bash
# Manual scaling
kubectl scale deployment/analytics-dashboard --replicas=4

# Check HPA status
kubectl get hpa analytics-dashboard
```

## Bare-Metal / VM Deployment

### Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run with Gunicorn

```bash
export DASH_ENV=production
export DASH_LOG_FORMAT=json
export DASH_LOG_LEVEL=WARNING

gunicorn \
  --bind 0.0.0.0:8050 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  app.main:server
```

### Run with systemd

Create `/etc/systemd/system/analytics-dashboard.service`:

```ini
[Unit]
Description=Multi-Domain Analytics Dashboard
After=network.target

[Service]
Type=simple
User=dashboard
WorkingDirectory=/opt/analytics-dashboard
EnvironmentFile=/opt/analytics-dashboard/.env
ExecStart=/opt/analytics-dashboard/venv/bin/gunicorn \
  --bind 0.0.0.0:8050 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  app.main:server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now analytics-dashboard
sudo systemctl status analytics-dashboard
```

## Monitoring

### Health Check

The application exposes a `/health` endpoint that returns:

```json
{
  "status": "healthy",
  "uptime_seconds": 12345.6,
  "cache": {
    "equipment": { "exists": true, "size_bytes": 1048576 },
    "bases": { "exists": true, "size_bytes": 524288 },
    "healthcare": { "exists": true, "size_bytes": 2097152 },
    "ecg": { "exists": true, "size_bytes": 2097152 }
  },
  "cache_directory": true,
  "data_available": true,
  "all_caches_warm": true
}
```

- **200** — healthy
- **503** — degraded (datasets directory missing)

Use this endpoint for:
- Docker `HEALTHCHECK`
- Kubernetes `livenessProbe` / `readinessProbe`
- Load balancer health checks

### Metrics

The `/metrics` endpoint returns JSON counters and histograms:

```json
{
  "counters": {
    "cache_hits": 42,
    "cache_misses": 4
  },
  "histograms": {
    "callback_duration_seconds{callback=render_tab}": {
      "count": 100,
      "sum": 5.234,
      "min": 0.012,
      "max": 0.456,
      "avg": 0.052
    }
  }
}
```

Scrape with Prometheus `json_exporter`, Datadog, or any HTTP-based monitoring agent.

### Logging

- **Development:** Human-readable pipe-delimited text to stdout
- **Production:** Single-line JSON to stdout for log aggregation

Example JSON log entry:
```json
{"timestamp": "2024-01-15T10:30:00Z", "level": "WARNING", "name": "app.data.loader", "message": "Cache miss for equipment data"}
```

### Error Tracking (Sentry)

Set the `SENTRY_DSN` environment variable to enable Sentry integration. The application automatically captures unhandled exceptions and can send manual breadcrumbs via `capture_message()`.

## Data & Caching

### First-Run Behavior

On first startup, the application:
1. Loads raw CSV datasets from `datasets/`
2. Generates Parquet caches in `data_cache/` for equipment, bases, and healthcare data
3. Precomputes ECG analysis (50 samples/class, mean waveforms, correlation matrices, PCA embeddings) and saves to `data_cache/ecg_precomputed.json`

The ECG precomputation processes ~555MB of raw data into a ~2MB cache file. This takes several minutes on first run but is instant on subsequent startups.

### Cache Persistence

For containerized deployments, mount `data_cache/` as a persistent volume to avoid recomputing on restarts:

```yaml
# docker-compose
volumes:
  - dashboard-cache:/app/data_cache

# Kubernetes
volumeMounts:
  - name: cache-volume
    mountPath: /app/data_cache
```

## Reverse Proxy (nginx)

Example nginx configuration for production:

```nginx
upstream dashboard {
    server 127.0.0.1:8050;
}

server {
    listen 80;
    server_name dashboard.example.com;

    location / {
        proxy_pass http://dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for Dash callbacks)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| App exits on startup | Missing datasets | Ensure `datasets/` directory contains all CSV files |
| Slow first load | ECG precomputation | Wait for cache generation or pre-build the cache |
| 503 on `/health` | Datasets directory missing | Mount datasets directory correctly |
| Worker timeout | Large data processing | Increase `GUNICORN_TIMEOUT` |
| High memory usage | Multiple Gunicorn workers loading data | Reduce `GUNICORN_WORKERS` or increase container memory |
