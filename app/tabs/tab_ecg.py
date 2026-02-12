"""Tab 2: ECG Heartbeat Classification visualization."""

import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State, no_update, Patch
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy.signal import find_peaks

from app.components.chart_container import chart_container
from app.data.loader import load_ecg_precomputed
from app.config import PLOTLY_TEMPLATE, COLORS
from app.logging_config import get_logger

logger = get_logger(__name__)


ECG_COLORS = [COLORS["secondary"], COLORS["danger"], COLORS["success"], COLORS["warning"], COLORS["accent"]]

# Fiducial point marker colors
FIDUCIAL_COLORS = {
    "R": COLORS["danger"],
    "Q": COLORS["info"],
    "S": COLORS["info"],
    "P": COLORS["success"],
    "T": COLORS["warning"],
}

# Trim leading noisy samples from each beat (Waveform Browser only)
TRIM_START = 15
TRIM_END = 5  # also trim trailing edge
NUM_PLAYBACK_WAVES = 20  # beats in playback strip
SYNTH_BEAT_LEN = 200  # points per synthetic beat for playback

# Speed presets (ms per animation tick) -- higher intervals = fewer round-trips
SPEED_PRESETS = {"slow": 150, "normal": 100, "fast": 50}
# Target playback duration per speed (seconds) -- 10s min, 30s max
PLAYBACK_DURATION = {"slow": 25, "normal": 15, "fast": 10}


def _smooth(signal, window=5):
    """Simple moving-average smoothing."""
    kernel = np.ones(window) / window
    return np.convolve(signal, kernel, mode="same")


def _normalize_beat(beat):
    """Min-max normalize a single beat to [0, 1] range."""
    arr = np.array(beat, dtype=float)
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-8:
        return arr
    return (arr - mn) / (mx - mn)


def _prepare_beat(raw_beat):
    """Trim edges, normalize, and lightly smooth a single raw beat."""
    trimmed = raw_beat[TRIM_START:]
    if TRIM_END > 0 and len(trimmed) > TRIM_END:
        trimmed = trimmed[:-TRIM_END]
    normed = _normalize_beat(trimmed)
    # Light 3-point smoothing to reduce high-freq noise
    smoothed = _smooth(normed, window=3)
    return smoothed.tolist()


# ── Synthetic ECG beat generation ──
# Per-class parameter overrides for PQRST Gaussian synthesis
ECG_SYNTH_PARAMS = {
    # MIT-BIH classes
    "Normal (N)": {},
    "Supraventricular (S)": {"P_amp": 0.18, "P_width": 0.03, "T_amp": 0.20, "T_width": 0.05},
    "Ventricular (V)": {
        "Q_amp": -0.15,
        "R_width": 0.025,
        "S_amp": -0.25,
        "T_amp": 0.15,
        "T_center": 0.60,
        "T_width": 0.08,
    },
    "Fusion (F)": {"R_width": 0.022, "S_amp": -0.20, "T_amp": 0.18, "Q_amp": -0.10},
    "Unknown (Q)": {"P_amp": 0.06, "R_amp": 0.65, "T_amp": 0.12, "R_width": 0.020},
    # PTB-DB classes
    "Normal": {},
    "Abnormal": {"Q_amp": -0.12, "S_amp": -0.22, "T_amp": 0.35, "T_center": 0.50, "T_width": 0.055},
}


def _generate_ecg_beat(beat_length=SYNTH_BEAT_LEN, class_name=None):
    """Generate a clean synthetic PQRST complex using sum of Gaussians.

    Each component (P, Q, R, S, T) is a Gaussian with (amplitude, center, width).
    Parameters are adjusted per class to reflect different arrhythmia morphologies.
    """
    params = ECG_SYNTH_PARAMS.get(class_name, {}) if class_name else {}
    t = np.linspace(0, 1, beat_length)

    # Default PQRST: (amplitude, center_fraction, width_fraction)
    defaults = {
        "P": (0.12, 0.20, 0.04),
        "Q": (-0.08, 0.33, 0.012),
        "R": (1.0, 0.36, 0.015),
        "S": (-0.15, 0.39, 0.012),
        "T": (0.25, 0.55, 0.06),
    }

    signal = np.zeros(beat_length)
    for comp, (def_amp, def_center, def_width) in defaults.items():
        amp = params.get(f"{comp}_amp", def_amp)
        center = params.get(f"{comp}_center", def_center)
        width = params.get(f"{comp}_width", def_width)
        signal += amp * np.exp(-((t - center) ** 2) / (2 * width**2))

    return signal.tolist()


