"""Tab 4: Healthcare Documentation visualization."""

import io
import json
import re
from collections import Counter

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State, dash_table, no_update
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.components.chart_container import chart_container
from app.data.loader import load_healthcare
from app.config import PLOTLY_TEMPLATE, COLORS
from app.logging_config import get_logger

logger = get_logger(__name__)


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
    """Build the Healthcare Documentation tab layout with filters and chart containers.

    Returns:
        dash.html.Div: Complete tab layout with filter panel, charts, and data table.
    """
    df = load_healthcare()
    specialties = sorted(df["medical_specialty"].dropna().unique())

    return html.Div(
        [
            # Filtered data store + CSV download
            dcc.Store(id="health-filtered-store"),
            dcc.Download(id="health-download-csv"),
            # Filters
            html.Div(
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Medical Specialty", className="filter-label"),
                                dcc.Dropdown(
                                    id="health-specialty-filter",
                                    options=[{"label": s, "value": s} for s in specialties],
                                    multi=True,
                                    placeholder="All Specialties",
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Keyword Search", className="filter-label"),
                                dcc.Input(
                                    id="health-keyword-search",
                                    type="text",
                                    placeholder="Search keywords...",
                                    debounce=True,
                                    className="form-control",
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="filter-panel",
                ),
                role="search",
                **{"aria-label": "Healthcare data filters"},
            ),
            # Export button
            dbc.Row(
                dbc.Col(
                    html.Button(
                        [
                            html.I(className="bi bi-download me-2", **{"aria-hidden": "true"}),
                            "Export Filtered Data (CSV)",
                        ],
                        id="health-export-btn",
                        className="btn btn-outline-info btn-sm",
                        **{"aria-label": "Download filtered healthcare data as CSV"},
                    ),
                    width="auto",
                ),
                className="mb-2",
                justify="end",
            ),
            # Specialty distribution + Resource demand quadrant
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "health-specialty-dist",
                            "Records by Medical Specialty",
                            info=(
                                "Horizontal bar chart showing the count of medical"
                                " documentation records per specialty"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "health-demand-quadrant",
                            "Resource Demand Quadrant",
                            info=(
                                "Scatter plot mapping each specialty by case volume (x) vs"
                                " case complexity (avg transcription length, y). Top-right"
                                " quadrant = high volume + high complexity = most"
                                " resource-intensive specialties."
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # Box plot + Workload Pareto
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "health-boxplot",
                            "Transcription Length by Specialty",
                            info=(
                                "Box plot showing the distribution of transcription lengths"
                                " for the top 15 specialties. Box shows median and quartiles."
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "health-pareto",
                            "Workload Concentration (Pareto)",
                            info=(
                                "Pareto chart showing how caseload concentrates across"
                                " specialties. The line shows cumulative percentage —"
                                " reveals that a few specialties account for most of"
                                " the workload."
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # Resource allocation index + Top keywords
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "health-resource-index",
                            "Resource Allocation Index",
                            info=(
                                "Composite score ranking specialties by estimated resource"
                                " need (50% volume + 50% complexity). Higher scores indicate"
                                " specialties requiring more staffing and infrastructure."
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "health-keywords",
                            "Top 30 Medical Keywords",
                            info=(
                                "Most frequently occurring clinical terms extracted from"
                                " medical documentation, excluding specialty names and"
                                " boilerplate text"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # DataTable
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            [
                                                html.Span("Documentation Records"),
                                                html.I(
                                                    className="bi bi-info-circle ms-2 chart-info-icon",
                                                    id="health-datatable-info-icon",
                                                ),
                                            ],
                                            className="chart-title",
                                            style={"display": "flex", "alignItems": "center"},
                                        ),
                                        dbc.Tooltip(
                                            "Searchable and sortable table of medical"
                                            " records. Click a row to expand the full"
                                            " transcription below.",
                                            target="health-datatable-info-icon",
                                            placement="right",
                                        ),
                                        dcc.Loading(
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
                                            type="circle",
                                            color="#38BDF8",
                                        ),
                                    ]
                                ),
                                className="chart-card",
                            ),
                        ],
                        md=12,
                    ),
                ]
            ),
            # Expanded transcription
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Collapse(
                                [
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5("Full Transcription", className="chart-title"),
                                                dcc.Loading(
                                                    html.Div(
                                                        id="health-transcription-text",
                                                        style={
                                                            "maxHeight": "400px",
                                                            "overflowY": "auto",
                                                            "whiteSpace": "pre-wrap",
                                                            "fontSize": "13px",
                                                            "lineHeight": "1.6",
                                                        },
                                                    ),
                                                    type="circle",
                                                    color="#38BDF8",
                                                ),
                                            ]
                                        ),
                                        className="chart-card",
                                    ),
                                ],
                                id="health-transcription-collapse",
                                is_open=False,
                            ),
                        ],
                        md=12,
                    ),
                ]
            ),
        ],
        className="tab-content-wrapper",
    )


