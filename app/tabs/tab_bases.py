"""Tab 3: Military Bases Map visualization."""

import io
import json

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, no_update
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from app.components.chart_container import chart_container
from app.data.loader import load_bases
from app.logging_config import get_logger
from app.config import PLOTLY_TEMPLATE, BRANCH_COLORS, COLORS, STATE_NAME_TO_ABBREV

logger = get_logger(__name__)


def get_branch_color(comp):
    for branch, color in BRANCH_COLORS.items():
        if branch.lower() in comp.lower():
            return color
    return BRANCH_COLORS.get("Other", "#9E9E9E")


def layout():
    df = load_bases()
    components = sorted(df["COMPONENT"].dropna().unique())
    statuses = sorted(df["Oper Stat"].dropna().unique())
    states = sorted(df["State Terr"].dropna().unique())
    joint_vals = sorted(df["Joint Base"].dropna().unique())

    return html.Div(
        [
            # Filtered data store
            dcc.Store(id="bases-filtered-store"),
            # Filters
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Component / Branch", className="filter-label"),
                            dcc.Dropdown(
                                id="bases-component-filter",
                                options=[{"label": c, "value": c} for c in components],
                                multi=True,
                                placeholder="All Components",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("Operational Status", className="filter-label"),
                            dcc.Dropdown(
                                id="bases-status-filter",
                                options=[{"label": s, "value": s} for s in statuses],
                                multi=True,
                                placeholder="All Statuses",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("State / Territory", className="filter-label"),
                            dcc.Dropdown(
                                id="bases-state-filter",
                                options=[{"label": s, "value": s} for s in states],
                                multi=True,
                                placeholder="All States",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("Joint Base", className="filter-label"),
                            dcc.Dropdown(
                                id="bases-joint-filter",
                                options=[{"label": j, "value": j} for j in joint_vals],
                                multi=True,
                                placeholder="All",
                            ),
                        ],
                        md=3,
                    ),
                ],
                className="filter-panel",
            ),
            # --- Geographic Overview ---
            dbc.Row(
                [
                    dbc.Col(
                        [
                            chart_container(
                                "bases-map",
                                "Military Installations Map",
                                height=500,
                                info=(
                                    "Interactive map showing locations of US military installations,"
                                    " color-coded by branch. Hover over markers for base details."
                                ),
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "bases-density",
                            "Base Concentration by State",
                            height=500,
                            info=(
                                "Choropleth showing the number of military installations per state"
                                " with individual base locations overlaid as white dots"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # --- High-Level Summaries ---
            # Status overview + Bases by branch
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "bases-status-donut",
                            "Operational Status Overview",
                            info=(
                                "Donut chart showing the proportion of bases by operational status"
                                " (Active, Closed, Surplus, etc.)"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "bases-by-branch",
                            "Bases by Branch",
                            info=(
                                "Stacked bar chart of base counts by military branch,"
                                " showing operational status breakdown"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # --- State-Level Detail ---
            # Bases by state + Joint base analysis
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "bases-by-state",
                            "Bases by State (Top 20)",
                            info="Stacked bar chart showing states with the most military bases, broken down by branch",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "bases-joint-analysis",
                            "Joint Base Analysis",
                            info=(
                                "Grouped bar chart showing which military branches participate in"
                                " joint base operations and how many bases are joint vs non-joint"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # --- Physical Characteristics ---
            # Base size + Area vs perimeter
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "bases-size-box",
                            "Base Size Distribution by Branch",
                            info=(
                                "Box plot showing the distribution of base area (AREA column)"
                                " for each military branch. Outliers indicate exceptionally"
                                " large installations."
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "bases-area-perimeter",
                            "Area vs Perimeter Scatter",
                            info=(
                                "Scatter plot comparing base area and perimeter by branch."
                                " Outliers indicate unusually shaped installations."
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # --- Drill-Down ---
            # Sunburst + small multiples
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "bases-sunburst",
                            "State / Component / Base Hierarchy",
                            info=(
                                "Sunburst chart showing the hierarchy of states, branches,"
                                " and individual bases. Click to drill down. Top 15 states shown."
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "bases-small-multiples",
                            "Geographic Distribution by Branch",
                            info="Small multiple maps showing base locations for each military branch separately",
                        ),
                        md=6,
                    ),
                ]
            ),
        ],
        className="tab-content-wrapper",
    )


# ---------------------------------------------------------------------------
# Filter callback: writes filtered DataFrame to dcc.Store
# ---------------------------------------------------------------------------
@callback(
    Output("bases-filtered-store", "data"),
    Input("bases-component-filter", "value"),
    Input("bases-status-filter", "value"),
    Input("bases-state-filter", "value"),
    Input("bases-joint-filter", "value"),
)
def update_bases_filter(components, statuses, states, joints):
    logger.info(
        "Bases callback: components=%s, statuses=%s, states=%s, joints=%s", components, statuses, states, joints
    )
    df = load_bases()

    if components:
        df = df[df["COMPONENT"].isin(components)]
    if statuses:
        df = df[df["Oper Stat"].isin(statuses)]
    if states:
        df = df[df["State Terr"].isin(states)]
    if joints:
        df = df[df["Joint Base"].isin(joints)]

    df = df.copy()
    # Pre-compute hovertext using vectorized string ops (replaces row-wise .apply)
    df["hovertext"] = (
        "<b>"
        + df["Site Name"].fillna("")
        + "</b><br>"
        + df["COMPONENT"].fillna("")
        + "<br>"
        + df["State Terr"].fillna("")
        + "<br>"
        + df["Oper Stat"].fillna("")
    )

    store = {
        "df": df.to_json(date_format="iso", orient="split"),
    }
    return json.dumps(store)


# ---------------------------------------------------------------------------
# Map + Density callback (2 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("bases-map", "figure"),
    Output("bases-density", "figure"),
    Input("bases-filtered-store", "data"),
)
def update_bases_maps(store_data):
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient="split")

    # Map - assign colors
    df_map = df.copy()

    map_fig = go.Figure()
    for comp in sorted(df_map["COMPONENT"].unique()):
        comp_df = df_map[df_map["COMPONENT"] == comp]
        map_fig.add_trace(
            go.Scattergeo(
                lat=comp_df["lat"],
                lon=comp_df["lon"],
                mode="markers",
                marker=dict(size=6, color=get_branch_color(comp), opacity=0.7),
                name=comp,
                hovertext=comp_df["hovertext"],
                hoverinfo="text",
            )
        )

    map_fig.update_layout(
        geo=dict(
            scope="usa",
            showland=True,
            landcolor="#1A2332",
            showlakes=True,
            lakecolor="#0F1726",
            showcountries=True,
            countrycolor="rgba(99,125,175,0.2)",
            showsubunits=True,
            subunitcolor="rgba(99,125,175,0.15)",
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        template=PLOTLY_TEMPLATE,
    )

    # --- Base Density (state-level choropleth) ---
    df_density = df.copy()
    df_density["state_abbrev"] = df_density["State Terr"].map(STATE_NAME_TO_ABBREV)
    state_counts = df_density.groupby("state_abbrev").size().reset_index(name="Base Count")

    density_fig = go.Figure()
    density_fig.add_trace(
        go.Choropleth(
            locations=state_counts["state_abbrev"],
            z=state_counts["Base Count"],
            locationmode="USA-states",
            colorscale="Hot",
            reversescale=True,
            colorbar=dict(title="Bases", thickness=15),
            hovertemplate="<b>%{location}</b><br>Bases: %{z}<extra></extra>",
        )
    )
    # Overlay individual base markers for detail
    density_fig.add_trace(
        go.Scattergeo(
            lat=df["lat"],
            lon=df["lon"],
            mode="markers",
            marker=dict(size=3, color="white", opacity=0.4),
            hovertext=df["Site Name"],
            hoverinfo="text",
            showlegend=False,
        )
    )
    density_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        geo=dict(
            scope="usa",
            bgcolor="rgba(0,0,0,0)",
            showland=True,
            landcolor="#1A2332",
            showlakes=True,
            lakecolor="#0F1726",
            showcountries=True,
            countrycolor="rgba(99,125,175,0.2)",
            showsubunits=True,
            subunitcolor="rgba(99,125,175,0.15)",
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=500,
    )

    return map_fig, density_fig


# ---------------------------------------------------------------------------
# Summary callback: by-branch + status donut (2 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("bases-by-branch", "figure"),
    Output("bases-status-donut", "figure"),
    Input("bases-filtered-store", "data"),
)
def update_bases_summary(store_data):
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient="split")

    # Bases by branch (stacked by status)
    branch_status = df.groupby(["COMPONENT", "Oper Stat"]).size().reset_index(name="Count")
    branch_fig = px.bar(
        branch_status,
        x="COMPONENT",
        y="Count",
        color="Oper Stat",
        template=PLOTLY_TEMPLATE,
    )
    branch_fig.update_layout(
        barmode="stack",
        xaxis=dict(title=""),
        yaxis=dict(title="Number of Bases"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    # --- Operational Status Donut ---
    status_counts = df["Oper Stat"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    status_fig = go.Figure(
        go.Pie(
            labels=status_counts["Status"],
            values=status_counts["Count"],
            hole=0.45,
            textinfo="label+percent",
            textposition="outside",
            marker=dict(
                colors=[
                    COLORS["success"],
                    COLORS["danger"],
                    COLORS["warning"],
                    COLORS["secondary"],
                    COLORS["accent"],
                    COLORS["info"],
                ]
            ),
        )
    )
    status_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=0, r=0, t=10, b=0),
        height=450,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    return branch_fig, status_fig


# ---------------------------------------------------------------------------
# State callback: by-state + joint analysis (2 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("bases-by-state", "figure"),
    Output("bases-joint-analysis", "figure"),
    Input("bases-filtered-store", "data"),
)
def update_bases_state(store_data):
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient="split")

    # Bases by state (top 20, stacked by component)
    state_comp = df.groupby(["State Terr", "COMPONENT"]).size().reset_index(name="Count")
    state_totals = state_comp.groupby("State Terr")["Count"].sum().nlargest(20).index
    state_comp = state_comp[state_comp["State Terr"].isin(state_totals)]

    state_fig = px.bar(
        state_comp,
        x="Count",
        y="State Terr",
        color="COMPONENT",
        orientation="h",
        template=PLOTLY_TEMPLATE,
        color_discrete_map={comp: get_branch_color(comp) for comp in state_comp["COMPONENT"].unique()},
    )
    state_fig.update_layout(
        barmode="stack",
        yaxis=dict(autorange="reversed", title="", categoryorder="total ascending"),
        xaxis=dict(title="Number of Bases"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    # --- Joint Base Analysis ---
    joint_comp = df.groupby(["Joint Base", "COMPONENT"]).size().reset_index(name="Count")
    if len(joint_comp) > 0:
        joint_fig = px.bar(
            joint_comp,
            x="COMPONENT",
            y="Count",
            color="Joint Base",
            barmode="group",
            template=PLOTLY_TEMPLATE,
        )
    else:
        joint_fig = go.Figure()
    joint_fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(title="Number of Bases"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    return state_fig, joint_fig


# ---------------------------------------------------------------------------
# Detail callback: sunburst + small multiples + size box + area-perimeter (4 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("bases-sunburst", "figure"),
    Output("bases-small-multiples", "figure"),
    Output("bases-size-box", "figure"),
    Output("bases-area-perimeter", "figure"),
    Input("bases-filtered-store", "data"),
)
def update_bases_detail(store_data):
    if store_data is None:
        return no_update, no_update, no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient="split")

    # Sunburst
    sun_df = df[["State Terr", "COMPONENT", "Site Name"]].copy()
    sun_df["count"] = 1
    top_states = df["State Terr"].value_counts().nlargest(15).index
    sun_df = sun_df[sun_df["State Terr"].isin(top_states)]

    sunburst_fig = px.sunburst(
        sun_df,
        path=["State Terr", "COMPONENT", "Site Name"],
        values="count",
        template=PLOTLY_TEMPLATE,
    )
    sunburst_fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=450)

    # Small multiples - mini map per branch
    branches = sorted(df["COMPONENT"].unique())
    n_branches = min(len(branches), 6)
    rows = 2
    cols = 3

    sm_fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=branches[:n_branches],
        specs=[[{"type": "scattergeo"} for _ in range(cols)] for _ in range(rows)],
    )

    for i, branch in enumerate(branches[:n_branches]):
        r, c = divmod(i, cols)
        branch_df = df[df["COMPONENT"] == branch]
        sm_fig.add_trace(
            go.Scattergeo(
                lat=branch_df["lat"],
                lon=branch_df["lon"],
                mode="markers",
                marker=dict(size=4, color=get_branch_color(branch), opacity=0.7),
                name=branch,
                showlegend=False,
                hovertext=branch_df["Site Name"],
            ),
            row=r + 1,
            col=c + 1,
        )

    for i in range(1, n_branches + 1):
        sm_fig.update_geos(
            scope="usa",
            showland=True,
            landcolor="#1A2332",
            showlakes=False,
            showcountries=False,
            selector=dict({"geo": f"geo{i}" if i > 1 else "geo"}),
        )

    geo_updates = {}
    for i in range(1, n_branches + 1):
        key = f"geo{i}" if i > 1 else "geo"
        geo_updates[key] = dict(
            scope="usa",
            showland=True,
            landcolor="#1A2332",
            showlakes=False,
            showcountries=False,
            bgcolor="rgba(0,0,0,0)",
        )
    sm_fig.update_layout(
        **geo_updates,
        template=PLOTLY_TEMPLATE,
        margin=dict(l=0, r=0, t=30, b=0),
        height=450,
        showlegend=False,
    )

    # --- Base Size by Branch ---
    area_df = df[df["AREA"] > 0].copy()
    if len(area_df) > 0:
        size_box_fig = px.box(
            area_df,
            x="COMPONENT",
            y="AREA",
            template=PLOTLY_TEMPLATE,
            color="COMPONENT",
            color_discrete_map={comp: get_branch_color(comp) for comp in area_df["COMPONENT"].unique()},
        )
    else:
        size_box_fig = go.Figure()
    size_box_fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(title="Area", type="log"),
        showlegend=False,
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    # --- Area vs Perimeter Scatter ---
    ap_df = df[(df["AREA"] > 0) & (df["PERIMETER"] > 0)].copy()
    if len(ap_df) > 0:
        ap_fig = px.scatter(
            ap_df,
            x="AREA",
            y="PERIMETER",
            color="COMPONENT",
            hover_name="Site Name",
            template=PLOTLY_TEMPLATE,
            color_discrete_map={comp: get_branch_color(comp) for comp in ap_df["COMPONENT"].unique()},
            log_x=True,
            log_y=True,
        )
    else:
        ap_fig = go.Figure()
    ap_fig.update_layout(
        xaxis=dict(title="Area (log scale)"),
        yaxis=dict(title="Perimeter (log scale)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    return sunburst_fig, sm_fig, size_box_fig, ap_fig