def detect_ecg_fiducials(waveform):
    """Detect P, Q, R, S, T fiducial points on a single-heartbeat waveform.

    Expects a normalized [0,1] beat (after trim + normalize + smooth).
    Returns dict with keys R, Q, S, P, T (each {index, amplitude} or None),
    plus PR_interval, QT_interval, ST_segment (each {start, end, length} or None).
    """
    sig = np.array(waveform, dtype=float)
    n = len(sig)
    smoothed = _smooth(sig, window=5)
    sig_range = float(sig.max() - sig.min())

    result = {
        "R": None,
        "Q": None,
        "S": None,
        "P": None,
        "T": None,
        "PR_interval": None,
        "QT_interval": None,
        "ST_segment": None,
    }

    # Skip detection on essentially flat signals
    if sig_range < 0.15:
        return result

    # R-peak: global maximum
    r_idx = int(np.argmax(sig))
    r_amp = float(sig[r_idx])
    result["R"] = {"index": r_idx, "amplitude": r_amp}

    # Q-point: minimum in window before R (must drop notably below R)
    q_start = max(0, r_idx - int(0.18 * n))
    if r_idx > q_start:
        q_region = sig[q_start:r_idx]
        q_idx = q_start + int(np.argmin(q_region))
        if r_amp - float(sig[q_idx]) > 0.1 * sig_range:
            result["Q"] = {"index": q_idx, "amplitude": float(sig[q_idx])}

    # S-point: minimum in window after R (must drop notably below R)
    s_start = r_idx + 1
    s_end = min(n, r_idx + int(0.18 * n))
    if s_end > s_start:
        s_region = sig[s_start:s_end]
        s_idx = s_start + int(np.argmin(s_region))
        if r_amp - float(sig[s_idx]) > 0.1 * sig_range:
            result["S"] = {"index": s_idx, "amplitude": float(sig[s_idx])}

    # P-wave peak: tallest local max in first ~40% before Q
    p_end = result["Q"]["index"] if result["Q"] else r_idx
    p_end = min(p_end, int(0.40 * n))
    if p_end > 5:
        # Use the original signal (not double-smoothed) for P wave detection
        p_region = sig[:p_end]
        peaks, props = find_peaks(p_region, distance=3, prominence=0.01 * sig_range)
        if len(peaks) > 0:
            best = peaks[np.argmax(p_region[peaks])]
            result["P"] = {"index": int(best), "amplitude": float(sig[int(best)])}
        else:
            # Fallback: highest point in the P region if it's above median
            p_idx = int(np.argmax(p_region))
            if p_idx > 1 and float(p_region[p_idx]) > float(np.median(p_region)) + 0.02 * sig_range:
                result["P"] = {"index": p_idx, "amplitude": float(sig[p_idx])}

    # T-wave peak: tallest local max after S in latter portion
    t_start = (result["S"]["index"] + 5) if result["S"] else r_idx + int(0.12 * n)
    t_start = min(t_start, n - 1)
    if n - t_start > 5:
        t_region = smoothed[t_start:]
        peaks, _ = find_peaks(t_region, distance=5, prominence=0.03 * sig_range)
        if len(peaks) > 0:
            best = peaks[np.argmax(t_region[peaks])]
            t_idx = t_start + int(best)
            result["T"] = {"index": t_idx, "amplitude": float(sig[t_idx])}
        else:
            # Fallback: highest point if it stands out
            t_idx = t_start + int(np.argmax(t_region))
            if float(t_region[t_idx - t_start]) > float(np.median(t_region)) + 0.05 * sig_range:
                result["T"] = {"index": t_idx, "amplitude": float(sig[t_idx])}

    # Derived intervals
    if result["P"] and result["R"]:
        result["PR_interval"] = {
            "start": result["P"]["index"],
            "end": result["R"]["index"],
            "length": result["R"]["index"] - result["P"]["index"],
        }
    if result["Q"] and result["T"]:
        result["QT_interval"] = {
            "start": result["Q"]["index"],
            "end": result["T"]["index"],
            "length": result["T"]["index"] - result["Q"]["index"],
        }
    if result["S"] and result["T"]:
        result["ST_segment"] = {
            "start": result["S"]["index"],
            "end": result["T"]["index"],
            "length": result["T"]["index"] - result["S"]["index"],
        }

    return result


