# ADR 0002: Store-Based Callback Architecture

## Status
Accepted

## Context
Each dashboard tab has multiple interactive filters (dropdowns, sliders, radio buttons) that drive updates to 5-10 charts. Naive implementation would create N*M callback connections (N filters x M charts), each independently loading and filtering data.

## Decision
We adopted a **filter → Store → chart** pattern:
1. A single filter callback reads all filter values, applies them to the dataset, and writes the filtered DataFrame (plus pre-computed aggregations) to a `dcc.Store` component as JSON.
2. Chart callbacks read from the Store and render their specific visualization.

## Rationale
- **Single data load**: The filter callback loads the dataset once; chart callbacks read pre-filtered data from the Store
- **Pre-computed aggregations**: Common aggregations (state totals, specialty counts) are computed once in the filter callback and shared across chart callbacks via the Store, avoiding redundant groupby operations
- **Decoupled updates**: Each chart callback is independent — adding or removing a chart doesn't affect other callbacks
- **Cross-module callbacks**: Using `@callback` from `dash` (not `app.callback`) allows callbacks to be defined in separate tab modules without circular imports
- **Serialization**: `DataFrame.to_json(orient="split")` provides compact serialization; pre-computed Series and aggregations are included alongside the filtered DataFrame

## Consequences
- Store data is serialized/deserialized as JSON on every filter change — adds latency for large datasets (mitigated by pre-aggregation)
- All chart callbacks in a tab fire when any filter changes, even if only one chart is affected
- Store size is bounded by pre-filtering (typically < 1MB of JSON after aggregation)
