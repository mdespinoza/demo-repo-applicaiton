"""Tab 1: Military Equipment Transfers visualization."""

import io
import json

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.components.kpi_card import kpi_card
from app.components.chart_container import chart_container
from app.logging_config import get_logger
from app.data.loader import load_equipment
from app.config import PLOTLY_TEMPLATE, COLORS, DEMIL_LABELS, STATE_POPULATION, CENSUS_REGIONS, REGION_COLORS

logger = get_logger(__name__)


def layout():
    df = load_equipment()
    states = sorted(df["State"].dropna().unique())
    categories = sorted(df["Category"].dropna().unique())
    years = df["Year"].dropna()
    min_year = int(years.min()) if len(years) > 0 else 1990
    max_year = int(years.max()) if len(years) > 0 else 2021

    return html.Div(
        [
            # Filtered data store
            dcc.Store(id="equip-filtered-store"),
            # Filters
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("States", className="filter-label"),
                            dcc.Dropdown(
                                id="equip-state-filter",
                                options=[{"label": s, "value": s} for s in states],
                                multi=True,
                                placeholder="All States",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Year Range", className="filter-label"),
                            dcc.RangeSlider(
                                id="equip-year-slider",
                                min=min_year,
                                max=max_year,
                                value=[min_year, max_year],
                                marks={y: str(y) for y in range(min_year, max_year + 1, 5)},
                                step=1,
                                tooltip={"placement": "bottom"},
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Category", className="filter-label"),
                            dcc.Dropdown(
                                id="equip-category-filter",
                                options=[{"label": c, "value": c} for c in categories],
                                multi=True,
                                placeholder="All Categories",
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="filter-panel",
            ),
            # KPI cards
            dbc.Row(id="equip-kpis"),
            # --- Temporal + Top Equipment ---
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "equip-timeline",
                            "Transfers Over Time",
                            height=450,
                            info=(
                                "Animated bar chart tracking cumulative transfer quantities"
                                " over time for the top 5 equipment categories. Press play"
                                " to watch transfers accumulate year by year."
                            ),
                        ),
                        md=7,
                    ),
                    dbc.Col(
                        [
                            chart_container(
                                "equip-top-items",
                                "Top 15 Equipment Types by Quantity",
                                info=(
                                    "Horizontal bar chart ranking the 15 most frequently"
                                    " transferred equipment types by total quantity"
                                ),
                            ),
                        ],
                        md=5,
                    ),
                ]
            ),
            # --- Geographic Overview ---
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            [
                                                html.Span("Equipment Transfers by State"),
                                                html.I(
                                                    className="bi bi-info-circle ms-2 chart-info-icon",
                                                    id="equip-choropleth-info-icon",
                                                ),
                                            ],
                                            className="chart-title",
                                            style={"display": "flex", "alignItems": "center"},
                                        ),
                                        dbc.Tooltip(
                                            "Choropleth map showing geographic distribution"
                                            " of military equipment transfers. Toggle between"
                                            " total acquisition value and item count using"
                                            " the radio buttons above.",
                                            target="equip-choropleth-info-icon",
                                            placement="right",
                                        ),
                                        dbc.RadioItems(
                                            id="equip-map-metric",
                                            options=[
                                                {"label": "Acquisition Value", "value": "value"},
                                                {"label": "Item Count", "value": "count"},
                                            ],
                                            value="value",
                                            inline=True,
                                            className="mb-2",
                                        ),
                                        dcc.Loading(
                                            dcc.Graph(id="equip-choropleth", style={"height": "450px"}), type="circle"
                                        ),
                                    ]
                                ),
                                className="chart-card",
                            ),
                        ],
                        md=7,
                    ),
                    dbc.Col(
                        chart_container(
                            "equip-yoy",
                            "Year-over-Year Transfer Growth Rate",
                            info=(
                                "Bar chart showing annual percentage change in total"
                                " acquisition value. Green bars indicate growth,"
                                " red bars indicate decline."
                            ),
                        ),
                        md=5,
                    ),
                ]
            ),
            # Per-Capita Choropleth
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "equip-percapita",
                            "Per-Capita Equipment Value by State",
                            info=(
                                "Choropleth map showing equipment acquisition value"
                                " normalized by state population (2020 Census). Reveals"
                                " disproportionate transfers to smaller states."
                            ),
                        ),
                        md=12,
                    ),
                ]
            ),
            # --- Equipment Type Breakdowns ---
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "equip-demil",
                            "DEMIL Code Breakdown",
                            info=(
                                "Stacked bar chart showing equipment sensitivity/restriction"
                                " levels (DEMIL codes) across top categories by"
                                " acquisition value"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "equip-top-states",
                            "Top 10 States by Acquisition Value",
                            info=(
                                "Horizontal bar chart showing the 10 states with the highest"
                                " total equipment acquisition values, colored by census region"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # Treemap
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "equip-treemap",
                            "Acquisition Value by Category",
                            info=(
                                "Treemap showing relative acquisition value of equipment"
                                " grouped by category and item name. Larger rectangles"
                                " indicate higher value."
                            ),
                        ),
                        md=12,
                    ),
                ]
            ),
            # --- Rankings & Derived Metrics ---
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "equip-diversity",
                            "Average Value per Item by State",
                            info=(
                                "Horizontal bar chart showing average acquisition value per"
                                " transferred item for the top 25 states — reveals which"
                                " states receive more expensive equipment"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "equip-top-agencies",
                            "Top 20 Agencies by Acquisition Value",
                            info=(
                                "Horizontal bar chart showing the 20 agencies with the"
                                " highest total equipment acquisition values"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
        ],
        className="tab-content-wrapper",
    )