def detect_multibeat_fiducials(full_waveform, beat_length):
    """Run fiducial detection on each beat in a concatenated multi-beat strip.

    Returns a list of fiducial dicts with indices offset to the full strip.
    """
    all_fiducials = []
    n_beats = max(1, len(full_waveform) // beat_length)
    for i in range(n_beats):
        start = i * beat_length
        end = min(start + beat_length, len(full_waveform))
        beat = full_waveform[start:end]
        if len(beat) < 10:
            continue
        fid = detect_ecg_fiducials(beat)
        # Offset indices to the full-strip coordinate system
        offset_fid = {}
        for key in ("P", "Q", "R", "S", "T"):
            pt = fid.get(key)
            if pt is not None:
                offset_fid[key] = {"index": pt["index"] + start, "amplitude": pt["amplitude"]}
        all_fiducials.append(offset_fid)
    return all_fiducials


def _build_fiducial_figure(waveform, fiducials):
    """Build annotated fiducial figure with interval shading."""
    sig = np.array(waveform, dtype=float)
    x_full = list(range(len(sig)))

    fig = go.Figure()

    # Shaded interval bands
    band_meta = [
        ("PR_interval", "rgba(39,174,96,0.12)", "PR Interval"),
        ("QT_interval", "rgba(231,76,60,0.08)", "QT Interval"),
        ("ST_segment", "rgba(243,156,18,0.15)", "ST Segment"),
    ]
    for key, fill_color, label in band_meta:
        iv = fiducials.get(key)
        if iv and iv.get("start") is not None:
            s, e = iv["start"], iv["end"]
            y_min = float(np.min(sig[s : e + 1])) if e >= s else 0
            y_max = float(np.max(sig[s : e + 1])) if e >= s else 0
            pad = (y_max - y_min) * 0.15 + 0.02
            fig.add_shape(
                type="rect",
                x0=s,
                x1=e,
                y0=y_min - pad,
                y1=y_max + pad,
                fillcolor=fill_color,
                line=dict(width=0),
                layer="below",
            )
            fig.add_annotation(
                x=(s + e) / 2,
                y=y_max + pad,
                text=label,
                showarrow=False,
                font=dict(size=9, color="#94A3B8"),
                yshift=6,
            )

    # Waveform trace
    fig.add_trace(
        go.Scatter(
            x=x_full,
            y=sig.tolist(),
            mode="lines",
            line=dict(color=COLORS["secondary"], width=1.8),
            name="ECG Signal",
            hovertemplate="Sample: %{x}<br>Amplitude: %{y:.4f}<extra></extra>",
        )
    )

    # Fiducial markers
    marker_meta = [
        ("P", "P wave", "triangle-up", 12, FIDUCIAL_COLORS["P"]),
        ("Q", "Q point", "diamond", 10, FIDUCIAL_COLORS["Q"]),
        ("R", "R peak", "star", 14, FIDUCIAL_COLORS["R"]),
        ("S", "S point", "diamond", 10, FIDUCIAL_COLORS["S"]),
        ("T", "T wave", "triangle-up", 12, FIDUCIAL_COLORS["T"]),
    ]
    for key, label, symbol, size, color in marker_meta:
        pt = fiducials.get(key)
        if pt is not None:
            fig.add_trace(
                go.Scatter(
                    x=[pt["index"]],
                    y=[pt["amplitude"]],
                    mode="markers+text",
                    text=[key],
                    textposition="top center",
                    marker=dict(symbol=symbol, size=size, color=color, line=dict(width=1, color="#fff")),
                    name=label,
                    hovertemplate=f"{label}<br>Sample: %{{x}}<br>Amp: %{{y:.4f}}<extra></extra>",
                    textfont=dict(size=11, color=color),
                )
            )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Sample Point"),
        yaxis=dict(title="Amplitude"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=30, b=0),
        height=280,
    )
    return fig


def _build_fiducial_table(fiducials):
    """Build summary table of detected fiducial points and intervals."""
    rows = []
    for key, label in [("P", "P Wave Peak"), ("Q", "Q Point"), ("R", "R Peak"), ("S", "S Point"), ("T", "T Wave Peak")]:
        pt = fiducials.get(key)
        if pt:
            rows.append(
                html.Tr(
                    [
                        html.Td(label, style={"fontWeight": "600"}),
                        html.Td(f"{pt['index']}"),
                        html.Td(f"{pt['amplitude']:.4f}"),
                    ]
                )
            )
        else:
            rows.append(html.Tr([html.Td(label, style={"fontWeight": "600"}), html.Td("--"), html.Td("--")]))

    for key, label in [("PR_interval", "PR Interval"), ("QT_interval", "QT Interval"), ("ST_segment", "ST Segment")]:
        iv = fiducials.get(key)
        if iv:
            rows.append(
                html.Tr(
                    [
                        html.Td(label, style={"fontWeight": "600"}),
                        html.Td(f"{iv['start']} - {iv['end']}"),
                        html.Td(f"{iv['length']} pts"),
                    ]
                )
            )
        else:
            rows.append(html.Tr([html.Td(label, style={"fontWeight": "600"}), html.Td("--"), html.Td("--")]))

    header = html.Thead(
        html.Tr(
            [
                html.Th("Feature"),
                html.Th("Index / Range"),
                html.Th("Amplitude / Length"),
            ]
        )
    )
    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
        className="mt-2",
        style={"fontSize": "0.85rem"},
    )


