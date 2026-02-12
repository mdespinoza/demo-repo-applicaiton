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
            html.Div(
                [
                    html.Div(
                        [html.I(className="bi bi-cpu"), html.Span("System Information")],
                        className="admin-section-title",
                    ),
                    dbc.Row(id="admin-system-metrics"),
                ],
                className="admin-section",
            ),
            # --- Cache Management ---
            html.Div(
                [
                    html.Div(
                        [html.I(className="bi bi-database-gear"), html.Span("Cache Management")],
                        className="admin-section-title",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Button(
                                    [
                                        html.I(
                                            className="bi bi-arrow-clockwise me-2",
                                            **{"aria-hidden": "true"},
                                        ),
                                        "Refresh All Caches",
                                    ],
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
                ],
                className="admin-section",
            ),
            # --- Disk Cache ---
            html.Div(
                [
                    html.Div(
                        [html.I(className="bi bi-hdd"), html.Span("Disk Cache Files")],
                        className="admin-section-title",
                    ),
                    html.Div(id="admin-disk-info"),
                ],
                className="admin-section",
            ),
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
                dbc.CardBody(
                    [
                        html.H6("Process Memory", className="kpi-title"),
                        html.H3(_format_bytes(mem_info.rss), className="kpi-value", style={"color": "#38BDF8"}),
                    ]
                ),
                className="kpi-card",
            ),
            md=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6("System Memory", className="kpi-title"),
                        html.H3(
                            f"{psutil.virtual_memory().percent}%", className="kpi-value", style={"color": "#22D3EE"}
                        ),
                    ]
                ),
                className="kpi-card",
            ),
            md=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6("CPU Usage", className="kpi-title"),
                        html.H3(f"{cpu_pct:.1f}%", className="kpi-value", style={"color": "#34D399"}),
                    ]
                ),
                className="kpi-card",
            ),
            md=3,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6("Python Version", className="kpi-title"),
                        html.H3(platform.python_version(), className="kpi-value", style={"color": "#FBBF24"}),
                    ]
                ),
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
        mem_badge = (
            dbc.Badge("In Memory", color="success", className="me-1")
            if ds["in_memory"]
            else dbc.Badge("Not Loaded", color="secondary", className="me-1")
        )
        cache_badge = (
            dbc.Badge("Cached", color="info", className="me-1")
            if ds["cache_exists"]
            else dbc.Badge("No Cache", color="warning", className="me-1")
        )
        source_badge = (
            dbc.Badge("Source OK", color="success") if ds["source_exists"] else dbc.Badge("Missing", color="danger")
        )

        rows_text = ""
        if ds["memory_rows"] is not None:
            rows_text = f"Rows: {ds['memory_rows']}"

        card = dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(
                            ds["name"], className="chart-title", style={"borderBottom": "none", "marginBottom": "8px"}
                        ),
                        html.Div([mem_badge, cache_badge, source_badge], className="mb-2"),
                        html.Div(
                            [
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
                                html.Small(rows_text, className="text-muted d-block") if rows_text else None,
                            ]
                        ),
                    ]
                ),
                className="chart-card",
            ),
            md=3,
        )
        cards.append(card)

    # Disk cache info — only show actual cache files (skip dotfiles)
    disk_items = []
    if os.path.exists(CACHE_DIR):
        for f in sorted(os.listdir(CACHE_DIR)):
            if f.startswith("."):
                continue
            fpath = os.path.join(CACHE_DIR, f)
            if os.path.isfile(fpath):
                sz = os.path.getsize(fpath)
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
                ext = os.path.splitext(f)[1].lstrip(".")
                disk_items.append({"name": f, "size": sz, "modified": mtime, "ext": ext})

    if disk_items:
        total_size = sum(item["size"] for item in disk_items)
        file_cards = []
        for item in disk_items:
            pct = (item["size"] / total_size * 100) if total_size > 0 else 0
            file_cards.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(className="bi bi-file-earmark-binary me-2"),
                                        html.Span(item["name"], className="disk-file-name"),
                                    ],
                                    className="disk-file-left",
                                ),
                                html.Div(
                                    [
                                        dbc.Badge(item["ext"].upper(), color="info", className="me-2"),
                                        html.Span(_format_bytes(item["size"]), className="disk-file-size"),
                                    ],
                                    className="disk-file-right",
                                ),
                            ],
                            className="disk-file-header",
                        ),
                        html.Div(
                            html.Div(
                                style={"width": f"{pct:.1f}%"},
                                className="disk-bar-fill",
                            ),
                            className="disk-bar",
                        ),
                        html.Small(item["modified"], className="text-muted"),
                    ],
                    className="disk-file-row",
                )
            )
        disk_table = html.Div(
            [
                html.Div(file_cards),
                html.Div(
                    [
                        html.Span("Total cache size", className="text-muted"),
                        html.Span(
                            _format_bytes(total_size),
                            className="disk-total-value",
                        ),
                    ],
                    className="disk-total-row",
                ),
            ]
        )
    else:
        disk_table = html.P("No cache files found.", className="text-muted")

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