# ---------------------------------------------------------------------------
# 1. Filter callback — writes filtered DataFrame to dcc.Store as JSON
# ---------------------------------------------------------------------------
@callback(
    Output("equip-filtered-store", "data"),
    Input("equip-state-filter", "value"),
    Input("equip-year-slider", "value"),
    Input("equip-category-filter", "value"),
)
def update_equip_store(states, year_range, categories):
    logger.info(
        "Equipment filter callback: states=%s, years=%s, categories=%s", states, year_range, categories
    )
    df = load_equipment()

    # Apply filters
    if states:
        df = df[df["State"].isin(states)]
    if year_range:
        df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    if categories:
        df = df[df["Category"].isin(categories)]

    # Pre-compute aggregations shared by multiple callbacks
    state_value = df.groupby("State")["Acquisition Value"].sum()
    state_qty = df.groupby("State")["Quantity"].sum()
    kpis = {
        "total_items": int(df["Quantity"].sum()),
        "total_value": float(df["Acquisition Value"].sum()),
        "n_agencies": int(df["Agency Name"].nunique()),
        "n_states": int(df["State"].nunique()),
    }
    store = {
        "df": df.to_json(date_format='iso', orient='split'),
        "state_value": state_value.to_json(),
        "state_qty": state_qty.to_json(),
        "kpis": kpis,
    }
    return json.dumps(store)


# ---------------------------------------------------------------------------
# 2. KPI callback
# ---------------------------------------------------------------------------
@callback(
    Output("equip-kpis", "children"),
    Input("equip-filtered-store", "data"),
)
def update_equip_kpis(store_data):
    if store_data is None:
        return no_update

    data = json.loads(store_data)
    kpis = data["kpis"]

    # KPIs — read from pre-computed values
    total_items = f"{kpis['total_items']:,}"
    total_value = f"${kpis['total_value']:,.0f}"
    n_agencies = f"{kpis['n_agencies']:,}"
    n_states = str(kpis['n_states'])
    kpis = dbc.Row(
        [
            dbc.Col(
                kpi_card(
                    "Total Items",
                    total_items,
                    color=COLORS["secondary"],
                    info="Total quantity of all equipment items transferred under the 1033 Program",
                ),
                md=3,
            ),
            dbc.Col(
                kpi_card(
                    "Total Value",
                    total_value,
                    color=COLORS["success"],
                    info="Combined acquisition value of all transferred military equipment",
                ),
                md=3,
            ),
            dbc.Col(
                kpi_card(
                    "Agencies Served",
                    n_agencies,
                    color=COLORS["warning"],
                    info="Number of unique law enforcement agencies that received equipment",
                ),
                md=3,
            ),
            dbc.Col(
                kpi_card(
                    "States & Territories",
                    n_states,
                    color=COLORS["info"],
                    info="Number of US states and territories with recorded equipment transfers",
                ),
                md=3,
            ),
        ]
    )

    return kpis