def layout():
    return html.Div(
        [
            # Dataset selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Dataset", className="filter-label"),
                            dbc.RadioItems(
                                id="ecg-dataset-select",
                                options=[
                                    {"label": "MIT-BIH Arrhythmia (5-class)", "value": "mitbih"},
                                    {"label": "PTB Diagnostic (2-class)", "value": "ptbdb"},
                                ],
                                value="mitbih",
                                inline=True,
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Distribution Scale", className="filter-label"),
                            dbc.RadioItems(
                                id="ecg-scale-toggle",
                                options=[
                                    {"label": "Linear", "value": "linear"},
                                    {"label": "Log", "value": "log"},
                                ],
                                value="linear",
                                inline=True,
                            ),
                        ],
                        md=3,
                    ),
                ],
                className="filter-panel",
            ),
            # ── ECG Playback & Fiducial Detection (top of page) ──
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            [
                                                html.Span("ECG Playback Monitor"),
                                                html.I(
                                                    className="bi bi-info-circle ms-2 chart-info-icon",
                                                    id="ecg-playback-info-icon",
                                                ),
                                            ],
                                            className="chart-title",
                                            style={"display": "flex", "alignItems": "center"},
                                        ),
                                        dbc.Tooltip(
                                            "Animated ECG strip chart with real-time PQRST fiducial"
                                            " detection. Synthetic waveforms are generated based on"
                                            " the selected heartbeat class. Use Play/Pause and"
                                            " Speed controls.",
                                            target="ecg-playback-info-icon",
                                            placement="right",
                                        ),
                                        # Controls row
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.ButtonGroup(
                                                            [
                                                                dbc.Button(
                                                                    "Play",
                                                                    id="ecg-play-btn",
                                                                    size="sm",
                                                                    color="success",
                                                                ),
                                                                dbc.Button(
                                                                    "Reset",
                                                                    id="ecg-reset-btn",
                                                                    size="sm",
                                                                    outline=True,
                                                                    color="secondary",
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                    md=3,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Label(
                                                            "Speed",
                                                            className="filter-label me-2",
                                                            style={"display": "inline-block"},
                                                        ),
                                                        dbc.RadioItems(
                                                            id="ecg-speed-select",
                                                            options=[
                                                                {"label": "Slow", "value": "slow"},
                                                                {"label": "Normal", "value": "normal"},
                                                                {"label": "Fast", "value": "fast"},
                                                            ],
                                                            value="normal",
                                                            inline=True,
                                                        ),
                                                    ],
                                                    md=5,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Badge(
                                                            "Stopped",
                                                            id="ecg-playback-status",
                                                            color="secondary",
                                                            className="fs-6 p-2",
                                                        ),
                                                    ],
                                                    md=2,
                                                    className="text-end",
                                                ),
                                            ],
                                            className="mb-3 align-items-center",
                                        ),
                                        # Playback graph — taller to match fiducial panel
                                        dcc.Graph(id="ecg-playback-graph", style={"height": "550px"}),
                                    ]
                                ),
                                className="chart-card",
                            ),
                        ],
                        md=8,
                    ),
                    # Fiducial detection panel
                    dbc.Col(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            [
                                                html.Span("Fiducial Points"),
                                                html.I(
                                                    className="bi bi-info-circle ms-2 chart-info-icon",
                                                    id="ecg-fiducial-info-icon",
                                                ),
                                            ],
                                            className="chart-title",
                                            style={"display": "flex", "alignItems": "center"},
                                        ),
                                        dbc.Tooltip(
                                            "Annotated single-beat waveform showing detected"
                                            " P, Q, R, S, T points and derived intervals"
                                            " (PR, QT, ST). Shaded bands highlight interval"
                                            " regions.",
                                            target="ecg-fiducial-info-icon",
                                            placement="right",
                                        ),
                                        dcc.Graph(id="ecg-fiducial-graph", style={"height": "280px"}),
                                        html.Div(id="ecg-fiducial-table"),
                                    ]
                                ),
                                className="chart-card",
                            ),
                        ],
                        md=4,
                    ),
                ]
            ),
            # Class distribution
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "ecg-class-dist",
                            "Class Distribution (Train vs Test)",
                            info=(
                                "Grouped bar chart comparing heartbeat class distribution"
                                " between training and test datasets. Use the scale toggle"
                                " to switch between linear and log."
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "ecg-waveform-overlay",
                            "Mean Waveform by Class (+/- 1 Std Dev)",
                            info=(
                                "Mean waveform overlay for each heartbeat class with shaded"
                                " bands showing +/- 1 standard deviation of signal variability"
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # Waveform browser
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            [
                                                html.Span("Waveform Browser"),
                                                html.I(
                                                    className="bi bi-info-circle ms-2 chart-info-icon",
                                                    id="ecg-browser-info-icon",
                                                ),
                                            ],
                                            className="chart-title",
                                            style={"display": "flex", "alignItems": "center"},
                                        ),
                                        dbc.Tooltip(
                                            "Browse individual ECG samples one at a time."
                                            " Select a class from the dropdown and navigate"
                                            " with Prev/Next buttons.",
                                            target="ecg-browser-info-icon",
                                            placement="right",
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Label("Class", className="filter-label"),
                                                        dcc.Dropdown(id="ecg-browse-class", placeholder="Select class"),
                                                    ],
                                                    md=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Label("Sample", className="filter-label"),
                                                        dbc.ButtonGroup(
                                                            [
                                                                dbc.Button(
                                                                    "< Prev",
                                                                    id="ecg-prev-btn",
                                                                    size="sm",
                                                                    outline=True,
                                                                    color="primary",
                                                                ),
                                                                html.Span(
                                                                    id="ecg-sample-idx",
                                                                    className="mx-3 align-self-center",
                                                                    style={"fontWeight": "600"},
                                                                ),
                                                                dbc.Button(
                                                                    "Next >",
                                                                    id="ecg-next-btn",
                                                                    size="sm",
                                                                    outline=True,
                                                                    color="primary",
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                    md=4,
                                                ),
                                            ],
                                            className="mb-2",
                                        ),
                                        dcc.Loading(
                                            dcc.Graph(id="ecg-waveform-browser", style={"height": "350px"}),
                                            type="circle",
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
            # Features + Heatmap
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "ecg-features",
                            "Signal Feature Comparison",
                            info=(
                                "Grouped bar chart comparing extracted signal features"
                                " (peak amplitude, energy, zero crossings) across"
                                " heartbeat classes"
                            ),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        chart_container(
                            "ecg-correlation",
                            "Class Similarity Heatmap",
                            info=(
                                "Correlation matrix showing pairwise similarity between"
                                " heartbeat classes based on mean waveform shape."
                                " Values range from -1 to 1."
                            ),
                        ),
                        md=6,
                    ),
                ]
            ),
            # PCA Embedding
            dbc.Row(
                [
                    dbc.Col(
                        chart_container(
                            "ecg-pca-scatter",
                            "PCA Class Embedding",
                            info=(
                                "2D PCA projection of sampled ECG waveforms, colored by"
                                " class label. Shows class separability in reduced feature"
                                " space. Explained variance shown in axis labels."
                            ),
                        ),
                        md=12,
                    ),
                ]
            ),
            # Hidden stores
            dcc.Store(id="ecg-sample-store", data=0),
            dcc.Store(id="ecg-playback-waveform", data=[]),
            dcc.Store(id="ecg-playback-frame", data=0),
            dcc.Store(id="ecg-playback-playing", data=False),
            dcc.Store(id="ecg-fiducial-positions", data={}),
            dcc.Interval(id="ecg-playback-interval", interval=60, disabled=True),
        ],
        className="tab-content-wrapper",
    )


