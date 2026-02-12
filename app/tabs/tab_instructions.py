"""Instructions tab — static layout with dashboard guidance."""

from dash import html
import dash_bootstrap_components as dbc


def layout():
    """Return the Instructions tab layout."""
    return html.Div(
        [
            # A. Welcome Card
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H3(
                                [
                                    html.I(className="bi bi-compass me-2 instructions-icon"),
                                    "Welcome to the Command Center",
                                ]
                            ),
                            html.P(
                                "This dashboard unifies four distinct datasets into a single "
                                "analytical platform. Explore U.S. military equipment transfers, "
                                "installation locations, biomedical ECG heartbeat signals, and "
                                "healthcare transcription records — each on its own tab, plus a "
                                "combined intelligence view that joins military data for deeper insight.",
                                className="instructions-section",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
            # B. Tab-by-Tab Guide
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(
                                [
                                    html.I(className="bi bi-layout-text-sidebar-reverse me-2 instructions-icon"),
                                    "Tab-by-Tab Guide",
                                ]
                            ),
                            dbc.Accordion(
                                [
                                    # Equipment Transfers
                                    dbc.AccordionItem(
                                        [
                                            html.P(
                                                "Visualizes the Department of Defense 1033 Program, which "
                                                "transfers excess military equipment to law enforcement agencies. "
                                                "The dataset contains over 130,000 rows covering all U.S. states "
                                                "and territories.",
                                                className="instructions-section",
                                            ),
                                            html.P("Available controls and charts:", className="fw-bold mb-1"),
                                            html.Ul(
                                                [
                                                    html.Li("Filters: state, year range, and equipment category"),
                                                    html.Li("KPI cards showing totals and averages"),
                                                    html.Li("Choropleth map of transfer values by state"),
                                                    html.Li("Bar charts for top states and categories"),
                                                    html.Li("Timeline of transfers over the years"),
                                                    html.Li("Treemap for hierarchical category breakdown"),
                                                ]
                                            ),
                                        ],
                                        title="Equipment Transfers",
                                    ),
                                    # Installations Map
                                    dbc.AccordionItem(
                                        [
                                            html.P(
                                                "Maps U.S. military base and installation locations. "
                                                "Filter by branch of service, operational status, state, "
                                                "and joint-base designation.",
                                                className="instructions-section",
                                            ),
                                            html.P("Available controls and charts:", className="fw-bold mb-1"),
                                            html.Ul(
                                                [
                                                    html.Li("Scatter-geo map of base locations"),
                                                    html.Li("Stacked bar chart of bases by branch and status"),
                                                    html.Li("Sunburst chart for branch / state hierarchy"),
                                                    html.Li("Small-multiple maps by service branch"),
                                                ]
                                            ),
                                        ],
                                        title="Installations Map",
                                    ),
                                    # ECG Analysis
                                    dbc.AccordionItem(
                                        [
                                            html.P(
                                                "Analyzes the MIT-BIH and PTB heartbeat datasets. "
                                                "Each record is a 187-point ECG signal segment with a "
                                                "diagnostic label.",
                                                className="instructions-section",
                                            ),
                                            html.P("Available controls and charts:", className="fw-bold mb-1"),
                                            html.Ul(
                                                [
                                                    html.Li("Playback monitor with animated ECG trace"),
                                                    html.Li("PQRST peak detection and fiducial annotations"),
                                                    html.Li("Class distribution bar chart"),
                                                    html.Li("Waveform browser to compare individual samples"),
                                                    html.Li("Feature comparison across diagnostic classes"),
                                                    html.Li("Similarity heatmap between classes"),
                                                ]
                                            ),
                                        ],
                                        title="ECG Analysis",
                                    ),
                                    # Medical Records
                                    dbc.AccordionItem(
                                        [
                                            html.P(
                                                "Explores 3,800+ healthcare transcription records "
                                                "spanning 39 medical specialties. Supports specialty "
                                                "filtering and keyword search across transcription text.",
                                                className="instructions-section",
                                            ),
                                            html.P("Available controls and charts:", className="fw-bold mb-1"),
                                            html.Ul(
                                                [
                                                    html.Li("Bar chart of record counts by specialty"),
                                                    html.Li("Word cloud of most frequent terms"),
                                                    html.Li("Box plot of transcription length by specialty"),
                                                    html.Li("Keyword frequency chart"),
                                                    html.Li(
                                                        "Searchable data table with row"
                                                        " expansion for full transcription"
                                                    ),
                                                ]
                                            ),
                                        ],
                                        title="Medical Records",
                                    ),
                                    # Combined Intel
                                    dbc.AccordionItem(
                                        [
                                            html.P(
                                                "Cross-dataset analysis that joins equipment transfer data "
                                                "with military base locations for combined intelligence insights.",
                                                className="instructions-section",
                                            ),
                                            html.P("Available controls and charts:", className="fw-bold mb-1"),
                                            html.Ul(
                                                [
                                                    html.Li("Dual-layer map overlaying bases and equipment data"),
                                                    html.Li("Scatter correlation between bases and transfer values"),
                                                    html.Li("Butterfly chart comparing metrics side by side"),
                                                    html.Li("Branch-category heatmap"),
                                                    html.Li("Composite state ranking table"),
                                                ]
                                            ),
                                        ],
                                        title="Combined Intel",
                                    ),
                                ],
                                start_collapsed=True,
                                className="mt-2",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
            # C. How to Use Card
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(
                                [
                                    html.I(className="bi bi-hand-index-thumb me-2 instructions-icon"),
                                    "How to Use",
                                ]
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        "Use dropdowns and sliders to filter data —"
                                        " all charts in the active tab update together."
                                    ),
                                    html.Li("Hover over any chart element to see detailed values in a tooltip."),
                                    html.Li(
                                        [
                                            "Look for the ",
                                            html.I(className="bi bi-info-circle"),
                                            " icon next to chart titles for a description of what the chart shows.",
                                        ]
                                    ),
                                    html.Li(
                                        "Click segments in sunburst and treemap charts"
                                        " to drill down into subcategories."
                                    ),
                                    html.Li(
                                        "ECG playback: use Play / Pause / Reset buttons"
                                        " and the speed slider to control animation."
                                    ),
                                    html.Li(
                                        "Data tables support sorting and filtering."
                                        " Click a row to expand and view full"
                                        " transcription text."
                                    ),
                                ],
                                className="instructions-section",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
            # D. Data Sources Card
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(
                                [
                                    html.I(className="bi bi-database me-2 instructions-icon"),
                                    "Data Sources",
                                ]
                            ),
                            html.Ul(
                                [
                                    html.Li("DoD 1033 Program Equipment Transfers — 130,958 rows"),
                                    html.Li("U.S. Military Installations — semicolon-delimited base records"),
                                    html.Li("MIT-BIH & PTB ECG Heartbeat — 187-point signal segments"),
                                    html.Li("Medical Transcriptions — 3,813 records across 39 specialties"),
                                ],
                                className="instructions-section",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
        ],
        className="tab-content-wrapper",
    )