# ---------------------------------------------------------------------------
# 3. Maps callback — choropleth + per-capita + YoY
# ---------------------------------------------------------------------------
@callback(
    Output("equip-choropleth", "figure"),
    Output("equip-percapita", "figure"),
    Output("equip-yoy", "figure"),
    Input("equip-filtered-store", "data"),
    Input("equip-map-metric", "value"),
)
def update_equip_maps(store_data, map_metric):
    if store_data is None:
        return no_update, no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient='split')
    state_value_series = pd.read_json(io.StringIO(data["state_value"]), typ='series')
    state_qty_series = pd.read_json(io.StringIO(data["state_qty"]), typ='series')

    # Choropleth — use pre-computed series
    if map_metric == "value":
        state_agg = state_value_series.reset_index()
        state_agg.columns = ["State", "Value"]
        color_col = "Value"
        color_label = "Acquisition Value ($)"
    else:
        state_agg = state_qty_series.reset_index()
        state_agg.columns = ["State", "Value"]
        color_col = "Value"
        color_label = "Item Count"

    choropleth = px.choropleth(
        state_agg,
        locations="State",
        locationmode="USA-states",
        color=color_col,
        color_continuous_scale="Blues",
        scope="usa",
        template=PLOTLY_TEMPLATE,
        labels={"Value": color_label},
    )
    choropleth.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_colorbar=dict(title=color_label, thickness=15),
        geo=dict(
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
    )

    # --- Per-Capita Equipment Value — use pre-computed state_value_series ---
    pc = state_value_series.reset_index()
    pc.columns = ["State", "Total Value"]
    pc["Population"] = pc["State"].map(STATE_POPULATION)
    pc = pc.dropna(subset=["Population"])
    pc["Per Capita Value"] = pc["Total Value"] / pc["Population"]

    percapita_fig = px.choropleth(
        pc,
        locations="State",
        locationmode="USA-states",
        color="Per Capita Value",
        color_continuous_scale="Reds",
        scope="usa",
        template=PLOTLY_TEMPLATE,
        hover_data={"Total Value": ":$,.0f", "Population": ":,"},
    )
    percapita_fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_colorbar=dict(title="$/Person", thickness=15),
        geo=dict(
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
        height=450,
    )

    # --- Year-over-Year Growth Rate ---
    yearly_val = df.dropna(subset=["Year"]).groupby("Year")["Acquisition Value"].sum().sort_index()
    if len(yearly_val) > 1:
        yoy_pct = yearly_val.pct_change().dropna() * 100
        yoy_df = pd.DataFrame({"Year": yoy_pct.index.astype(int), "Growth Rate (%)": yoy_pct.values})
        bar_colors = [COLORS["success"] if v >= 0 else COLORS["danger"] for v in yoy_df["Growth Rate (%)"]]

        yoy_fig = go.Figure(
            go.Bar(
                x=yoy_df["Year"],
                y=yoy_df["Growth Rate (%)"],
                marker_color=bar_colors,
                hovertemplate="Year: %{x}<br>Growth: %{y:.1f}%<extra></extra>",
            )
        )
    else:
        yoy_fig = go.Figure()
    yoy_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Year", dtick=2),
        yaxis=dict(title="Growth Rate (%)", zeroline=True, zerolinecolor="rgba(255,255,255,0.3)"),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    return choropleth, percapita_fig, yoy_fig