# ══════════════════════════════════════════════════════════════════════
# EXISTING CALLBACKS (unchanged)
# ══════════════════════════════════════════════════════════════════════


@callback(
    Output("ecg-browse-class", "options"),
    Output("ecg-browse-class", "value"),
    Input("ecg-dataset-select", "value"),
)
def update_class_options(dataset):
    data = load_ecg_precomputed()
    ds = data[dataset]
    class_names = list(ds["class_names"].values())
    return [{"label": c, "value": c} for c in class_names], class_names[0]


@callback(
    Output("ecg-class-dist", "figure"),
    Input("ecg-dataset-select", "value"),
    Input("ecg-scale-toggle", "value"),
)
def update_class_distribution(dataset, scale):
    logger.info("ECG distribution callback: dataset=%s, scale=%s", dataset, scale)
    data = load_ecg_precomputed()
    ds = data[dataset]

    fig = go.Figure()
    for split_name in ["train", "test"]:
        if split_name in ds["splits"]:
            dist = ds["splits"][split_name]["class_distribution"]
            fig.add_trace(
                go.Bar(
                    y=list(dist.keys()),
                    x=list(dist.values()),
                    name=split_name.capitalize(),
                    orientation="h",
                )
            )

    fig.update_layout(
        barmode="group",
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Count", type="log" if scale == "log" else "linear"),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=400,
    )
    return fig


@callback(
    Output("ecg-waveform-overlay", "figure"),
    Input("ecg-dataset-select", "value"),
)
def update_waveform_overlay(dataset):
    data = load_ecg_precomputed()
    ds = data[dataset]

    # Handle empty splits dictionary
    if not ds["splits"]:
        return go.Figure()

    split = ds["splits"].get("train", list(ds["splits"].values())[0])

    fig = go.Figure()
    x_axis = list(range(len(list(split["mean_waveforms"].values())[0])))

    for i, class_name in enumerate(split["mean_waveforms"]):
        mean = np.array(split["mean_waveforms"][class_name])
        std = np.array(split["std_waveforms"][class_name])
        color = ECG_COLORS[i % len(ECG_COLORS)]

        # Std band
        fig.add_trace(
            go.Scatter(
                x=x_axis + x_axis[::-1],
                y=(mean + std).tolist() + (mean - std).tolist()[::-1],
                fill="toself",
                fillcolor=(
                    color.replace(")", ",0.1)").replace("rgb", "rgba")
                    if "rgb" in color
                    else f"rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},0.1)"
                ),
                line=dict(width=0),
                name=f"{class_name} +/-1 std",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Mean line
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=mean.tolist(),
                name=class_name,
                line=dict(color=color, width=2),
            )
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Sample Point"),
        yaxis=dict(title="Amplitude"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=400,
    )
    return fig


@callback(
    Output("ecg-sample-store", "data"),
    Input("ecg-prev-btn", "n_clicks"),
    Input("ecg-next-btn", "n_clicks"),
    Input("ecg-browse-class", "value"),
    State("ecg-sample-store", "data"),
    State("ecg-dataset-select", "value"),
)
def update_sample_index(prev_clicks, next_clicks, class_name, current_idx, dataset):
    from dash import ctx

    if not class_name:
        return 0

    data = load_ecg_precomputed()
    ds = data[dataset]

    # Handle empty splits dictionary
    if not ds["splits"]:
        return 0

    split = ds["splits"].get("train", list(ds["splits"].values())[0])
    n_samples = len(split["samples"].get(class_name, []))

    if n_samples == 0:
        return 0

    triggered = ctx.triggered_id
    if triggered == "ecg-next-btn":
        return min(current_idx + 1, n_samples - 1)
    elif triggered == "ecg-prev-btn":
        return max(current_idx - 1, 0)
    else:
        return 0


@callback(
    Output("ecg-waveform-browser", "figure"),
    Output("ecg-sample-idx", "children"),
    Input("ecg-sample-store", "data"),
    Input("ecg-browse-class", "value"),
    Input("ecg-dataset-select", "value"),
)
def update_waveform_browser(sample_idx, class_name, dataset):
    if not class_name:
        return go.Figure(), "0 / 0"

    data = load_ecg_precomputed()
    ds = data[dataset]

    # Handle empty splits dictionary
    if not ds["splits"]:
        return go.Figure(), "0 / 0"

    split = ds["splits"].get("train", list(ds["splits"].values())[0])
    samples = split["samples"].get(class_name, [])

    if not samples:
        return go.Figure(), "0 / 0"

    waveform = _prepare_beat(samples[sample_idx])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=waveform,
            mode="lines",
            line=dict(color=COLORS["secondary"], width=1.5),
            name=class_name,
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis=dict(title="Sample Point"),
        yaxis=dict(title="Amplitude"),
        margin=dict(l=0, r=10, t=10, b=0),
        height=350,
    )
    return fig, f"{sample_idx + 1} / {len(samples)}"


