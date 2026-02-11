"""Tab 4: Healthcare Documentation visualization."""
import re
from collections import Counter

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from app.components.chart_container import chart_container
from app.data.loader import load_healthcare
from app.config import PLOTLY_TEMPLATE, COLORS


def _extract_keywords(df):
    """Extract real medical keywords, filtering out specialty names and junk."""
    specialty_names = set(df["medical_specialty"].dropna().str.lower().unique())
    # Also catch partial specialty names
    spec_words = set()
    for s in specialty_names:
        for part in re.split(r"[/\-\s]+", s):
            part = part.strip().lower()
            if len(part) > 3:
                spec_words.add(part)

    all_keywords = []
    for kw_str in df["keywords"].dropna():
        parts = kw_str.split(",")
        # Skip first entry — it's typically the specialty name
        for kw in parts[1:]:
            kw = kw.strip().lower()
            if not kw or len(kw) <= 2 or len(kw) > 40:
                continue
            if kw in specialty_names or kw in spec_words:
                continue
            all_keywords.append(kw)
    return all_keywords


def layout():
    df = load_healthcare()
    specialties = sorted(df["medical_specialty"].dropna().unique())

    return html.Div([
        # Filters
        dbc.Row([
            dbc.Col([
                html.Label("Medical Specialty", className="filter-label"),
                dcc.Dropdown(
                    id="health-specialty-filter",
                    options=[{"label": s, "value": s} for s in specialties],
                    multi=True, placeholder="All Specialties",
                ),
            ], md=6),
            dbc.Col([
                html.Label("Keyword Search", className="filter-label"),
                dcc.Input(
                    id="health-keyword-search",
                    type="text", placeholder="Search keywords...",
                    debounce=True,
                    className="form-control",
                ),
            ], md=6),
        ], className="filter-panel"),

        # Specialty distribution + Resource demand quadrant
        dbc.Row([
            dbc.Col(chart_container("health-specialty-dist", "Records by Medical Specialty", info="Horizontal bar chart showing the count of medical documentation records per specialty"), md=6),
            dbc.Col(chart_container("health-demand-quadrant", "Resource Demand Quadrant", info="Scatter plot mapping each specialty by case volume (x) vs case complexity (avg transcription length, y). Top-right quadrant = high volume + high complexity = most resource-intensive specialties."), md=6),
        ]),

        # Box plot + Workload Pareto
        dbc.Row([
            dbc.Col(chart_container("health-boxplot", "Transcription Length by Specialty", info="Box plot showing the distribution of transcription lengths for the top 15 specialties. Box shows median and quartiles."), md=6),
            dbc.Col(chart_container("health-pareto", "Workload Concentration (Pareto)", info="Pareto chart showing how caseload concentrates across specialties. The line shows cumulative percentage — reveals that a few specialties account for most of the workload."), md=6),
        ]),

        # Resource allocation index + Top keywords
        dbc.Row([
            dbc.Col(chart_container("health-resource-index", "Resource Allocation Index", info="Composite score ranking specialties by estimated resource need (50% volume + 50% complexity). Higher scores indicate specialties requiring more staffing and infrastructure."), md=6),
            dbc.Col(chart_container("health-keywords", "Top 30 Medical Keywords", info="Most frequently occurring clinical terms extracted from medical documentation, excluding specialty names and boilerplate text"), md=6),
        ]),

        # DataTable
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody([
                    html.H5(
                        [html.Span("Documentation Records"),
                         html.I(className="bi bi-info-circle ms-2 chart-info-icon", id="health-datatable-info-icon")],
                        className="chart-title",
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    dbc.Tooltip(
                        "Searchable and sortable table of medical records. Click a row to expand the full transcription below.",
                        target="health-datatable-info-icon", placement="right",
                    ),
                    dash_table.DataTable(
                        id="health-datatable",
                        columns=[
                            {"name": "ID", "id": "Serial No"},
                            {"name": "Specialty", "id": "medical_specialty"},
                            {"name": "Sample Name", "id": "sample_name"},
                            {"name": "Description", "id": "description"},
                            {"name": "Length", "id": "transcription_length"},
                        ],
                        page_size=10,
                        sort_action="native",
                        filter_action="native",
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "left",
                            "padding": "8px",
                            "fontSize": "13px",
                            "maxWidth": "300px",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "backgroundColor": "#151D2E",
                            "color": "#E2E8F0",
                            "borderColor": "rgba(99, 125, 175, 0.12)",
                        },
                        style_header={
                            "backgroundColor": "#0B0F19",
                            "color": "#38BDF8",
                            "fontWeight": "bold",
                        },
                        style_data_conditional=[
                            {"if": {"row_index": "odd"}, "backgroundColor": "#111827"},
                        ],
                        row_selectable="single",
                    ),
                ]), className="chart-card"),
            ], md=12),
        ]),

        # Expanded transcription
        dbc.Row([
            dbc.Col([
                dbc.Collapse([
                    dbc.Card(dbc.CardBody([
                        html.H5("Full Transcription", className="chart-title"),
                        html.Div(id="health-transcription-text",
                                 style={"maxHeight": "400px", "overflowY": "auto", "whiteSpace": "pre-wrap",
                                        "fontSize": "13px", "lineHeight": "1.6"}),
                    ]), className="chart-card"),
                ], id="health-transcription-collapse", is_open=False),
            ], md=12),
        ]),
    ], className="tab-content-wrapper")