# ---------------------------------------------------------------------------
# 4. Bars callback — top items + top agencies + top states + avg value
# ---------------------------------------------------------------------------
@callback(
    Output("equip-top-items", "figure"),
    Output("equip-top-agencies", "figure"),
    Output("equip-top-states", "figure"),
    Output("equip-diversity", "figure"),
    Input("equip-filtered-store", "data"),
)
def update_equip_bars(store_data):
    if store_data is None:
        return no_update, no_update, no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient='split')
    state_value_series = pd.read_json(io.StringIO(data["state_value"]), typ='series')

    # Top 15 items by quantity
    top_items = df.groupby("Item Name")["Quantity"].sum().nlargest(15).reset_index()
    top_items_fig = px.bar(
        top_items,
        x="Quantity",
        y="Item Name",
        orientation="h",
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=[COLORS["secondary"]],
    )
    top_items_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        yaxis=dict(autorange="reversed", title=""),
        xaxis=dict(title="Quantity"),
        height=450,
    )

    # Top agencies
    top_agencies = df.groupby("Agency Name")["Acquisition Value"].sum().nlargest(20).reset_index()
    agencies_fig = px.bar(
        top_agencies,
        x="Acquisition Value",
        y="Agency Name",
        orientation="h",
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=[COLORS["success"]],
    )
    agencies_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        yaxis=dict(autorange="reversed", title=""),
        xaxis=dict(title="Acquisition Value ($)"),
        height=500,
    )

    # --- Top 10 States by Acquisition Value — use pre-computed ---
    top_states_df = state_value_series.nlargest(10).reset_index()
    top_states_df.columns = ["State", "Value"]
    top_states_df["Region"] = top_states_df["State"].map(CENSUS_REGIONS).fillna("Other")
    top_states_df = top_states_df.sort_values("Value", ascending=True)

    top_states_fig = px.bar(
        top_states_df,
        x="Value",
        y="State",
        orientation="h",
        template=PLOTLY_TEMPLATE,
        color="Region",
        color_discrete_map=REGION_COLORS,
        labels={"Value": "Acquisition Value ($)", "State": ""},
    )
    top_states_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    # --- Average Value per Item by State ---
    state_avg = (
        df.groupby("State")
        .agg(
            total_value=("Acquisition Value", "sum"),
            total_qty=("Quantity", "sum"),
        )
        .reset_index()
    )
    state_avg = state_avg[state_avg["total_qty"] > 0]
    state_avg["Avg Value per Item"] = state_avg["total_value"] / state_avg["total_qty"]
    state_avg = state_avg.nlargest(25, "Avg Value per Item").sort_values("Avg Value per Item", ascending=True)

    diversity_fig = px.bar(
        state_avg,
        x="Avg Value per Item",
        y="State",
        orientation="h",
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=[COLORS["accent"]],
        hover_data={"total_value": ":$,.0f", "total_qty": ":,"},
    )
    diversity_fig.update_layout(
        yaxis=dict(title=""),
        xaxis=dict(title="Average Value per Item ($)"),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    return top_items_fig, agencies_fig, top_states_fig, diversity_fig


# ---------------------------------------------------------------------------
# 5. Timeline callback — animated line chart
# ---------------------------------------------------------------------------
@callback(
    Output("equip-timeline", "figure"),
    Input("equip-filtered-store", "data"),
)
def update_equip_timeline(store_data):
    if store_data is None:
        return no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient='split')

    # Timeline — animated line chart with play button
    timeline_df = df.dropna(subset=["Year"]).copy()
    if len(timeline_df) > 0:
        top_cats = timeline_df.groupby("Category")["Quantity"].sum().nlargest(5).index.tolist()
        timeline_df = timeline_df[timeline_df["Category"].isin(top_cats)]
        timeline_agg = timeline_df.groupby(["Year", "Category"])["Quantity"].sum().reset_index()
        timeline_agg["Year"] = timeline_agg["Year"].astype(int)
        all_years = sorted(timeline_agg["Year"].unique())
        y_max = timeline_agg["Quantity"].max() * 1.1

        # Build frames — each frame shows data up to that year
        frames = []
        for yr in all_years:
            frame_df = timeline_agg[timeline_agg["Year"] <= yr]
            frame_traces = []
            for cat in top_cats:
                cat_df = frame_df[frame_df["Category"] == cat].sort_values("Year")
                frame_traces.append(
                    go.Scatter(
                        x=cat_df["Year"],
                        y=cat_df["Quantity"],
                        mode="lines+markers",
                        name=cat,
                    )
                )
            frames.append(go.Frame(data=frame_traces, name=str(yr)))

        # Initial frame (first year only)
        init_df = timeline_agg[timeline_agg["Year"] <= all_years[0]]
        timeline_fig = go.Figure(
            data=[
                go.Scatter(
                    x=init_df[init_df["Category"] == cat].sort_values("Year")["Year"],
                    y=init_df[init_df["Category"] == cat].sort_values("Year")["Quantity"],
                    mode="lines+markers",
                    name=cat,
                )
                for cat in top_cats
            ],
            frames=frames,
        )
        timeline_fig.update_layout(
            xaxis=dict(range=[min(all_years) - 0.5, max(all_years) + 0.5], title="Year", dtick=2),
            yaxis=dict(range=[0, y_max], title="Quantity"),
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    x=0.0,
                    y=-0.12,
                    xanchor="left",
                    bgcolor="#1A2332",
                    font=dict(color="#E2E8F0"),
                    buttons=[
                        dict(
                            label="Play",
                            method="animate",
                            args=[None, {"frame": {"duration": 400, "redraw": True}, "fromcurrent": True}],
                        ),
                        dict(
                            label="Pause",
                            method="animate",
                            args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                        ),
                    ],
                )
            ],
            sliders=[
                dict(
                    active=0,
                    steps=[
                        dict(
                            args=[[str(yr)], {"frame": {"duration": 400, "redraw": True}, "mode": "immediate"}],
                            method="animate",
                            label=str(yr),
                        )
                        for yr in all_years
                    ],
                    x=0.15,
                    len=0.85,
                    y=-0.12,
                    currentvalue=dict(prefix="Year: ", font=dict(color="#E2E8F0")),
                    font=dict(color="#E2E8F0"),
                    bgcolor="#1A2332",
                    bordercolor="rgba(99,125,175,0.3)",
                )
            ],
        )
    else:
        timeline_fig = go.Figure()
    timeline_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=0, r=10, t=10, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=450,
    )

    return timeline_fig


