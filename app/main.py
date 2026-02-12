"""Data Visualization App - Main entry point."""

import sys
import os
from urllib.parse import parse_qs, urlencode

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash  # noqa: E402
from dash import dcc, html, Input, Output, no_update  # noqa: E402
import dash_bootstrap_components as dbc  # noqa: E402

from app.tabs import (  # noqa: E402
    tab_instructions,
    tab_equipment,
    tab_ecg,
    tab_bases,
    tab_healthcare,
    tab_combined,
    tab_admin,
)

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Tactical Command Center",
    assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
)

server = app.server

# Register monitoring endpoints on the Flask server
from app.health import register_health_endpoint  # noqa: E402
from app.metrics import register_metrics_endpoint  # noqa: E402

register_health_endpoint(server)
register_metrics_endpoint(server)

# App layout
app.layout = html.Div(
    [
        # Skip to content link (accessibility)
        html.A("Skip to main content", href="#tab-content", className="skip-link"),
        # URL state persistence
        dcc.Location(id="url", refresh=False),
        # Header
        html.Header(
            [
                dbc.Container(
                    [
                        html.Div(
                            [
                                html.Div("LIVE ANALYTICS PLATFORM", className="header-badge"),
                                html.H1(
                                    [
                                        "Command ",
                                        html.Span("Center", className="highlight"),
                                    ]
                                ),
                                html.P("Military, biomedical & healthcare intelligence \u2014 unified in one view"),
                            ],
                            className="header-inner",
                        ),
                    ],
                    fluid=True,
                ),
            ],
            className="app-header",
            role="banner",
        ),
        # Tabs — grouped: Military > Medical > Combined
        html.Main(
            dbc.Container(
                [
                    dbc.Tabs(
                        [
                            dbc.Tab(label="Instructions", tab_id="tab-instructions"),
                            dbc.Tab(label="Equipment Transfers", tab_id="tab-equipment"),
                            dbc.Tab(label="Installations Map", tab_id="tab-bases"),
                            dbc.Tab(label="ECG Analysis", tab_id="tab-ecg"),
                            dbc.Tab(label="Medical Records", tab_id="tab-healthcare"),
                            dbc.Tab(label="Combined Intel", tab_id="tab-combined"),
                            dbc.Tab(label="Admin", tab_id="tab-admin"),
                        ],
                        id="main-tabs",
                        active_tab="tab-equipment",
                    ),
                    html.Div(id="tab-content", role="tabpanel", **{"aria-live": "polite"}),
                ],
                fluid=True,
            ),
            role="main",
        ),
    ]
)


VALID_TABS = {
    "tab-instructions",
    "tab-equipment",
    "tab-ecg",
    "tab-bases",
    "tab-healthcare",
    "tab-combined",
    "tab-admin",
}


@app.callback(
    Output("main-tabs", "active_tab"),
    Input("url", "search"),
)
def set_tab_from_url(search):
    """Set active tab from URL query parameter on page load."""
    if search:
        params = parse_qs(search.lstrip("?"))
        tab = params.get("tab", [None])[0]
        if tab and tab in VALID_TABS:
            return tab
    return no_update


@app.callback(
    Output("url", "search"),
    Input("main-tabs", "active_tab"),
)
def update_url_from_tab(active_tab):
    """Write the active tab to the URL query string for shareability."""
    if active_tab:
        return "?" + urlencode({"tab": active_tab})
    return no_update


@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab"),
)
def render_tab(active_tab):
    """Render the selected tab content."""
    if active_tab == "tab-instructions":
        return tab_instructions.layout()
    elif active_tab == "tab-equipment":
        return tab_equipment.layout()
    elif active_tab == "tab-ecg":
        return tab_ecg.layout()
    elif active_tab == "tab-bases":
        return tab_bases.layout()
    elif active_tab == "tab-healthcare":
        return tab_healthcare.layout()
    elif active_tab == "tab-combined":
        return tab_combined.layout()
    elif active_tab == "tab-admin":
        return tab_admin.layout()
    return html.Div("Select a tab to get started.")


if __name__ == "__main__":
    from app.logging_config import setup_logging
    from app.settings import DASH_HOST, DASH_PORT, DASH_DEBUG
    from app.error_tracking import init_error_tracking

    logger = setup_logging()
    init_error_tracking()
    logger.info("Starting Tactical Command Center...")
    logger.info("Open http://%s:%s in your browser", DASH_HOST, DASH_PORT)
    app.run(debug=DASH_DEBUG, host=DASH_HOST, port=DASH_PORT)
