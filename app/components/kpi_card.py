"""Reusable KPI card component."""

import dash_bootstrap_components as dbc
from dash import html


def kpi_card(title, value, icon=None, color="#3498DB", info=None):
    """Create a styled KPI card component for dashboard metrics.

    Args:
        title: Display title for the KPI (e.g., "Total Items").
        value: Formatted value string (e.g., "1,234" or "$5.6M").
        icon: Unused, reserved for future icon support.
        color: Hex color string for the value text.
        info: Optional tooltip text shown via an info icon beside the title.

    Returns:
        dbc.Card: Bootstrap card component with title, value, and optional tooltip.
    """
    title_children = [html.Span(title)]
    tooltips = []
    if info:
        icon_id = f"kpi-{title.lower().replace(' ', '-')}-info-icon"
        title_children.append(html.I(className="bi bi-info-circle ms-2 chart-info-icon", id=icon_id))
        tooltips.append(dbc.Tooltip(info, target=icon_id, placement="right"))
    return html.Div(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H6(
                        title_children,
                        className="kpi-title",
                        style={"display": "flex", "alignItems": "center", "justifyContent": "center"} if info else {},
                    ),
                    html.H3(
                        value, className="kpi-value",
                        style={"color": color},
                        **{"aria-label": f"{title}: {value}"},
                    ),
                ]
                + tooltips
            ),
            className="kpi-card",
        ),
        role="status",
        **{"aria-label": f"{title} metric"},
    )
