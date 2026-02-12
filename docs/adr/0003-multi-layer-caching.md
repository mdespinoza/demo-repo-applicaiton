# ADR 0003: Multi-Layer Caching Strategy

## Status
Accepted

## Context
The application loads four datasets:
- Military Equipment: 130,958 rows CSV (comma-delimited)
- ECG Data: ~555MB across 4 CSV files (no headers, 188 columns)
- Military Bases: 776 rows CSV (semicolon-delimited with GeoJSON polygons)
- Healthcare: 3,813 rows CSV

Cold loading all datasets from CSV on every startup takes 30-60 seconds (dominated by ECG). Re-parsing CSVs on every request is unacceptable for production.

## Decision
We implemented a **three-layer caching strategy**:

1. **In-memory cache** (`_cache` dict in `data/loader.py`): Holds loaded DataFrames for the lifetime of the process. First check on every data access.
2. **Disk cache** (Parquet files in `data_cache/`): Equipment, bases, and healthcare DataFrames are persisted as Parquet. Freshness is validated by comparing file modification times against source CSVs.
3. **ECG precomputation** (`ecg_precomputed.json`): Raw ECG data (~555MB) is reduced to a ~2MB JSON cache containing 50 samples/class, mean/std waveforms, signal features, correlation matrices, and PCA embeddings.

## Rationale
- **Parquet over CSV**: 3-10x faster reads, built-in compression, preserves dtypes (no re-parsing category columns or dates)
- **Freshness validation**: `_cache_is_fresh()` compares mtime of cache vs source — automatically regenerates when source data changes
- **ECG precomputation**: Reduces 555MB → 2MB by pre-sampling and pre-computing statistics. The dashboard never needs raw ECG signals — only aggregated views
- **In-memory layer**: Eliminates disk I/O for repeated accesses within a single process (important with Gunicorn workers)
- **Metrics integration**: Cache hits/misses are tracked via the metrics module for monitoring cache effectiveness

## Consequences
- First startup generates all caches (takes several minutes for ECG precomputation)
- `data_cache/` directory must be writable; for containers, it should be mounted as a volume to persist across restarts
- Cache invalidation is based solely on file timestamps — manual cache clearing may be needed if data processing logic changes
- Each Gunicorn worker maintains its own in-memory cache (not shared), so memory usage scales linearly with worker count
