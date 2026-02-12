# ADR 0005: Multi-Stage Docker Build

## Status
Accepted

## Context
The application depends on compiled Python packages (numpy, pandas, scikit-learn) that require build tools (gcc, g++) during `pip install`. Including these tools in the production image would increase image size by ~200MB and expand the attack surface.

## Decision
We use a **multi-stage Docker build** with Python 3.12-slim:
1. **Builder stage**: Installs gcc/g++, compiles pip dependencies with `--prefix=/install`
2. **Runtime stage**: Copies only the installed packages from the builder, plus application code and datasets

## Rationale
- **Smaller image**: Runtime image contains no compilers, build headers, or pip cache — ~60% smaller than a single-stage build
- **Security**: No build tools in production reduces attack surface (CIS Docker Benchmark)
- **Reproducibility**: `--prefix=/install` isolates built packages for clean copy to runtime stage
- **Production defaults**: Environment variables in the Dockerfile set production-safe defaults (debug off, JSON logging, WARNING level)

### Production entrypoint
Gunicorn with 4 workers and 120s timeout handles the WSGI serving. The 120s timeout accommodates initial data loading and ECG precomputation on cold starts.

## Consequences
- Dataset files are copied into the image — image size depends on dataset size (~200MB for all CSVs)
- Rebuilding the image is required when dependencies change (no hot-reload of packages)
- Docker Compose overrides the entrypoint for development (uses Dash dev server with hot reload instead of Gunicorn)
