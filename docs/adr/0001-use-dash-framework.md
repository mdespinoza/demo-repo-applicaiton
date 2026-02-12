# ADR 0001: Use Dash as the Web Framework

## Status
Accepted

## Context
We needed a framework to build an interactive, multi-dataset analytics dashboard with 50+ visualizations. The application must support server-side data processing (large CSV datasets up to 555MB), interactive filtering, and real-time chart updates without requiring a separate frontend build pipeline.

Options considered:
- **Dash (Plotly)** — Python-native reactive web framework with built-in Plotly charting
- **Streamlit** — Python rapid-prototyping framework
- **Flask + React** — Traditional backend + SPA frontend
- **Panel (HoloViz)** — Python dashboard framework built on Bokeh

## Decision
We chose **Dash 2.17.1** with Dash Bootstrap Components.

## Rationale
- **Single language**: Entire stack (data processing + UI) in Python — no JavaScript build pipeline needed
- **Plotly integration**: Native support for 40+ chart types (choropleth, treemap, sunburst, scatter, animated timelines) with consistent dark-theme styling
- **Callback pattern**: Declarative reactive callbacks (`@callback` with `Input`/`Output`) map cleanly to filter-driven dashboard UIs
- **Production-ready**: Built on Flask, deployable via Gunicorn with standard WSGI patterns
- **Bootstrap theming**: `dash-bootstrap-components` provides responsive grid layout and the Darkly theme with minimal custom CSS
- **Ecosystem**: Compatible with pandas, numpy, scikit-learn for server-side data processing

### Why not alternatives
- **Streamlit**: Lacks fine-grained layout control, re-runs entire script on interaction, limited multi-page support at the time of evaluation
- **Flask + React**: Would require maintaining two codebases and a build pipeline — significantly more complexity for a data visualization project
- **Panel**: Smaller community, fewer chart types natively supported compared to Plotly

## Consequences
- All team members need Python skills (no separate frontend role)
- Client-side interactivity is limited to what Dash callbacks support (no arbitrary JavaScript without `clientside_callback`)
- `suppress_callback_exceptions=True` is required for dynamic tab content, which reduces early error detection