@callback(
    Output("ecg-features", "figure"),
    Input("ecg-dataset-select", "value"),
)
def update_features(dataset):
    data = load_ecg_precomputed()
    ds = data[dataset]

    # Handle empty splits dictionary
    if not ds["splits"]:
        return go.Figure()

    split = ds["splits"].get("train", list(ds["splits"].values())[0])
    features = split["features"]

    feature_names = ["peak_amplitude", "energy", "zero_crossings"]
    display_names = {"peak_amplitude": "Peak Amplitude", "energy": "Energy", "zero_crossings": "Zero Crossings"}

    fig = go.Figure()
    for class_name in features:
        vals = [features[class_name][f] for f in feature_names]
        fig.add_trace(
            go.Bar(
                x=[display_names[f] for f in feature_names],
                y=vals,
                name=class_name,
            )
        )

    fig.update_layout(
        barmode="group",
        template=PLOTLY_TEMPLATE,
        yaxis=dict(title="Value"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=10, t=10, b=0),
        height=400,
    )
    return fig


@callback(
    Output("ecg-correlation", "figure"),
    Input("ecg-dataset-select", "value"),
)
def update_correlation(dataset):
    data = load_ecg_precomputed()
    ds = data[dataset]

    if "correlation_matrix" not in ds:
        return go.Figure()

    corr = ds["correlation_matrix"]
    fig = go.Figure(
        go.Heatmap(
            z=corr["matrix"],
            x=corr["classes"],
            y=corr["classes"],
            colorscale="RdBu",
            zmin=-1,
            zmax=1,
            text=[[f"{v:.3f}" for v in row] for row in corr["matrix"]],
            texttemplate="%{text}",
            textfont={"size": 11},
        )
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        margin=dict(l=0, r=10, t=10, b=0),
        height=400,
        xaxis=dict(side="bottom"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════
# NEW: ECG Playback & Fiducial Detection Callbacks
# ══════════════════════════════════════════════════════════════════════


@callback(
    Output("ecg-playback-waveform", "data"),
    Input("ecg-browse-class", "value"),
    Input("ecg-dataset-select", "value"),
)
def sync_playback_waveform(class_name, dataset):
    """Build a clean multi-beat strip using synthetic PQRST for the class."""
    if not class_name:
        return []
    beat = _generate_ecg_beat(SYNTH_BEAT_LEN, class_name)
    return beat * NUM_PLAYBACK_WAVES


@callback(
    Output("ecg-fiducial-graph", "figure"),
    Output("ecg-fiducial-table", "children"),
    Input("ecg-playback-waveform", "data"),
)
def update_fiducial_panel(waveform):
    """Detect fiducial points on the first beat and render annotated chart + table."""
    if not waveform or len(waveform) < 10:
        empty = go.Figure()
        empty.update_layout(
            template=PLOTLY_TEMPLATE,
            height=280,
            margin=dict(l=0, r=10, t=10, b=0),
            annotations=[
                dict(
                    text="No waveform selected",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=14, color="#999"),
                )
            ],
        )
        return empty, html.P("Select a waveform from the browser above.", className="text-muted")

    first_beat = waveform[:SYNTH_BEAT_LEN] if len(waveform) > SYNTH_BEAT_LEN else waveform
    fiducials = detect_ecg_fiducials(first_beat)
    fig = _build_fiducial_figure(first_beat, fiducials)
    table = _build_fiducial_table(fiducials)
    return fig, table


# ── Pre-compute fiducial positions for all beats ──

MARKER_CONFIG = [
    ("P", "P wave", "triangle-up", 10, FIDUCIAL_COLORS["P"]),
    ("Q", "Q point", "diamond", 8, FIDUCIAL_COLORS["Q"]),
    ("R", "R peak", "star", 12, FIDUCIAL_COLORS["R"]),
    ("S", "S point", "diamond", 8, FIDUCIAL_COLORS["S"]),
    ("T", "T wave", "triangle-up", 10, FIDUCIAL_COLORS["T"]),
]


@callback(
    Output("ecg-fiducial-positions", "data"),
    Input("ecg-playback-waveform", "data"),
)
def compute_fiducial_positions(waveform):
    """Detect fiducials across all beats and store grouped by marker type."""
    if not waveform or len(waveform) < 10:
        return {}
    all_fids = detect_multibeat_fiducials(waveform, SYNTH_BEAT_LEN)
    positions = {}
    for key in ("P", "Q", "R", "S", "T"):
        xs, ys = [], []
        for fid in all_fids:
            pt = fid.get(key)
            if pt:
                xs.append(pt["index"])
                ys.append(pt["amplitude"])
        positions[key] = {"x": xs, "y": ys}
    return positions


# ── Empty playback figure with placeholder marker traces ──


@callback(
    Output("ecg-playback-graph", "figure"),
    Input("ecg-playback-waveform", "data"),
)
def build_playback_figure(waveform):
    """Create an EMPTY figure with correct axes. No data shown until Play.

    Trace layout:
      [0] ECG line (empty, filled via extendData)
      [1] P markers (empty, filled via Patch in scroll_playback)
      [2] Q markers
      [3] R markers
      [4] S markers
      [5] T markers
    """
    fig = go.Figure()
    # Trace 0: ECG line
    fig.add_trace(
        go.Scatter(
            x=[],
            y=[],
            mode="lines",
            line=dict(color=COLORS["danger"], width=2),
            name="ECG Trace",
        )
    )

    # Traces 1-5: one per fiducial type (empty initially)
    for key, name, symbol, size, color in MARKER_CONFIG:
        fig.add_trace(
            go.Scatter(
                x=[],
                y=[],
                mode="markers+text",
                text=[],
                textposition="top center",
                marker=dict(symbol=symbol, size=size, color=color, line=dict(width=1, color="#fff")),
                textfont=dict(size=9, color=color),
                name=name,
                showlegend=(key != "P"),
                hovertemplate=f"{key}<br>Sample: %{{x}}<br>Amp: %{{y:.4f}}<extra></extra>",
            )
        )

    if waveform and len(waveform) > 1:
        sig = np.array(waveform, dtype=float)
        window = 3 * SYNTH_BEAT_LEN
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            height=550,
            xaxis=dict(title="Sample Point", range=[0, window], autorange=False),
            yaxis=dict(
                title="Amplitude (mV)", range=[float(sig.min()) - 0.1, float(sig.max()) + 0.15], autorange=False
            ),
            margin=dict(l=0, r=10, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
        )
    else:
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            height=550,
            margin=dict(l=0, r=10, t=10, b=0),
            annotations=[
                dict(
                    text="Select a class and press Play",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=14, color="#999"),
                )
            ],
        )
    return fig


