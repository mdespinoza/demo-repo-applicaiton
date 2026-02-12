"""Wrapper component with loading spinner for charts."""

from dash import dcc, html
import dash_bootstrap_components as dbc


def chart_container(graph_id, title=None, height=450, info=None):
    """Wrap a dcc.Graph in a styled card with optional title and loading spinner.

    Args:
        graph_id: Unique Dash component ID for the dcc.Graph.
        title: Optional chart title displayed above the graph.
        height: Graph height in pixels (default 450).
        info: Optional tooltip text shown via an info icon beside the title.

    Returns:
        dbc.Card: Bootstrap card containing the titled graph with loading indicator.
    """
    children = []
    if title:
        if info:
            icon_id = f"{graph_id}-info-icon"
            children.append(
                html.H5(
                    [html.Span(title), html.I(className="bi bi-info-circle ms-2 chart-info-icon", id=icon_id)],
                    className="chart-title",
                    style={"display": "flex", "alignItems": "center"},
                )
            )
            children.append(dbc.Tooltip(info, target=icon_id, placement="right"))
        else:
            children.append(html.H5(title, className="chart-title"))
    children.append(
        dcc.Loading(
            dcc.Graph(id=graph_id, style={"height": f"{height}px"}),
            type="circle",
            color="#38BDF8",
        )
    )
    return dbc.Card(dbc.CardBody(children), className="chart-card")
