# ADR 0004: Structured Logging and In-Process Metrics

## Status
Accepted

## Context
The application needs observability for production deployment: log aggregation for debugging, health checks for load balancers, and metrics for performance monitoring. We needed to choose between external monitoring dependencies (Prometheus client, OpenTelemetry) and a lightweight built-in approach.

## Decision
We implemented:
- **Dual-format logging** (`logging_config.py`): JSON format for production (ELK/Splunk), pipe-delimited text for development, controlled by `DASH_LOG_FORMAT` env var
- **In-process metrics** (`metrics.py`): Thread-safe counters and histograms exposed via `/metrics` JSON endpoint
- **Health endpoint** (`health.py`): `/health` returns cache status, uptime, and data availability with HTTP 200/503
- **Optional Sentry** (`error_tracking.py`): Pluggable error tracking that falls back to structured logging when no DSN is configured

## Rationale
- **Zero external dependencies**: No Prometheus client library, no StatsD, no OpenTelemetry SDK — metrics are a simple Python dict exposed as JSON
- **JSON logging**: Single-line JSON logs are directly ingestible by ELK, Splunk, and CloudWatch without parsing rules
- **Environment-driven**: All configuration via environment variables — same Docker image works for dev and prod
- **Graceful degradation**: Sentry integration is optional (import-guarded); the app functions fully without it
- **Health check contract**: Standard HTTP health check works with Kubernetes probes, AWS ALB, and Docker HEALTHCHECK

### Why not Prometheus client
- Adds a dependency for a single-app dashboard
- JSON metrics endpoint is scrapable by `json_exporter` for Prometheus or directly by Datadog/custom agents
- Avoids the complexity of histogram buckets and label cardinality management for a small application

## Consequences
- Metrics are per-process (not aggregated across Gunicorn workers) — aggregation happens at the monitoring layer
- No histogram percentiles (p50, p99) — only min/max/avg/count/sum are tracked
- Rotating file handler writes to `app.log` (10MB max, 5 backups) — should be monitored in production