# ── Play / Pause toggle ──


@callback(
    Output("ecg-playback-playing", "data"),
    Output("ecg-playback-frame", "data", allow_duplicate=True),
    Output("ecg-play-btn", "children"),
    Output("ecg-play-btn", "color"),
    Output("ecg-playback-status", "children"),
    Output("ecg-playback-status", "color"),
    Input("ecg-play-btn", "n_clicks"),
    State("ecg-playback-playing", "data"),
    State("ecg-playback-frame", "data"),
    State("ecg-playback-waveform", "data"),
    prevent_initial_call=True,
)
def toggle_play_pause(n_clicks, is_playing, current_frame, waveform):
    if not waveform:
        return False, 0, "Play", "success", "No data", "secondary"
    total = len(waveform)
    if is_playing:
        return False, current_frame, "Play", "success", "Paused", "warning"
    else:
        new_frame = current_frame if current_frame < total else 0
        return True, new_frame, "Pause", "danger", "Playing", "success"


# ── Reset: clear the drawn trace ──


@callback(
    Output("ecg-playback-playing", "data", allow_duplicate=True),
    Output("ecg-playback-frame", "data", allow_duplicate=True),
    Output("ecg-play-btn", "children", allow_duplicate=True),
    Output("ecg-play-btn", "color", allow_duplicate=True),
    Output("ecg-playback-status", "children", allow_duplicate=True),
    Output("ecg-playback-status", "color", allow_duplicate=True),
    Output("ecg-playback-graph", "figure", allow_duplicate=True),
    Input("ecg-reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_playback(_n):
    window = 3 * SYNTH_BEAT_LEN
    patched = Patch()
    # Clear ECG trace and all marker traces
    for i in range(6):  # traces 0-5
        patched["data"][i]["x"] = []
        patched["data"][i]["y"] = []
        if i > 0:
            patched["data"][i]["text"] = []
    patched["layout"]["xaxis"]["range"] = [0, window]
    return False, 0, "Play", "success", "Stopped", "secondary", patched


# ── Reset when waveform changes (build_playback_figure handles the graph) ──


@callback(
    Output("ecg-playback-playing", "data", allow_duplicate=True),
    Output("ecg-playback-frame", "data", allow_duplicate=True),
    Output("ecg-play-btn", "children", allow_duplicate=True),
    Output("ecg-play-btn", "color", allow_duplicate=True),
    Output("ecg-playback-status", "children", allow_duplicate=True),
    Output("ecg-playback-status", "color", allow_duplicate=True),
    Input("ecg-playback-waveform", "data"),
    prevent_initial_call=True,
)
def reset_on_waveform_change(_waveform):
    return False, 0, "Play", "success", "Stopped", "secondary"


# ── Control interval timer ──


@callback(
    Output("ecg-playback-interval", "disabled"),
    Output("ecg-playback-interval", "interval"),
    Input("ecg-playback-playing", "data"),
    Input("ecg-speed-select", "value"),
)
def control_interval_timer(is_playing, speed):
    ms = SPEED_PRESETS.get(speed, SPEED_PRESETS["normal"])
    return (not is_playing), ms


# ── Animation tick: append points via extendData + scroll via Patch ──


@callback(
    Output("ecg-playback-graph", "extendData"),
    Output("ecg-playback-frame", "data"),
    Output("ecg-playback-playing", "data", allow_duplicate=True),
    Output("ecg-play-btn", "children", allow_duplicate=True),
    Output("ecg-play-btn", "color", allow_duplicate=True),
    Output("ecg-playback-status", "children", allow_duplicate=True),
    Output("ecg-playback-status", "color", allow_duplicate=True),
    Input("ecg-playback-interval", "n_intervals"),
    State("ecg-playback-frame", "data"),
    State("ecg-playback-playing", "data"),
    State("ecg-playback-waveform", "data"),
    State("ecg-speed-select", "value"),
    prevent_initial_call=True,
)
def animate_tick(_n, current_frame, is_playing, waveform, speed):
    """Append the next chunk of points via extendData (tiny payload per tick)."""
    if not is_playing or not waveform:
        return (no_update,) * 7

    total = len(waveform)
    target_s = PLAYBACK_DURATION.get(speed, 15)
    interval_ms = SPEED_PRESETS.get(speed, 100)
    n_ticks = max(1, target_s * 1000 / interval_ms)
    step = max(1, round(total / n_ticks))

    new_frame = min(current_frame + step, total)
    new_x = list(range(current_frame, new_frame))
    new_y = waveform[current_frame:new_frame]

    extend = ({"x": [new_x], "y": [new_y]}, [0])

    if new_frame >= total:
        return extend, total, False, "Play", "success", "Complete", "info"
    return extend, new_frame, no_update, no_update, no_update, no_update, no_update


# ── Scroll the x-axis window as the trace grows ──


@callback(
    Output("ecg-playback-graph", "figure", allow_duplicate=True),
    Input("ecg-playback-frame", "data"),
    State("ecg-playback-waveform", "data"),
    State("ecg-fiducial-positions", "data"),
    prevent_initial_call=True,
)
def scroll_playback(frame, waveform, fid_positions):
    """Scroll x-axis + populate fiducial markers up to current frame."""
    if not waveform or frame <= 0:
        return no_update
    window = 3 * SYNTH_BEAT_LEN
    patched = Patch()

    # Scroll the viewport
    x_end = max(window, frame)
    x_start = max(0, x_end - window)
    patched["layout"]["xaxis"]["range"] = [x_start, x_start + window]

    # Update marker traces (1-5) with fiducials up to current frame
    if fid_positions:
        for i, (key, _, _, _, _) in enumerate(MARKER_CONFIG):
            pos = fid_positions.get(key, {})
            all_x = pos.get("x", [])
            all_y = pos.get("y", [])
            vis_x = [x for x in all_x if x < frame]
            vis_y = [all_y[j] for j, x in enumerate(all_x) if x < frame]
            patched["data"][i + 1]["x"] = vis_x
            patched["data"][i + 1]["y"] = vis_y
            patched["data"][i + 1]["text"] = [key] * len(vis_x)

    return patched


# ══════════════════════════════════════════════════════════════════════
# NEW: PCA Embedding Scatter
# ══════════════════════════════════════════════════════════════════════


@callback(
    Output("ecg-pca-scatter", "figure"),
    Input("ecg-dataset-select", "value"),
)
def update_pca_scatter(dataset):
    data = load_ecg_precomputed()
    ds = data[dataset]

    if "pca_embedding" not in ds:
        fig = go.Figure()
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            height=450,
            annotations=[
                dict(
                    text="PCA data not available — regenerate cache",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=14, color="#999"),
                )
            ],
        )
        return fig

    pca = ds["pca_embedding"]
    import pandas as pd

    pca_df = pd.DataFrame(
        {
            "PC1": pca["x"],
            "PC2": pca["y"],
            "Class": pca["labels"],
        }
    )
    ev = pca.get("explained_variance", [0, 0])
    ev1 = ev[0] * 100 if len(ev) > 0 else 0
    ev2 = ev[1] * 100 if len(ev) > 1 else 0

    fig = px.scatter(
        pca_df,
        x="PC1",
        y="PC2",
        color="Class",
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=ECG_COLORS,
        labels={"PC1": f"PC1 ({ev1:.1f}% var)", "PC2": f"PC2 ({ev2:.1f}% var)"},
    )
    fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig
