"""Data Visualization App - Main entry point."""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from app.tabs import tab_instructions, tab_equipment, tab_ecg, tab_bases, tab_healthcare, tab_combined

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Tactical Command Center",
    assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
)

server = app.server

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        dbc.Container([
            html.Div([
                html.Div("LIVE ANALYTICS PLATFORM", className="header-badge"),
                html.H1([
                    "Command ",
                    html.Span("Center", className="highlight"),
                ]),
                html.P("Military, biomedical & healthcare intelligence \u2014 unified in one view"),
            ], className="header-inner"),
        ], fluid=True),
    ], className="app-header"),

    # Tabs — grouped: Military > Medical > Combined
    dbc.Container([
        dbc.Tabs([
            dbc.Tab(label="Instructions", tab_id="tab-instructions"),
            dbc.Tab(label="Equipment Transfers", tab_id="tab-equipment"),
            dbc.Tab(label="Installations Map", tab_id="tab-bases"),
            dbc.Tab(label="ECG Analysis", tab_id="tab-ecg"),
            dbc.Tab(label="Medical Records", tab_id="tab-healthcare"),
            dbc.Tab(label="Combined Intel", tab_id="tab-combined"),
        ], id="main-tabs", active_tab="tab-equipment"),
        html.Div(id="tab-content"),
    ], fluid=True),
])


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
    return html.Div("Select a tab to get started.")


if __name__ == "__main__":
    from app.logging_config import setup_logging

    logger = setup_logging()
    logger.info("Starting Tactical Command Center...")
    logger.info("Open http://localhost:8050 in your browser")
    app.run(debug=True, host="0.0.0.0", port=8050)
