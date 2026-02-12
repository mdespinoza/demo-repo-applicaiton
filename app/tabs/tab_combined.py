"""Tab 5: Combined Military Insights (cross-dataset analysis)."""

import io
import json

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State, no_update
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from app.components.chart_container import chart_container
from app.data.loader import load_equipment, load_bases
from app.config import (
    PLOTLY_TEMPLATE,
    COLORS,
    STATE_ABBREV_TO_NAME,
    STATE_NAME_TO_ABBREV,
    CENSUS_REGIONS,
    REGION_COLORS,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


def _build_combined_data():
    """Join equipment and bases data by state."""
    equip_df = load_equipment()
    bases_df = load_bases()

    # Equipment aggregation by state
    equip_by_state = (
        equip_df.groupby("State")
        .agg(
            equipment_value=("Acquisition Value", "sum"),
            equipment_count=("Quantity", "sum"),
            n_agencies=("Agency Name", "nunique"),
        )
        .reset_index()
    )
    equip_by_state.rename(columns={"State": "state_abbrev"}, inplace=True)

    # Bases aggregation by state - convert full name to abbreviation
    bases_df["state_abbrev"] = bases_df["State Terr"].map(STATE_NAME_TO_ABBREV)
    bases_by_state = (
        bases_df.groupby("state_abbrev")
        .agg(
            base_count=("Site Name", "nunique"),
        )
        .reset_index()
    )

    # Also get component/branch counts per state
    branch_by_state = bases_df.groupby(["state_abbrev", "COMPONENT"]).size().reset_index(name="branch_bases")

    # Join
    combined = pd.merge(equip_by_state, bases_by_state, on="state_abbrev", how="outer").fillna(0)
    combined["state_name"] = combined["state_abbrev"].map(STATE_ABBREV_TO_NAME)
    combined["region"] = combined["state_abbrev"].map(CENSUS_REGIONS).fillna("Other")

    return combined, branch_by_state, equip_df, bases_df


def layout():
    """Build the Combined Intelligence tab layout with filters and chart containers.

    Returns:
        dash.html.Div: Complete tab layout with filter panel and cross-dataset charts.
    """
    return html.Div(
        [
            # --- Intermediate data store + CSV download ---
            dcc.Store(id="combined-filtered-store"),
            dcc.Download(id="combined-download-csv"),
            # --- NEW FILTER PANEL ---
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Region", className="filter-label"),
                            dcc.Dropdown(
                                id="combined-region-filter",
                                options=[{"label": r, "value": r} for r in ["Northeast", "Midwest", "South", "West"]],
                                multi=True,
                                placeholder="All Regions",
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Minimum Bases", className="filter-label"),
                            dcc.Slider(
                                id="combined-min-bases",
                                min=0,
                                max=50,
                                value=0,
                                step=1,
                                marks={0: "0", 10: "10", 20: "20", 30: "30", 40: "40", 50: "50"},
                                tooltip={"placement": "bottom"},
                            ),
                        ],
                        md=6,
                    ),
                ],
                className="filter-panel",
                role="search",
                **{"aria-label": "Combined data filters"},
            ),
            # Export button
            dbc.Row(
                dbc.Col(
                    html.Button(
                        [
                            html.I(className="bi bi-download me-2", **{"aria-hidden": "true"}),
                            "Export Combined Data (CSV)",
                        ],
                        id="combined-export-btn",
                        className="btn btn-outline-info btn-sm",
                        **{"aria-label": "Download filtered combined data as CSV"},
                    ),
                    width="auto",
                ),
                className="mb-2",
                justify="end",
            ),
            # --- Overview ---
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "combined-temporal",
                            "Temporal Equipment Overlay",
                            height=500,
                            info=(
                                "Bar chart of yearly equipment acquisition value with a"
                                " reference line showing total base count for context"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "combined-dual-map",
                            "Equipment Value + Base Locations",
                            height=500,
                            info=(
                                "Dual-layer map: blue choropleth shows equipment acquisition"
                                " value by state, red dots mark military base locations"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # --- State-Level Comparisons ---
            # Scatter + Quadrant (both plot bases vs equipment as scatter)
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "combined-scatter",
                            "Base Count vs Equipment Value by State",
                            info=(
                                "Scatter plot showing correlation between number of bases and"
                                " equipment value per state. Bubble size reflects equipment"
                                " count. OLS trendline fitted."
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "combined-quadrant",
                            "Quadrant Analysis",
                            info=(
                                "Scatter plot with median dividers creating four quadrants:"
                                " high/low base count vs high/low equipment value for"
                                " strategic assessment"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # Butterfly + Equip-per-Base (both are state-level horizontal bar rankings)
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "combined-butterfly",
                            "Bases vs Equipment Value (Top 20 States)",
                            info=(
                                "Butterfly chart comparing normalized base counts (left) and"
                                " equipment values (right) for the top 20 states"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "combined-equip-per-base",
                            "Equipment-per-Base Ratio (Top 25)",
                            info=(
                                "Horizontal bar chart showing equipment value divided by number"
                                " of bases per state — identifies states with high equipment"
                                " relative to military presence"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # --- Aggregate Summaries ---
            # Regional Radar + Combined Ranking
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "combined-radar",
                            "Regional Comparison Radar",
                            info=(
                                "Radar chart comparing regions across four dimensions:"
                                " equipment value, equipment count, base count, and number"
                                " of agencies (all normalized 0-100)"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "combined-ranking",
                            "Combined State Ranking",
                            info=(
                                "Composite score ranking of top 25 states (50% base count"
                                " + 50% equipment value), colored by census region"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # --- Multi-Dimensional Cross-Cuts ---
            # Heatmap + Agency Bubble
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "combined-heatmap",
                            "Branch vs Equipment Category Heatmap",
                            info=(
                                "Heatmap of equipment values (log10 scale) across military"
                                " branches and top 10 equipment categories"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "combined-bubble",
                            "Agency Reach Bubble Chart",
                            info=(
                                "Bubble chart showing the three-way relationship:"
                                " agencies served (x), base count (y), and equipment"
                                " value (bubble size)"
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
# Filter callback: builds combined data and writes to dcc.Store
# ---------------------------------------------------------------------------
@callback(
    Output("combined-filtered-store", "data"),
    Input("combined-region-filter", "value"),
    Input("combined-min-bases", "value"),
)
def update_combined_store(regions, min_bases):
    """Build combined dataset, apply filters, and store pre-computed aggregations.

    Args:
        regions: List of selected census regions, or None for all.
        min_bases: Minimum base count threshold per state.

    Returns:
        str: JSON-encoded dict with combined data, yearly values, regional aggs, etc.
    """
    logger.info("Combined filter callback: regions=%s, min_bases=%s", regions, min_bases)
    combined, branch_by_state, equip_df, bases_df = _build_combined_data()

    # Apply filters
    if regions:
        combined = combined[combined["region"].isin(regions)]
    if min_bases and min_bases > 0:
        combined = combined[combined["base_count"] >= min_bases]

    selected_states = set(combined["state_abbrev"].dropna())

    # Pre-compute yearly equipment values for temporal chart
    filtered_equip = equip_df[equip_df["State"].isin(selected_states)] if selected_states else equip_df
    yearly_val = filtered_equip.dropna(subset=["Year"]).groupby("Year")["Acquisition Value"].sum().reset_index()
    yearly_val.columns = ["Year", "Value"]

    # Pre-compute regional aggregation for radar
    region_agg = (
        combined.groupby("region")
        .agg(
            equipment_value=("equipment_value", "sum"),
            equipment_count=("equipment_count", "sum"),
            base_count=("base_count", "sum"),
            n_agencies=("n_agencies", "sum"),
        )
        .reset_index()
    )

    # Pre-compute heatmap data (branch vs category)
    branch_states = branch_by_state.groupby("COMPONENT")["state_abbrev"].apply(set).to_dict()
    if selected_states:
        branch_states = {k: v & selected_states for k, v in branch_states.items()}

    heat_data = []
    for branch, br_states in branch_states.items():
        branch_equip = equip_df[equip_df["State"].isin(br_states)]
        cat_values = branch_equip.groupby("Category")["Acquisition Value"].sum()
        for cat, val in cat_values.items():
            heat_data.append({"Branch": branch, "Category": cat, "Value": val})

    # Pre-compute base locations for map
    bases_df_loc = bases_df.dropna(subset=["lat", "lon"]).copy()
    bases_df_loc["state_abbrev"] = bases_df_loc["State Terr"].map(STATE_NAME_TO_ABBREV)
    if selected_states:
        bases_df_loc = bases_df_loc[bases_df_loc["state_abbrev"].isin(selected_states)]
    bases_map_data = bases_df_loc[["lat", "lon", "Site Name"]].to_json(orient="split")

    store_data = {
        "combined": combined.to_json(date_format="iso", orient="split"),
        "branch_by_state": branch_by_state.to_json(date_format="iso", orient="split"),
        "selected_states": list(selected_states),
        "yearly_val": yearly_val.to_json(orient="split"),
        "region_agg": region_agg.to_json(orient="split"),
        "heat_data": heat_data,
        "bases_map": bases_map_data,
    }
    return json.dumps(store_data)


# ---------------------------------------------------------------------------
# Maps callback: dual map + temporal overlay (2 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("combined-dual-map", "figure"),
    Output("combined-temporal", "figure"),
    Input("combined-filtered-store", "data"),
)
def update_combined_maps(store_data):
    """Generate dual-layer map and temporal equipment overlay figures.

    Args:
        store_data: JSON string from combined-filtered-store.

    Returns:
        tuple: (dual_fig, temporal_fig) Plotly Figure objects.
    """
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    combined = pd.read_json(io.StringIO(data["combined"]), orient="split")
    yearly_val = pd.read_json(io.StringIO(data["yearly_val"]), orient="split")
    bases_map = pd.read_json(io.StringIO(data["bases_map"]), orient="split")

    # 1. Dual-layer choropleth
    dual_fig = go.Figure()

    dual_fig.add_trace(
        go.Choropleth(
            locations=combined["state_abbrev"],
            z=combined["equipment_value"],
            locationmode="USA-states",
            colorscale="Blues",
            colorbar=dict(title="Equipment Value ($)", x=1.0, thickness=15),
            hovertemplate="<b>%{location}</b><br>Equipment Value: $%{z:,.0f}<extra></extra>",
        )
    )

    dual_fig.add_trace(
        go.Scattergeo(
            lat=bases_map["lat"],
            lon=bases_map["lon"],
            mode="markers",
            marker=dict(size=5, color=COLORS["danger"], opacity=0.6, symbol="circle"),
            name="Military Bases",
            hovertext=bases_map["Site Name"],
            hoverinfo="text",
        )
    )

    dual_fig.update_layout(
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
        template=PLOTLY_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    # --- Temporal Equipment Overlay ---
    total_bases = combined["base_count"].sum()

    temporal_fig = make_subplots(specs=[[{"secondary_y": True}]])
    if len(yearly_val) > 0:
        temporal_fig.add_trace(
            go.Bar(
                x=yearly_val["Year"],
                y=yearly_val["Value"],
                name="Acquisition Value",
                marker_color=COLORS["secondary"],
                opacity=0.8,
            ),
            secondary_y=False,
        )
        temporal_fig.add_trace(
            go.Scatter(
                x=[yearly_val["Year"].min(), yearly_val["Year"].max()],
                y=[total_bases, total_bases],
                mode="lines",
                name=f"Total Bases ({int(total_bases)})",
                line=dict(color=COLORS["danger"], width=2, dash="dash"),
            ),
            secondary_y=True,
        )
    temporal_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )
    temporal_fig.update_yaxes(title_text="Acquisition Value ($)", secondary_y=False)
    temporal_fig.update_yaxes(title_text="Base Count", secondary_y=True)

    return dual_fig, temporal_fig


# ---------------------------------------------------------------------------
# Scatter callback: scatter + quadrant + bubble (3 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("combined-scatter", "figure"),
    Output("combined-quadrant", "figure"),
    Output("combined-bubble", "figure"),
    Input("combined-filtered-store", "data"),
)
def update_combined_scatter(store_data):
    """Generate correlation scatter, quadrant analysis, and agency bubble charts.

    Args:
        store_data: JSON string from combined-filtered-store.

    Returns:
        tuple: (scatter_fig, quadrant_fig, bubble_fig) Plotly Figure objects.
    """
    if store_data is None:
        return no_update, no_update, no_update

    data = json.loads(store_data)
    combined = pd.read_json(io.StringIO(data["combined"]), orient="split")

    # 2. Correlation scatter
    combined_filtered = combined[(combined["base_count"] > 0) & (combined["equipment_value"] > 0)].copy()

    scatter_fig = px.scatter(
        combined_filtered,
        x="base_count",
        y="equipment_value",
        size="equipment_count",
        color="region",
        color_discrete_map=REGION_COLORS,
        hover_name="state_name",
        trendline="ols",
        template=PLOTLY_TEMPLATE,
        labels={"base_count": "Number of Bases", "equipment_value": "Equipment Value ($)"},
        size_max=40,
    )
    scatter_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    # --- Quadrant Analysis ---
    quad_df = combined[(combined["base_count"] > 0) & (combined["equipment_value"] > 0)].copy()

    if len(quad_df) > 0:
        med_bases = quad_df["base_count"].median()
        med_value = quad_df["equipment_value"].median()

        quadrant_fig = px.scatter(
            quad_df,
            x="base_count",
            y="equipment_value",
            color="region",
            color_discrete_map=REGION_COLORS,
            hover_name="state_name",
            template=PLOTLY_TEMPLATE,
            labels={"base_count": "Number of Bases", "equipment_value": "Equipment Value ($)"},
        )
        # Add median lines
        quadrant_fig.add_hline(
            y=med_value,
            line_dash="dash",
            line_color="rgba(255,255,255,0.3)",
            annotation_text="Median Value",
            annotation_position="top left",
        )
        quadrant_fig.add_vline(
            x=med_bases,
            line_dash="dash",
            line_color="rgba(255,255,255,0.3)",
            annotation_text="Median Bases",
            annotation_position="top right",
        )
    else:
        quadrant_fig = go.Figure()

    quadrant_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    # --- Agency Reach Bubble Chart ---
    bubble_df = combined[(combined["n_agencies"] > 0) & (combined["base_count"] > 0)].copy()

    if len(bubble_df) > 0:
        bubble_fig = px.scatter(
            bubble_df,
            x="n_agencies",
            y="base_count",
            size="equipment_value",
            color="region",
            color_discrete_map=REGION_COLORS,
            hover_name="state_name",
            template=PLOTLY_TEMPLATE,
            size_max=50,
            labels={
                "n_agencies": "Agencies Served",
                "base_count": "Number of Bases",
                "equipment_value": "Equipment Value ($)",
            },
        )
    else:
        bubble_fig = go.Figure()

    bubble_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    return scatter_fig, quadrant_fig, bubble_fig


# ---------------------------------------------------------------------------
# Bars callback: butterfly + equip-per-base + ranking (3 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("combined-butterfly", "figure"),
    Output("combined-equip-per-base", "figure"),
    Output("combined-ranking", "figure"),
    Input("combined-filtered-store", "data"),
)
def update_combined_bars(store_data):
    """Generate butterfly chart, equipment-per-base ratio, and combined ranking.

    Args:
        store_data: JSON string from combined-filtered-store.

    Returns:
        tuple: (butterfly_fig, epb_fig, ranking_fig) Plotly Figure objects.
    """
    if store_data is None:
        return no_update, no_update, no_update

    data = json.loads(store_data)
    combined = pd.read_json(io.StringIO(data["combined"]), orient="split")

    # 3. Butterfly / paired bar
    top20 = combined.nlargest(20, "equipment_value").sort_values("equipment_value", ascending=True)
    butterfly_fig = go.Figure()
    max_bases = top20["base_count"].max() if top20["base_count"].max() > 0 else 1
    max_val = top20["equipment_value"].max() if top20["equipment_value"].max() > 0 else 1

    butterfly_fig.add_trace(
        go.Bar(
            y=top20["state_name"],
            x=-top20["base_count"] / max_bases * 100,
            orientation="h",
            name="Bases (normalized)",
            marker_color=COLORS["secondary"],
            hovertemplate="%{y}: %{customdata} bases<extra></extra>",
            customdata=top20["base_count"].astype(int),
        )
    )
    butterfly_fig.add_trace(
        go.Bar(
            y=top20["state_name"],
            x=top20["equipment_value"] / max_val * 100,
            orientation="h",
            name="Equipment Value (normalized)",
            marker_color=COLORS["success"],
            hovertemplate="%{y}: $%{customdata:,.0f}<extra></extra>",
            customdata=top20["equipment_value"],
        )
    )
    butterfly_fig.update_layout(
        barmode="relative",
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="<-- Bases | Equipment Value -->", showticklabels=False),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
    )

    # --- Equipment-per-Base Ratio ---
    epb = combined[combined["base_count"] > 0].copy()
    epb["equip_per_base"] = epb["equipment_value"] / epb["base_count"]
    epb = epb.nlargest(25, "equip_per_base").sort_values("equip_per_base", ascending=True)

    if len(epb) > 0:
        epb_fig = px.bar(
            epb,
            x="equip_per_base",
            y="state_name",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            color="region",
            color_discrete_map=REGION_COLORS,
            labels={"equip_per_base": "Equipment Value / Base", "state_name": ""},
        )
    else:
        epb_fig = go.Figure()
    epb_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    # 5. Combined ranking
    combined_for_rank = combined[(combined["base_count"] > 0) | (combined["equipment_value"] > 0)].copy()
    if len(combined_for_rank) > 0:
        max_b = combined_for_rank["base_count"].max()
        max_v = combined_for_rank["equipment_value"].max()
        combined_for_rank["norm_bases"] = combined_for_rank["base_count"] / max_b * 100 if max_b > 0 else 0
        combined_for_rank["norm_value"] = combined_for_rank["equipment_value"] / max_v * 100 if max_v > 0 else 0
        combined_for_rank["composite_score"] = (
            0.5 * combined_for_rank["norm_bases"] + 0.5 * combined_for_rank["norm_value"]
        )
        combined_for_rank = combined_for_rank.nlargest(25, "composite_score").sort_values(
            "composite_score", ascending=True
        )

        ranking_fig = px.bar(
            combined_for_rank,
            x="composite_score",
            y="state_name",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            color="region",
            color_discrete_map=REGION_COLORS,
            labels={"composite_score": "Composite Score", "state_name": ""},
        )
    else:
        ranking_fig = go.Figure()

    ranking_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    return butterfly_fig, epb_fig, ranking_fig


# ---------------------------------------------------------------------------
# Advanced callback: heatmap + radar (2 outputs)
# ---------------------------------------------------------------------------
@callback(
    Output("combined-heatmap", "figure"),
    Output("combined-radar", "figure"),
    Input("combined-filtered-store", "data"),
)
def update_combined_advanced(store_data):
    """Generate branch-vs-category heatmap and regional radar chart.

    Args:
        store_data: JSON string from combined-filtered-store.

    Returns:
        tuple: (heatmap_fig, radar_fig) Plotly Figure objects.
    """
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    heat_data = data["heat_data"]
    region_agg = pd.read_json(io.StringIO(data["region_agg"]), orient="split")

    # 4. Branch vs category heatmap (using pre-computed heat_data)
    if heat_data:
        heat_df = pd.DataFrame(heat_data)
        heat_pivot = heat_df.pivot_table(index="Branch", columns="Category", values="Value", fill_value=0)
        top_cats = heat_df.groupby("Category")["Value"].sum().nlargest(10).index
        heat_pivot = heat_pivot[[c for c in top_cats if c in heat_pivot.columns]]

        heatmap_fig = go.Figure(
            go.Heatmap(
                z=np.log10(heat_pivot.values + 1),
                x=heat_pivot.columns.tolist(),
                y=heat_pivot.index.tolist(),
                colorscale="YlOrRd",
                colorbar=dict(title="Log10(Value)"),
                hovertemplate="Branch: %{y}<br>Category: %{x}<br>Log Value: %{z:.2f}<extra></extra>",
            )
        )
    else:
        heatmap_fig = go.Figure()

    heatmap_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(tickangle=-45),
        margin=dict(l=0, r=10, t=10, b=80),
        height=450,
    )

    # --- Regional Comparison Radar (using pre-computed region_agg) ---

    radar_fig = go.Figure()
    categories_radar = ["Equipment Value", "Equipment Count", "Base Count", "Agencies"]

    if len(region_agg) > 0:
        for _, row in region_agg.iterrows():
            vals = [row["equipment_value"], row["equipment_count"], row["base_count"], row["n_agencies"]]
            # Normalize each to 0-100 within the radar
            max_vals = region_agg[["equipment_value", "equipment_count", "base_count", "n_agencies"]].max()
            norm_vals = []
            for v, m in zip(vals, max_vals):
                norm_vals.append(v / m * 100 if m > 0 else 0)
            norm_vals.append(norm_vals[0])  # close the polygon

            radar_fig.add_trace(
                go.Scatterpolar(
                    r=norm_vals,
                    theta=categories_radar + [categories_radar[0]],
                    fill="toself",
                    name=row["region"],
                    line=dict(color=REGION_COLORS.get(row["region"], COLORS["muted"])),
                    opacity=0.7,
                )
            )

    radar_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(99,125,175,0.2)"),
            angularaxis=dict(gridcolor="rgba(99,125,175,0.2)"),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=40, r=40, t=30, b=20),
        height=450,
    )

    return heatmap_fig, radar_fig


# ---------------------------------------------------------------------------
# CSV Export callback
# ---------------------------------------------------------------------------
@callback(
    Output("combined-download-csv", "data"),
    Input("combined-export-btn", "n_clicks"),
    State("combined-filtered-store", "data"),
    prevent_initial_call=True,
)
def export_combined_csv(n_clicks, store_data):
    """Export currently filtered combined data as a CSV download."""
    if not store_data:
        return no_update
    data = json.loads(store_data)
    combined = pd.read_json(io.StringIO(data["combined"]), orient="split")
    return dcc.send_data_frame(combined.to_csv, "combined_intel.csv", index=False)
