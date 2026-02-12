"""Tab 7: Admin Dashboard for cache management and system monitoring."""

import os
import platform
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output
import psutil

from app.data.loader import get_cache_info, clear_cache
from app.config import CACHE_DIR
from app.logging_config import get_logger

logger = get_logger(__name__)


def _format_bytes(nbytes):
    """Format bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def layout():
    """Build the Admin Dashboard tab layout."""
    return html.Div(
        [
            # Auto-refresh interval (every 10s)
            dcc.Interval(id="admin-refresh-interval", interval=10_000, n_intervals=0),
            # --- System Info ---
            html.H4("System Information", className="chart-title mt-3"),
            dbc.Row(id="admin-system-metrics", className="mb-3"),
            # --- Cache Management ---
            html.H4("Cache Management", className="chart-title"),
            dbc.Row(
                [
                    dbc.Col(
                        html.Button(
                            [html.I(className="bi bi-arrow-clockwise me-2", **{"aria-hidden": "true"}),
                             "Refresh All Caches"],
                            id="admin-refresh-all-btn",
                            className="btn btn-outline-warning btn-sm",
                            **{"aria-label": "Clear all in-memory caches and reload"},
                        ),
                        width="auto",
                    ),
                ],
                className="mb-3",
            ),
            html.Div(id="admin-refresh-status"),
            dbc.Row(id="admin-cache-cards"),
            # --- Disk Cache ---
            html.H4("Disk Cache Files", className="chart-title mt-3"),
            html.Div(id="admin-disk-info"),
        ],
        className="tab-content-wrapper",
    )


@callback(
    Output("admin-system-metrics", "children"),
    Input("admin-refresh-interval", "n_intervals"),
)
def update_system_metrics(_):
    """Show system resource usage as KPI-style cards."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    cpu_pct = process.cpu_percent(interval=None)

    cards = [
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6("Process Memory", className="kpi-title"),
                    html.H3(_format_bytes(mem_info.rss), className="kpi-value", style={"color": "#38BDF8"}),
                ]),
                className="kpi-card",
            ),
            md=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6("System Memory", className="kpi-title"),
                    html.H3(f"{psutil.virtual_memory().percent}%", className="kpi-value", style={"color": "#22D3EE"}),
                ]),
                className="kpi-card",
            ),
            md=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6("CPU Usage", className="kpi-title"),
                    html.H3(f"{cpu_pct:.1f}%", className="kpi-value", style={"color": "#34D399"}),
                ]),
                className="kpi-card",
            ),
            md=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H6("Python Version", className="kpi-title"),
                    html.H3(platform.python_version(), className="kpi-value", style={"color": "#FBBF24"}),
                ]),
                className="kpi-card",
            ),
            md=3,
        ),
    ]
    return cards


@callback(
    Output("admin-cache-cards", "children"),
    Output("admin-disk-info", "children"),
    Input("admin-refresh-interval", "n_intervals"),
    Input("admin-refresh-all-btn", "n_clicks"),
)
def update_cache_status(_, n_clicks):
    """Display cache status cards for each dataset."""
    cache_info = get_cache_info()

    cards = []
    for ds in cache_info:
        mem_badge = dbc.Badge("In Memory", color="success", className="me-1") if ds["in_memory"] else dbc.Badge(
            "Not Loaded", color="secondary", className="me-1"
        )
        cache_badge = dbc.Badge("Cached", color="info", className="me-1") if ds["cache_exists"] else dbc.Badge(
            "No Cache", color="warning", className="me-1"
        )
        source_badge = dbc.Badge("Source OK", color="success") if ds["source_exists"] else dbc.Badge(
            "Missing", color="danger"
        )

        rows_text = ""
        if ds["memory_rows"] is not None:
            rows_text = f"Rows: {ds['memory_rows']}"

        card = dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5(ds["name"], className="chart-title", style={"borderBottom": "none", "marginBottom": "8px"}),
                    html.Div([mem_badge, cache_badge, source_badge], className="mb-2"),
                    html.Div([
                        html.Small(
                            f"Cache: {ds['cache_size_mb']} MB",
                            className="text-muted d-block",
                        ),
                        html.Small(
                            f"Last cached: {ds['cache_modified'] or 'Never'}",
                            className="text-muted d-block",
                        ),
                        html.Small(
                            f"Source: {ds['source_modified'] or 'N/A'}",
                            className="text-muted d-block",
                        ),
                        html.Small(
                            rows_text, className="text-muted d-block"
                        ) if rows_text else None,
                    ]),
                ]),
                className="chart-card",
            ),
            md=3,
        )
        cards.append(card)

    # Disk cache info
    disk_rows = []
    if os.path.exists(CACHE_DIR):
        total_size = 0
        for f in sorted(os.listdir(CACHE_DIR)):
            fpath = os.path.join(CACHE_DIR, f)
            if os.path.isfile(fpath):
                sz = os.path.getsize(fpath)
                total_size += sz
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M:%S")
                disk_rows.append(
                    html.Tr([
                        html.Td(f, style={"color": "#E2E8F0"}),
                        html.Td(_format_bytes(sz), style={"color": "#94A3B8"}),
                        html.Td(mtime, style={"color": "#94A3B8"}),
                    ])
                )
        disk_rows.append(
            html.Tr([
                html.Td("Total", style={"color": "#38BDF8", "fontWeight": "700"}),
                html.Td(_format_bytes(total_size), style={"color": "#38BDF8", "fontWeight": "700"}),
                html.Td("", style={"color": "#94A3B8"}),
            ])
        )

    disk_table = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("File", style={"color": "#38BDF8"}),
                html.Th("Size", style={"color": "#38BDF8"}),
                html.Th("Last Modified", style={"color": "#38BDF8"}),
            ])),
            html.Tbody(disk_rows),
        ],
        bordered=True,
        dark=True,
        hover=True,
        size="sm",
        style={"maxWidth": "600px"},
    ) if disk_rows else html.P("No cache files found.", className="text-muted")

    return cards, disk_table


@callback(
    Output("admin-refresh-status", "children"),
    Input("admin-refresh-all-btn", "n_clicks"),
    prevent_initial_call=True,
)
def refresh_all_caches(n_clicks):
    """Clear all in-memory caches when refresh button is clicked."""
    clear_cache()
    return dbc.Alert(
        "All in-memory caches cleared. Data will be reloaded on next tab visit.",
        color="info",
        dismissable=True,
        duration=5000,
        className="mt-2",
    )