# --- Filter callback: writes filtered DataFrame to dcc.Store ---
@callback(
    Output("health-filtered-store", "data"),
    Input("health-specialty-filter", "value"),
    Input("health-keyword-search", "value"),
)
def filter_healthcare_data(specialties, keyword):
    """Filter healthcare data by specialty and keyword, store pre-computed stats.

    Args:
        specialties: List of selected medical specialties, or None for all.
        keyword: Search string to filter by keyword column, or None.

    Returns:
        str: JSON-encoded dict with filtered DataFrame and specialty statistics.
    """
    logger.info("Healthcare filter callback: specialties=%s, keyword=%s", specialties, keyword)
    df = load_healthcare()

    if specialties:
        df = df[df["medical_specialty"].isin(specialties)]
    if keyword:
        df = df[df["keywords"].str.contains(keyword, case=False, na=False)]

    # Pre-compute specialty stats shared by multiple callbacks
    spec_counts = df["medical_specialty"].value_counts().reset_index()
    spec_counts.columns = ["Specialty", "Count"]

    spec_stats = (
        df.groupby("medical_specialty")
        .agg(
            volume=("medical_specialty", "size"),
            avg_complexity=("transcription_length", "mean"),
        )
        .reset_index()
    )

    store = {
        "df": df.to_json(date_format="iso", orient="split"),
        "spec_counts": spec_counts.to_json(orient="split"),
        "spec_stats": spec_stats.to_json(orient="split"),
    }
    return json.dumps(store)


# --- Specialty distribution + box plot (2 outputs) ---
@callback(
    Output("health-specialty-dist", "figure"),
    Output("health-boxplot", "figure"),
    Input("health-filtered-store", "data"),
)
def update_health_distribution(store_data):
    """Generate specialty distribution bar chart and transcription length box plot.

    Args:
        store_data: JSON string from health-filtered-store.

    Returns:
        tuple: (spec_fig, box_fig) Plotly Figure objects.
    """
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient="split")
    spec_counts = pd.read_json(io.StringIO(data["spec_counts"]), orient="split")

    # --- Specialty Distribution (uses pre-computed spec_counts) ---
    spec_fig = px.bar(
        spec_counts,
        x="Count",
        y="Specialty",
        orientation="h",
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=[COLORS["secondary"]],
    )
    spec_fig.update_layout(
        yaxis=dict(autorange="reversed", title="", categoryorder="total ascending"),
        xaxis=dict(title="Number of Records"),
        margin=dict(l=0, r=10, t=10, b=0),
        height=500,
    )

    # --- Box Plot ---
    top_specs = spec_counts.nlargest(15, "Count")["Specialty"]
    box_df = df[df["medical_specialty"].isin(top_specs)]
    box_fig = px.box(
        box_df,
        x="medical_specialty",
        y="transcription_length",
        color="medical_specialty",
        template=PLOTLY_TEMPLATE,
    )
    box_fig.update_layout(
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Transcription Length (chars)"),
        showlegend=False,
        margin=dict(l=0, r=10, t=10, b=80),
        height=450,
    )

    return spec_fig, box_fig


