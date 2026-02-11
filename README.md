# Multi-Domain Analytics Dashboard

> **This is a demo application built purely for fun to demonstrate the ability to use Large Language Models (LLMs) to design, develop, and deploy a fully functional data visualization dashboard from scratch.** Every line of code, every visualization, and every design decision in this project was guided through LLM-assisted development — showcasing how AI can accelerate the creation of sophisticated, production-ready web applications.

---

## Table of Contents

- [Overview](#overview)
- [Live Preview](#live-preview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Datasets](#datasets)
- [Dashboard Tabs](#dashboard-tabs)
  - [Instructions](#1-instructions)
  - [Equipment Transfers](#2-equipment-transfers)
  - [Military Bases Map](#3-military-bases-map)
  - [ECG Analysis](#4-ecg-analysis)
  - [Healthcare Records](#5-healthcare-records)
  - [Combined Intelligence](#6-combined-intelligence)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
  - [Production Deployment](#production-deployment)
- [Performance Optimizations](#performance-optimizations)
- [Configuration](#configuration)
- [Data Processing Pipeline](#data-processing-pipeline)
- [License](#license)

---

## Overview

This project is a **multi-domain analytics dashboard** that brings together four completely different datasets — military equipment transfers, military base installations, ECG heartbeat signals, and healthcare medical transcriptions — into a single, cohesive, interactive web application. The dashboard features over **50 unique visualizations** across 6 tabs, including animated charts, geospatial maps, biomedical signal processing, and natural language analysis.

The entire application was designed and built using **LLM-assisted development** as a proof of concept, demonstrating that modern AI tools can produce clean, modular, well-architected code suitable for real-world deployment.

---

## Live Preview

After starting the application, navigate to:

```
http://localhost:8050
```

---

## Features

- **50+ Interactive Visualizations** — Choropleth maps, treemaps, sunbursts, radar charts, scatter plots, box plots, bar charts, word clouds, and more
- **Animated Playback** — ECG heartbeat monitor with real-time PQRST peak detection and equipment timeline animation with play/pause controls
- **Cross-Dataset Analysis** — A dedicated tab that joins military equipment and base data for strategic intelligence insights
- **Geospatial Mapping** — Interactive Mapbox-powered maps with branch-colored markers, density choropleths, and dual-layer overlays
- **Biomedical Signal Processing** — Full ECG waveform analysis with fiducial point detection (P, Q, R, S, T waves), interval computation, and PCA embeddings
- **Healthcare NLP** — Medical transcription analysis with keyword extraction, word clouds, specialty distribution, and resource demand scoring
- **Modern Dark Theme** — Polished UI with a custom dark color palette, Bootstrap components, loading spinners, and tooltip hints
- **Responsive Filtering** — Dynamic dropdowns, sliders, radio buttons, and search inputs that reactively update all connected charts
- **Production-Ready** — Gunicorn-compatible WSGI server, in-memory caching, and precomputed data pipelines

---

## Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| **Web Framework** | Dash | 2.17.1 |
| **Charting** | Plotly | 5.22.0 |
| **UI Components** | Dash Bootstrap Components | 1.6.0 |
| **Data Processing** | Pandas | 2.2.2 |
| **Numerical Computing** | NumPy | 1.26.4 |
| **Statistical Modeling** | StatsModels | 0.14.6 |
| **Signal Processing** | SciPy | (via StatsModels) |
| **Machine Learning** | Scikit-learn | (PCA embeddings) |
| **Text Visualization** | WordCloud | 1.9.3 |
| **Production Server** | Gunicorn | 22.0.0 |
| **Language** | Python | 3.10+ |

---

## Project Structure

```
demo-repository-application/
├── app/                              # Application source code
│   ├── main.py                       # Entry point — Dash app initialization & routing
│   ├── config.py                     # Configuration: paths, colors, mappings, constants
│   ├── __init__.py
│   ├── assets/
│   │   └── styles.css                # Custom dark theme stylesheet
│   ├── tabs/                         # Dashboard tab modules
│   │   ├── tab_instructions.py       # Welcome & onboarding guide
│   │   ├── tab_equipment.py          # Military equipment transfer analysis
│   │   ├── tab_bases.py              # Military installations geospatial view
│   │   ├── tab_ecg.py                # ECG heartbeat classification & signal processing
│   │   ├── tab_healthcare.py         # Healthcare transcription analysis
│   │   ├── tab_combined.py           # Cross-dataset military intelligence
│   │   └── __init__.py
│   ├── components/                   # Reusable UI components
│   │   ├── kpi_card.py               # Key Performance Indicator cards
│   │   ├── chart_container.py        # Chart wrapper with loading spinner
│   │   └── __init__.py
│   └── data/                         # Data loading layer
│       ├── loader.py                 # Centralized data loading with caching
│       └── __init__.py
├── datasets/                         # Curated datasets (from Kaggle)
│   ├── README.md
│   ├── Military_Equipment_for_Local_Law_Enforcement/
│   │   ├── dod_all_states.csv        # 130,958 transfer records
│   │   └── AllStatesAndTerritoriesQTR4FY21.xlsx
│   ├── ecg_data/
│   │   ├── mitbih_train.csv          # 87,554 MIT-BIH training samples
│   │   ├── mitbih_test.csv           # 21,892 MIT-BIH testing samples
│   │   ├── ptbdb_normal.csv          # 4,046 normal heartbeats
│   │   └── ptbdb_abnormal.csv        # 10,506 abnormal heartbeats
│   ├── military_bases/
│   │   └── military-bases.csv        # 776 installations with GeoJSON boundaries
│   └── healthcare_documentation/
│       └── Healthcare Documentation Database.csv  # 3,836 medical transcriptions
├── data_cache/                       # Runtime cache (auto-generated)
│   └── ecg_precomputed.json          # ~2MB precomputed ECG statistics
├── scripts/
│   └── precompute_ecg_samples.py     # One-time ECG preprocessing script
├── requirements.txt                  # Python dependencies
├── run.sh                            # Startup script
└── README.md                         # This file
```

---

## Datasets

All datasets are sourced from [Kaggle](https://www.kaggle.com/) and are included in the `datasets/` directory.

### Military Equipment Transfers (1033 Program)

| Property | Value |
|----------|-------|
| **Records** | 130,958 |
| **Source** | Department of Defense LESO Program |
| **Format** | CSV (comma-delimited) |
| **Key Fields** | State, Agency Name, Item Name, Quantity, Acquisition Value, Ship Date, NSN, DEMIL Code |
| **Description** | Tracks military surplus equipment transferred to local law enforcement agencies across all 50 US states and territories under the DoD 1033 Program |

### ECG Heartbeat Signals

| Property | Value |
|----------|-------|
| **Records** | 123,998 total (87,554 train + 21,892 test + 14,552 PTB) |
| **Source** | MIT-BIH Arrhythmia Database & PTB Diagnostic Database |
| **Format** | CSV (no headers, 188 columns: 187 signal samples + 1 class label) |
| **Classes (MIT-BIH)** | Normal (N), Supraventricular (S), Ventricular (V), Fusion (F), Unknown (Q) |
| **Classes (PTB)** | Normal, Abnormal |
| **Description** | Pre-segmented individual heartbeat waveforms for arrhythmia classification |

### Military Bases & Installations

| Property | Value |
|----------|-------|
| **Records** | 776 |
| **Source** | US Military installation data |
| **Format** | CSV (semicolon-delimited, UTF-8 with BOM) |
| **Key Fields** | Site Name, Geo Point, Geo Shape (GeoJSON polygons), Component/Branch, State, Operational Status, Area, Perimeter |
| **Description** | Comprehensive listing of US military installations with geographic boundaries and branch classification |

### Healthcare Medical Transcriptions

| Property | Value |
|----------|-------|
| **Records** | 3,836 |
| **Source** | Medical transcription samples |
| **Format** | CSV (comma-delimited) |
| **Key Fields** | Serial No, medical_specialty (39 specialties), transcription, cleaned_transcription, keywords |
| **Description** | De-identified medical transcription records spanning 39 medical specialties for NLP and resource analysis |

---

## Dashboard Tabs

### 1. Instructions

A comprehensive onboarding tab with accordion-based guides for navigating each section of the dashboard. Includes data source citations, usage tips, and interactive guidance.

### 2. Equipment Transfers

Deep analysis of the DoD 1033 Program — military surplus equipment transferred to local law enforcement.

**Visualizations include:**
- KPI summary cards (total items, total value, agencies served, states covered)
- US choropleth map of equipment value/count by state
- Animated timeline of top 5 equipment categories over time (with play/pause)
- Treemap of equipment categories by acquisition value
- Per-capita equipment value normalized by state population (2020 Census)
- DEMIL code breakdown (demilitarization restriction levels A through Q)
- Top agencies, states, and items ranked by value
- Year-over-year growth rate trend analysis

**Filters:** State multi-select, year range slider, equipment category dropdown

### 3. Military Bases Map

Geospatial analysis of 776 US military installations across all branches.

**Visualizations include:**
- Interactive Mapbox map with branch-colored markers
- State density choropleth with marker overlay
- Stacked bar charts: bases by state and by branch
- Sunburst hierarchy drill-down (State → Component → Base)
- Small multiple maps (one per military branch)
- Base size distribution by branch (box plots)
- Area vs. perimeter scatter plot (identifies unusual installation shapes)
- Joint base analysis
- Operational status donut chart

**Filters:** Component/branch, operational status, state, joint base designation

### 4. ECG Analysis

Biomedical signal processing and visualization of heartbeat waveforms from two clinical databases.

**Visualizations include:**
- Animated ECG playback monitor with real-time PQRST peak detection
- Class distribution bar chart (5-class MIT-BIH + binary PTB)
- Mean waveform overlay by class with standard deviation bands
- Inter-class correlation heatmap
- PCA 2D embedding scatter plot (dimensionality reduction)
- Signal feature comparison (amplitude, energy, zero-crossings)
- Individual waveform browser with sample inspection

**Signal Processing Features:**
- PQRST fiducial point detection using `scipy.signal.find_peaks`
- PR interval, QT interval, and ST segment computation
- Moving average smoothing and min-max normalization
- Synthetic ECG beat generation for continuous playback

### 5. Healthcare Records

Medical transcription analysis for resource planning and specialty workload assessment.

**Visualizations include:**
- Specialty distribution bar chart (39 medical specialties)
- Resource demand quadrant plot (volume vs. complexity)
- Transcription length box plot by specialty
- Workload Pareto chart (cumulative concentration analysis)
- Resource allocation index (composite scoring model)
- Top 30 medical keywords word cloud
- Searchable, paginated data table with row expansion
- Full transcription viewer in collapsible panels

**Filters:** Medical specialty dropdown, keyword search input

### 6. Combined Intelligence

Cross-dataset analysis that joins military equipment transfer data with base installation data by state for strategic insights.

**Visualizations include:**
- Dual-layer choropleth map: equipment value heatmap + base location markers
- Correlation scatter: base count vs. equipment value with OLS regression trendline
- Quadrant analysis (4 strategic classification zones)
- Butterfly chart: normalized bases vs. equipment value (top 20 states)
- Equipment-per-base ratio analysis
- Regional comparison radar chart (4 normalized dimensions)
- Combined state ranking (weighted 50% bases + 50% equipment value)
- Branch vs. equipment category heatmap
- Agency reach bubble chart (3-way relationship visualization)

**Filters:** Census region, minimum bases threshold slider

---

## Architecture

The application follows a modular, callback-driven architecture:

```
main.py (App Controller & Router)
    │
    ├── Layout: Header + 6-Tab Navigation + Content Container
    ├── Routing Callback: render_tab() → dispatches active tab to correct module
    │
    ├── Tab Modules (Views + Logic)
    │   ├── tab_instructions.py    → Static HTML layout
    │   ├── tab_equipment.py       → update_equipment() callback → 11 figure outputs
    │   ├── tab_bases.py           → update_bases() callback → 9 figure outputs
    │   ├── tab_ecg.py             → playback + waveform callbacks → 7 figure outputs
    │   ├── tab_healthcare.py      → update_healthcare() callback → 7 figure outputs
    │   └── tab_combined.py        → update_combined() callback → 9 figure outputs
    │
    ├── Reusable Components
    │   ├── kpi_card()             → Bootstrap card with value, color, tooltip
    │   └── chart_container()      → Card wrapper + dcc.Loading spinner
    │
    ├── Data Layer (loader.py)
    │   ├── load_equipment()       → Cached DataFrame (130K rows)
    │   ├── load_bases()           → Cached DataFrame (776 rows, parsed geo)
    │   ├── load_healthcare()      → Cached DataFrame (3.8K rows)
    │   └── load_ecg_precomputed() → JSON cache (or auto-precompute from 555MB raw)
    │
    └── Configuration (config.py)
        ├── File paths & directories
        ├── Color palette (dark theme)
        ├── NSN → Equipment category mappings
        ├── DEMIL code labels
        ├── State abbreviation/name lookups
        ├── Census region groupings
        ├── State populations (2020)
        └── ECG class label definitions
```

**Key Architectural Patterns:**

- **Reactive Callbacks** — Dash `@callback` decorators link filter controls to chart update functions. When a user changes a dropdown or slider, all connected visualizations re-render automatically.
- **In-Memory Caching** — A module-level `_cache` dictionary in `loader.py` prevents redundant disk I/O. Each dataset is loaded once and reused across all callback invocations.
- **Centralized Configuration** — All color palettes, file paths, data mappings, and constants live in `config.py`, making the entire application easy to customize.
- **Component Reuse** — `kpi_card()` and `chart_container()` provide consistent styling and behavior (loading states, tooltips) across all tabs.
- **Lazy Precomputation** — The ECG pipeline automatically generates its 2MB cache file on first load if the cache is missing, avoiding the need for a manual preprocessing step.

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd demo-repository-application
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

**Option 1 — Direct Python:**

```bash
python3 app/main.py
```

**Option 2 — Shell script (installs dependencies automatically):**

```bash
chmod +x run.sh
./run.sh
```

**Option 3 — Precompute ECG cache first (optional):**

```bash
python3 scripts/precompute_ecg_samples.py
python3 app/main.py
```

Then open your browser to **http://localhost:8050**.

> **Note:** On first launch, the ECG precomputation step will run automatically if the cache file doesn't exist. This processes ~555MB of raw signal data into a ~2MB JSON cache and may take a minute.

### Production Deployment

```bash
gunicorn app.main:server --bind 0.0.0.0:8050 --workers 4
```

---

## Performance Optimizations

| Optimization | Description |
|-------------|-------------|
| **ECG Precomputation** | 555MB of raw CSV data is reduced to a ~2MB JSON cache containing 50 samples per class, mean/std waveforms, feature vectors, PCA embeddings, and correlation matrices |
| **In-Memory Data Cache** | All datasets are loaded once into a module-level dictionary and reused across callback invocations, eliminating redundant disk reads |
| **Lazy Loading** | Tab content is only rendered when the user navigates to it (`suppress_callback_exceptions=True`) |
| **Plotly Dark Template** | A single `plotly_dark` template is applied globally, reducing per-chart configuration overhead |
| **Selective Data Loading** | The combined intelligence tab only loads equipment and bases data — it doesn't pull in unrelated datasets |

---

## Configuration

All application configuration lives in `app/config.py`. Key configurable items include:

- **Color Palette** — Primary (`#0B0F19`), Secondary (`#38BDF8`), Success (`#34D399`), Danger (`#FB7185`), and branch-specific military colors
- **Federal Supply Class Mappings** — 99 NSN prefix codes mapped to human-readable equipment categories (Weapons, Aircraft, Vehicles, Medical Equipment, etc.)
- **DEMIL Codes** — Demilitarization restriction labels (A through Q)
- **State Data** — Full abbreviation/name lookups, Census region groupings, and 2020 population figures for per-capita normalization
- **ECG Labels** — MIT-BIH 5-class and PTB binary class definitions
- **File Paths** — All dataset and cache paths are defined relative to the project root

---

## Data Processing Pipeline

### Equipment Data Flow

```
User adjusts filters (state, year, category)
  → @callback triggered
  → load_equipment() returns cached DataFrame
  → Apply filters (state, year range, category)
  → Compute aggregations (KPIs, groupby state, groupby year, treemap hierarchy)
  → Generate 11 Plotly Figure objects
  → Dash re-renders all connected chart components
```

### ECG Processing Pipeline

```
Raw CSV files (555MB total)
  → Load 4 files (mitbih_train/test, ptbdb_normal/abnormal)
  → Extract signals (columns 1-187) and labels (column 188, cast to int)
  → Per-class statistics: mean waveform, std waveform, feature vectors
  → Sample 50 beats per class (seed=42 for reproducibility)
  → PCA 2D embedding for visualization
  → Inter-class correlation matrix
  → Serialize to JSON → data_cache/ecg_precomputed.json (~2MB)
```

### PQRST Detection Algorithm

```
Input: 187-sample heartbeat waveform
  → R-peak: global maximum
  → Q-point: minimum in the 18% window before R
  → S-point: minimum in the 18% window after R
  → P-wave: local maximum in the first 40% of the signal (scipy.signal.find_peaks)
  → T-wave: local maximum after S-point (scipy.signal.find_peaks)
  → Compute intervals: PR, QT, ST segment
```

### Equipment Categorization

```
NSN (National Stock Number): e.g., "2540-01-565-4700"
  → Extract first 2 digits: "25"
  → Lookup in Federal Supply Class mapping
  → Result: "Vehicular Equipment"
```

---

## Why This Project Exists

This dashboard was built as a **fun personal project** to explore and demonstrate how Large Language Models can be used as development partners to create real, functional software. The goal was to see how far LLM-assisted development could go — from initial architecture decisions, through data pipeline design, to polished interactive visualizations with a production-ready deployment setup.

The result is a fully working multi-domain analytics platform that processes over **130,000 military equipment records**, **124,000 ECG heartbeat signals**, **776 military installations**, and **3,800 medical transcriptions** — all visualized through a modern, interactive web interface.

**This is not intended for production use or real analytical decision-making.** It's a demonstration of what's possible when combining human creativity with AI-assisted development.

---

## License

This project is provided as-is for demonstration and educational purposes. The datasets included are sourced from publicly available Kaggle repositories — please refer to their respective licenses for usage terms.
