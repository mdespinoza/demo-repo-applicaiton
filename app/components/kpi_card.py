"""Reusable KPI card component."""
import dash_bootstrap_components as dbc
from dash import html


def kpi_card(title, value, icon=None, color="#3498DB", info=None):
    """Create a KPI card with title and value."""
    title_children = [html.Span(title)]
    tooltips = []
    if info:
        icon_id = f"kpi-{title.lower().replace(' ', '-')}-info-icon"
        title_children.append(html.I(className="bi bi-info-circle ms-2 chart-info-icon", id=icon_id))
        tooltips.append(dbc.Tooltip(info, target=icon_id, placement="right"))
    return dbc.Card(
        dbc.CardBody([
            html.H6(
                title_children,
                className="kpi-title",
                style={"display": "flex", "alignItems": "center", "justifyContent": "center"} if info else {},
            ),
            html.H3(value, className="kpi-value", style={"color": color}),
        ] + tooltips),
        className="kpi-card",
    )