# --- Demand quadrant + pareto + resource index (3 outputs) ---
@callback(
    Output("health-demand-quadrant", "figure"),
    Output("health-pareto", "figure"),
    Output("health-resource-index", "figure"),
    Input("health-filtered-store", "data"),
)
def update_health_analysis(store_data):
    """Generate demand quadrant, Pareto chart, and resource allocation index.

    Args:
        store_data: JSON string from health-filtered-store.

    Returns:
        tuple: (quadrant_fig, pareto_fig, resource_fig) Plotly Figure objects.
    """
    if store_data is None:
        return no_update, no_update, no_update

    data = json.loads(store_data)
    spec_stats = pd.read_json(io.StringIO(data["spec_stats"]), orient="split")
    spec_counts = pd.read_json(io.StringIO(data["spec_counts"]), orient="split")

    # --- Resource Demand Quadrant (uses pre-computed spec_stats) ---
    med_vol = spec_stats["volume"].median()
    med_comp = spec_stats["avg_complexity"].median()

    # Vectorized quadrant assignment (replaces row-wise .apply())
    conditions = [
        (spec_stats["volume"] >= med_vol) & (spec_stats["avg_complexity"] >= med_comp),
        (spec_stats["volume"] >= med_vol),
        (spec_stats["avg_complexity"] >= med_comp),
    ]
    choices = ["High Volume + Complex", "High Volume", "Complex Cases"]
    spec_stats["Quadrant"] = np.select(conditions, choices, default="Low Priority")

    quadrant_colors = {
        "High Volume + Complex": COLORS["danger"],
        "High Volume": COLORS["warning"],
        "Complex Cases": COLORS["info"],
        "Low Priority": COLORS["secondary"],
    }

    quadrant_fig = px.scatter(
        spec_stats,
        x="volume",
        y="avg_complexity",
        color="Quadrant",
        hover_name="medical_specialty",
        size="volume",
        size_max=30,
        template=PLOTLY_TEMPLATE,
        color_discrete_map=quadrant_colors,
        labels={"volume": "Case Volume", "avg_complexity": "Avg Complexity (chars)"},
    )
    quadrant_fig.add_hline(y=med_comp, line_dash="dash", line_color="rgba(255,255,255,0.25)")
    quadrant_fig.add_vline(x=med_vol, line_dash="dash", line_color="rgba(255,255,255,0.25)")
    quadrant_fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
    )

    # --- Workload Pareto (uses pre-computed spec_counts) ---
    pareto_df = spec_counts.sort_values("Count", ascending=False).reset_index(drop=True)
    pareto_df["Cumulative %"] = pareto_df["Count"].cumsum() / pareto_df["Count"].sum() * 100
    # Show top 20 for readability
    pareto_df = pareto_df.head(20)

    pareto_fig = go.Figure()
    pareto_fig.add_trace(
        go.Bar(
            x=pareto_df["Specialty"],
            y=pareto_df["Count"],
            name="Records",
            marker_color=COLORS["secondary"],
            hovertemplate="%{x}<br>Records: %{y}<extra></extra>",
        )
    )
    pareto_fig.add_trace(
        go.Scatter(
            x=pareto_df["Specialty"],
            y=pareto_df["Cumulative %"],
            name="Cumulative %",
            yaxis="y2",
            mode="lines+markers",
            marker=dict(color=COLORS["warning"], size=6),
            line=dict(color=COLORS["warning"], width=2),
            hovertemplate="%{x}<br>Cumulative: %{y:.1f}%<extra></extra>",
        )
    )
    pareto_fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Number of Records"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=40, t=10, b=80),
        height=450,
    )

    # --- Resource Allocation Index ---
    res_df = spec_stats.copy()
    if len(res_df) > 0:
        res_df["norm_vol"] = res_df["volume"] / res_df["volume"].max()
        res_df["norm_comp"] = res_df["avg_complexity"] / res_df["avg_complexity"].max()
        res_df["Resource Score"] = (res_df["norm_vol"] * 0.5 + res_df["norm_comp"] * 0.5) * 100
        res_df = res_df.nlargest(20, "Resource Score").sort_values("Resource Score", ascending=True)

        resource_fig = px.bar(
            res_df,
            x="Resource Score",
            y="medical_specialty",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            color="Resource Score",
            color_continuous_scale="YlOrRd",
            labels={"medical_specialty": "", "Resource Score": "Resource Need Score"},
        )
        resource_fig.update_layout(
            coloraxis_colorbar=dict(title="Score", thickness=12),
            margin=dict(l=0, r=10, t=10, b=0),
            height=450,
        )
    else:
        resource_fig = go.Figure()
        resource_fig.update_layout(margin=dict(l=0, r=10, t=10, b=0), height=450)

    return quadrant_fig, pareto_fig, resource_fig


# --- Keywords + datatable (2 outputs) ---
@callback(
    Output("health-keywords", "figure"),
    Output("health-datatable", "data"),
    Input("health-filtered-store", "data"),
)
def update_health_keywords_table(store_data):
    """Generate top keywords bar chart and populate the data table.

    Args:
        store_data: JSON string from health-filtered-store.

    Returns:
        tuple: (kw_fig, table_data) where table_data is a list of row dicts.
    """
    if store_data is None:
        return no_update, no_update

    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient="split")

    # --- Top 30 Medical Keywords (cleaned) ---
    all_keywords = _extract_keywords(df)
    kw_counts = Counter(all_keywords).most_common(30)
    if kw_counts:
        kw_df = pd.DataFrame(kw_counts, columns=["Keyword", "Count"])
        kw_fig = px.bar(
            kw_df,
            x="Count",
            y="Keyword",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[COLORS["success"]],
        )
        kw_fig.update_layout(
            yaxis=dict(autorange="reversed", title="", categoryorder="total ascending"),
            margin=dict(l=0, r=10, t=10, b=0),
            height=450,
        )
    else:
        kw_fig = go.Figure()
        kw_fig.update_layout(margin=dict(l=0, r=10, t=10, b=0), height=450)

    # DataTable data
    table_data = df[["Serial No", "medical_specialty", "sample_name", "description", "transcription_length"]].to_dict(
        "records"
    )

    return kw_fig, table_data


@callback(
    Output("health-transcription-collapse", "is_open"),
    Output("health-transcription-text", "children"),
    Input("health-datatable", "selected_rows"),
    State("health-datatable", "data"),
)
def show_transcription(selected_rows, data):
    """Show the full transcription text for a selected data table row.

    Args:
        selected_rows: List of selected row indices from the DataTable.
        data: Current DataTable data (list of row dicts).

    Returns:
        tuple: (is_open, transcription_text) for the collapse component.
    """
    if not selected_rows or not data:
        return False, ""

    row = data[selected_rows[0]]
    df = load_healthcare()
    record = df[df["Serial No"] == row["Serial No"]]
    if len(record) == 0:
        return False, ""

    transcription = record.iloc[0].get("transcription", "No transcription available.")
    return True, str(transcription)


# ---------------------------------------------------------------------------
# CSV Export callback
# ---------------------------------------------------------------------------
@callback(
    Output("health-download-csv", "data"),
    Input("health-export-btn", "n_clicks"),
    State("health-filtered-store", "data"),
    prevent_initial_call=True,
)
def export_healthcare_csv(n_clicks, store_data):
    """Export currently filtered healthcare data as a CSV download."""
    if not store_data:
        return no_update
    data = json.loads(store_data)
    df = pd.read_json(io.StringIO(data["df"]), orient="split")
    return dcc.send_data_frame(df.to_csv, "healthcare_records.csv", index=False)
