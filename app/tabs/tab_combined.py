"""Tab 5: Combined Military Insights (cross-dataset analysis)."""

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output
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
    return html.Div(
        [
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


@callback(
    Output("combined-dual-map", "figure"),
    Output("combined-scatter", "figure"),
    Output("combined-butterfly", "figure"),
    Output("combined-heatmap", "figure"),
    Output("combined-ranking", "figure"),
    Output("combined-temporal", "figure"),
    Output("combined-radar", "figure"),
    Output("combined-equip-per-base", "figure"),
    Output("combined-quadrant", "figure"),
    Output("combined-bubble", "figure"),
    Input("combined-region-filter", "value"),
    Input("combined-min-bases", "value"),
)
def update_combined(regions, min_bases):
    logger.info("Combined callback: regions=%s, min_bases=%s", regions, min_bases)
    combined, branch_by_state, equip_df, bases_df = _build_combined_data()

    # Apply filters
    if regions:
        combined = combined[combined["region"].isin(regions)]
    if min_bases and min_bases > 0:
        combined = combined[combined["base_count"] >= min_bases]

    # Filter equipment/bases data to match selected states
    selected_states = set(combined["state_abbrev"].dropna())

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

    bases_for_map = bases_df.dropna(subset=["lat", "lon"])
    if selected_states:
        bases_for_map = bases_for_map[bases_for_map["state_abbrev"].isin(selected_states)]
    dual_fig.add_trace(
        go.Scattergeo(
            lat=bases_for_map["lat"],
            lon=bases_for_map["lon"],
            mode="markers",
            marker=dict(size=5, color=COLORS["danger"], opacity=0.6, symbol="circle"),
            name="Military Bases",
            hovertext=bases_for_map["Site Name"],
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

    # 4. Branch vs category heatmap
    branch_states = branch_by_state.groupby("COMPONENT")["state_abbrev"].apply(set).to_dict()
    # Filter to selected states if filters active
    if selected_states:
        branch_states = {k: v & selected_states for k, v in branch_states.items()}

    heat_data = []
    for branch, br_states in branch_states.items():
        branch_equip = equip_df[equip_df["State"].isin(br_states)]
        cat_values = branch_equip.groupby("Category")["Acquisition Value"].sum()
        for cat, val in cat_values.items():
            heat_data.append({"Branch": branch, "Category": cat, "Value": val})

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

    # --- NEW CHART C3: Temporal Equipment Overlay ---
    filtered_equip = equip_df[equip_df["State"].isin(selected_states)] if selected_states else equip_df
    yearly_val = filtered_equip.dropna(subset=["Year"]).groupby("Year")["Acquisition Value"].sum().reset_index()
    yearly_val.columns = ["Year", "Value"]
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

    # --- NEW CHART C1: Regional Comparison Radar ---
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

    # --- NEW CHART C2: Equipment-per-Base Ratio ---
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

    # --- NEW CHART C4: Quadrant Analysis ---
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

    # --- NEW CHART C5: Agency Reach Bubble Chart ---
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

    return (
        dual_fig,
        scatter_fig,
        butterfly_fig,
        heatmap_fig,
        ranking_fig,
        temporal_fig,
        radar_fig,
        epb_fig,
        quadrant_fig,
        bubble_fig,
    )