# ---------------------------------------------------------------------------
# 6. Categories callback — treemap + DEMIL
# ---------------------------------------------------------------------------
@callback(
    Output("equip-treemap", "figure"),
    Output("equip-demil", "figure"),
    Input("equip-filtered-store", "data"),
)
def update_equip_categories(store_data):
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient='split')

    # Treemap
    treemap_df = (
        df.groupby(["Category", "Item Name"])
        .agg(Value=("Acquisition Value", "sum"), Count=("Quantity", "sum"))
        .reset_index()
    )
    treemap_df = treemap_df[treemap_df["Value"] > 0]
    if len(treemap_df) > 0:
        treemap_df = (
            treemap_df.sort_values("Value", ascending=False).groupby("Category").head(10).reset_index(drop=True)
        )
        treemap_fig = px.treemap(
            treemap_df,
            path=["Category", "Item Name"],
            values="Value",
            template=PLOTLY_TEMPLATE,
            color="Value",
            color_continuous_scale="Blues",
        )
    else:
        treemap_fig = go.Figure()
    treemap_fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=450)

    # --- DEMIL Code Breakdown ---
    demil_df = df.copy()
    demil_df["DEMIL Label"] = demil_df["DEMIL Code"].map(DEMIL_LABELS).fillna(demil_df["DEMIL Code"])
    # Top 8 categories by value for readability
    top_demil_cats = demil_df.groupby("Category")["Acquisition Value"].sum().nlargest(8).index
    demil_agg = (
        demil_df[demil_df["Category"].isin(top_demil_cats)]
        .groupby(["Category", "DEMIL Label"])["Acquisition Value"]
        .sum()
        .reset_index()
    )

    if len(demil_agg) > 0:
        demil_fig = px.bar(
            demil_agg,
            x="Acquisition Value",
            y="Category",
            color="DEMIL Label",
            orientation="h",
            template=PLOTLY_TEMPLATE,
        )
    else:
        demil_fig = go.Figure()
    demil_fig.update_layout(
        barmode="stack",
        yaxis=dict(title="", categoryorder="total ascending"),
        xaxis=dict(title="Acquisition Value ($)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    return treemap_fig, demil_fig