@callback(
    Output("health-specialty-dist", "figure"),
    Output("health-demand-quadrant", "figure"),
    Output("health-boxplot", "figure"),
    Output("health-pareto", "figure"),
    Output("health-resource-index", "figure"),
    Output("health-keywords", "figure"),
    Output("health-datatable", "data"),
    Input("health-specialty-filter", "value"),
    Input("health-keyword-search", "value"),
)
def update_healthcare(specialties, keyword):
    df = load_healthcare()

    if specialties:
        df = df[df["medical_specialty"].isin(specialties)]
    if keyword:
        df = df[df["keywords"].str.contains(keyword, case=False, na=False)]

    # --- Specialty Distribution ---
    spec_counts = df["medical_specialty"].value_counts().reset_index()
    spec_counts.columns = ["Specialty", "Count"]
    spec_fig = px.bar(
        spec_counts, x="Count", y="Specialty", orientation="h",
        template=PLOTLY_TEMPLATE, color_discrete_sequence=[COLORS["secondary"]],
    )
    spec_fig.update_layout(
        yaxis=dict(autorange="reversed", title="", categoryorder="total ascending"),
        xaxis=dict(title="Number of Records"),
        margin=dict(l=0, r=10, t=10, b=0), height=500,
    )

    # --- Resource Demand Quadrant ---
    # x = case volume, y = avg complexity (transcription length)
    spec_stats = df.groupby("medical_specialty").agg(
        volume=("medical_specialty", "size"),
        avg_complexity=("transcription_length", "mean"),
    ).reset_index()

    med_vol = spec_stats["volume"].median()
    med_comp = spec_stats["avg_complexity"].median()

    def assign_quadrant(row):
        if row["volume"] >= med_vol and row["avg_complexity"] >= med_comp:
            return "High Volume + Complex"
        elif row["volume"] >= med_vol:
            return "High Volume"
        elif row["avg_complexity"] >= med_comp:
            return "Complex Cases"
        return "Low Priority"

    spec_stats["Quadrant"] = spec_stats.apply(assign_quadrant, axis=1)
    quadrant_colors = {
        "High Volume + Complex": COLORS["danger"],
        "High Volume": COLORS["warning"],
        "Complex Cases": COLORS["info"],
        "Low Priority": COLORS["secondary"],
    }

    quadrant_fig = px.scatter(
        spec_stats, x="volume", y="avg_complexity",
        color="Quadrant", hover_name="medical_specialty",
        size="volume", size_max=30,
        template=PLOTLY_TEMPLATE,
        color_discrete_map=quadrant_colors,
        labels={"volume": "Case Volume", "avg_complexity": "Avg Complexity (chars)"},
    )
    quadrant_fig.add_hline(y=med_comp, line_dash="dash", line_color="rgba(255,255,255,0.25)")
    quadrant_fig.add_vline(x=med_vol, line_dash="dash", line_color="rgba(255,255,255,0.25)")
    quadrant_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0), height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
    )

    # --- Box Plot ---
    top_specs = df["medical_specialty"].value_counts().nlargest(15).index
    box_df = df[df["medical_specialty"].isin(top_specs)]
    box_fig = px.box(
        box_df, x="medical_specialty", y="transcription_length",
        color="medical_specialty",
        template=PLOTLY_TEMPLATE,
    )
    box_fig.update_layout(
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Transcription Length (chars)"),
        showlegend=False,
        margin=dict(l=0, r=10, t=10, b=80), height=450,
    )

    # --- Workload Pareto ---
    pareto_df = spec_counts.sort_values("Count", ascending=False).reset_index(drop=True)
    pareto_df["Cumulative %"] = (pareto_df["Count"].cumsum() / pareto_df["Count"].sum() * 100)
    # Show top 20 for readability
    pareto_df = pareto_df.head(20)

    pareto_fig = go.Figure()
    pareto_fig.add_trace(go.Bar(
        x=pareto_df["Specialty"], y=pareto_df["Count"],
        name="Records", marker_color=COLORS["secondary"],
        hovertemplate="%{x}<br>Records: %{y}<extra></extra>",
    ))
    pareto_fig.add_trace(go.Scatter(
        x=pareto_df["Specialty"], y=pareto_df["Cumulative %"],
        name="Cumulative %", yaxis="y2",
        mode="lines+markers", marker=dict(color=COLORS["warning"], size=6),
        line=dict(color=COLORS["warning"], width=2),
        hovertemplate="%{x}<br>Cumulative: %{y:.1f}%<extra></extra>",
    ))
    pareto_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Number of Records"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=40, t=10, b=80), height=450,
    )

    # --- Resource Allocation Index ---
    res_df = spec_stats.copy()
    if len(res_df) > 0:
        res_df["norm_vol"] = res_df["volume"] / res_df["volume"].max()
        res_df["norm_comp"] = res_df["avg_complexity"] / res_df["avg_complexity"].max()
        res_df["Resource Score"] = (res_df["norm_vol"] * 0.5 + res_df["norm_comp"] * 0.5) * 100
        res_df = res_df.nlargest(20, "Resource Score").sort_values("Resource Score", ascending=True)

        resource_fig = px.bar(
            res_df, x="Resource Score", y="medical_specialty", orientation="h",
            template=PLOTLY_TEMPLATE,
            color="Resource Score", color_continuous_scale="YlOrRd",
            labels={"medical_specialty": "", "Resource Score": "Resource Need Score"},
        )
        resource_fig.update_layout(
            coloraxis_colorbar=dict(title="Score", thickness=12),
            margin=dict(l=0, r=10, t=10, b=0), height=450,
        )
    else:
        resource_fig = go.Figure()
        resource_fig.update_layout(margin=dict(l=0, r=10, t=10, b=0), height=450)

    # --- Top 30 Medical Keywords (cleaned) ---
    all_keywords = _extract_keywords(df)
    kw_counts = Counter(all_keywords).most_common(30)
    if kw_counts:
        kw_df = pd.DataFrame(kw_counts, columns=["Keyword", "Count"])
        kw_fig = px.bar(
            kw_df, x="Count", y="Keyword", orientation="h",
            template=PLOTLY_TEMPLATE, color_discrete_sequence=[COLORS["success"]],
        )
        kw_fig.update_layout(
            yaxis=dict(autorange="reversed", title="", categoryorder="total ascending"),
            margin=dict(l=0, r=10, t=10, b=0), height=450,
        )
    else:
        kw_fig = go.Figure()
        kw_fig.update_layout(margin=dict(l=0, r=10, t=10, b=0), height=450)

    # DataTable data
    table_data = df[["Serial No", "medical_specialty", "sample_name", "description", "transcription_length"]].to_dict("records")

    return spec_fig, quadrant_fig, box_fig, pareto_fig, resource_fig, kw_fig, table_data


@callback(
    Output("health-transcription-collapse", "is_open"),
    Output("health-transcription-text", "children"),
    Input("health-datatable", "selected_rows"),
    State("health-datatable", "data"),
)
def show_transcription(selected_rows, data):
    if not selected_rows or not data:
        return False, ""

    row = data[selected_rows[0]]
    df = load_healthcare()
    record = df[df["Serial No"] == row["Serial No"]]
    if len(record) == 0:
        return False, ""

    transcription = record.iloc[0].get("transcription", "No transcription available.")
    return True, str(transcription)
