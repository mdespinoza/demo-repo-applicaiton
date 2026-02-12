"""Integration tests for Dash callback functions.

Tests call callback functions directly with mock data injected
into the loader cache. Each callback's return values are validated
for correct types and structure.
"""

import io
import json
import pytest
import pandas as pd
import plotly.graph_objects as go

from app.data import loader

# ── Fixtures to seed loader cache with mock data ─────────────────


@pytest.fixture
def seed_equipment_cache(mock_equipment_df):
    """Inject mock equipment data into the loader cache."""
    loader._cache["equipment"] = mock_equipment_df


@pytest.fixture
def seed_bases_cache(mock_bases_df):
    """Inject mock bases data into the loader cache."""
    loader._cache["bases"] = mock_bases_df


@pytest.fixture
def seed_healthcare_cache(mock_healthcare_df):
    """Inject mock healthcare data into the loader cache."""
    loader._cache["healthcare"] = mock_healthcare_df


@pytest.fixture
def seed_ecg_cache(mock_ecg_precomputed):
    """Inject mock ECG data into the loader cache."""
    loader._cache["ecg"] = mock_ecg_precomputed


# ── Helper: generate store data from mock DataFrames ──────────────


def make_equip_store(mock_df):
    """Serialize a mock equipment DataFrame as the filter store would."""
    state_value = mock_df.groupby("State")["Acquisition Value"].sum()
    state_qty = mock_df.groupby("State")["Quantity"].sum()
    kpis = {
        "total_items": int(mock_df["Quantity"].sum()),
        "total_value": float(mock_df["Acquisition Value"].sum()),
        "n_agencies": int(mock_df["Agency Name"].nunique()),
        "n_states": int(mock_df["State"].nunique()),
    }
    store = {
        "df": mock_df.to_json(date_format="iso", orient="split"),
        "state_value": state_value.to_json(),
        "state_qty": state_qty.to_json(),
        "kpis": kpis,
    }
    return json.dumps(store)


def make_bases_store(mock_df):
    """Serialize a mock bases DataFrame as the filter store would."""
    df = mock_df.copy()
    df["hovertext"] = (
        "<b>" + df["Site Name"].fillna("") + "</b><br>"
        + df["COMPONENT"].fillna("") + "<br>"
        + df["State Terr"].fillna("") + "<br>"
        + df["Oper Stat"].fillna("")
    )
    store = {
        "df": df.to_json(date_format="iso", orient="split"),
    }
    return json.dumps(store)


def make_health_store(mock_df):
    """Serialize a mock healthcare DataFrame as the filter store would."""
    spec_counts = mock_df["medical_specialty"].value_counts().reset_index()
    spec_counts.columns = ["Specialty", "Count"]
    spec_stats = (
        mock_df.groupby("medical_specialty")
        .agg(
            volume=("medical_specialty", "size"),
            avg_complexity=("transcription_length", "mean"),
        )
        .reset_index()
    )
    store = {
        "df": mock_df.to_json(date_format="iso", orient="split"),
        "spec_counts": spec_counts.to_json(orient="split"),
        "spec_stats": spec_stats.to_json(orient="split"),
    }
    return json.dumps(store)


# ═══════════════════════════════════════════════════════════════════
# Equipment Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestEquipmentCallbacks:
    def test_filter_callback(self, seed_equipment_cache, mock_equipment_df):
        """Filter callback returns valid JSON store data."""
        from app.tabs.tab_equipment import update_equip_store

        result = update_equip_store(
            states=None,
            year_range=[2019, 2021],
            categories=None,
        )
        assert result is not None
        data = json.loads(result)
        assert "df" in data
        assert "kpis" in data
        assert "state_value" in data
        assert "state_qty" in data
        df = pd.read_json(io.StringIO(data["df"]), orient="split")
        assert len(df) > 0

    def test_kpi_callback(self, seed_equipment_cache, mock_equipment_df):
        """KPI callback returns an HTML component."""
        from app.tabs.tab_equipment import update_equip_kpis

        store_data = make_equip_store(mock_equipment_df)
        result = update_equip_kpis(store_data)
        assert result is not None

    def test_maps_callback(self, seed_equipment_cache, mock_equipment_df):
        """Maps callback returns 3 figures."""
        from app.tabs.tab_equipment import update_equip_maps

        store_data = make_equip_store(mock_equipment_df)
        result = update_equip_maps(store_data, "value")
        assert len(result) == 3
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_maps_callback_count_metric(self, seed_equipment_cache, mock_equipment_df):
        """Maps callback with count metric returns valid figures."""
        from app.tabs.tab_equipment import update_equip_maps

        store_data = make_equip_store(mock_equipment_df)
        result = update_equip_maps(store_data, "count")
        assert len(result) == 3

    def test_bars_callback(self, seed_equipment_cache, mock_equipment_df):
        """Bars callback returns 4 figures."""
        from app.tabs.tab_equipment import update_equip_bars

        store_data = make_equip_store(mock_equipment_df)
        result = update_equip_bars(store_data)
        assert len(result) == 4
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_timeline_callback(self, seed_equipment_cache, mock_equipment_df):
        """Timeline callback returns a figure."""
        from app.tabs.tab_equipment import update_equip_timeline

        store_data = make_equip_store(mock_equipment_df)
        result = update_equip_timeline(store_data)
        assert isinstance(result, go.Figure)

    def test_categories_callback(self, seed_equipment_cache, mock_equipment_df):
        """Categories callback returns 2 figures."""
        from app.tabs.tab_equipment import update_equip_categories

        store_data = make_equip_store(mock_equipment_df)
        result = update_equip_categories(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_state_filter(self, seed_equipment_cache, mock_equipment_df):
        """Filtering by state still works through the store."""
        from app.tabs.tab_equipment import update_equip_store, update_equip_kpis

        store_data = update_equip_store(
            states=["CA"],
            year_range=[2019, 2021],
            categories=None,
        )
        result = update_equip_kpis(store_data)
        assert result is not None

    def test_category_filter(self, seed_equipment_cache, mock_equipment_df):
        """Filtering by category narrows the data."""
        from app.tabs.tab_equipment import update_equip_store, update_equip_bars

        store_data = update_equip_store(
            states=None,
            year_range=[2019, 2021],
            categories=["Weapons & Firearms"],
        )
        result = update_equip_bars(store_data)
        assert len(result) == 4

    def test_none_store_returns_no_update(self, seed_equipment_cache):
        """Passing None store data returns no_update."""
        from dash import no_update
        from app.tabs.tab_equipment import update_equip_kpis

        result = update_equip_kpis(None)
        assert result is no_update


# ═══════════════════════════════════════════════════════════════════
# Bases Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestBasesCallbacks:
    def test_filter_callback(self, seed_bases_cache, mock_bases_df):
        """Filter callback returns valid JSON store data."""
        from app.tabs.tab_bases import update_bases_filter

        result = update_bases_filter(
            components=None,
            statuses=None,
            states=None,
            joints=None,
        )
        assert result is not None

    def test_maps_callback(self, seed_bases_cache, mock_bases_df):
        """Maps callback returns 2 figures."""
        from app.tabs.tab_bases import update_bases_maps

        store_data = make_bases_store(mock_bases_df)
        result = update_bases_maps(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_summary_callback(self, seed_bases_cache, mock_bases_df):
        """Summary callback returns 2 figures."""
        from app.tabs.tab_bases import update_bases_summary

        store_data = make_bases_store(mock_bases_df)
        result = update_bases_summary(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_state_callback(self, seed_bases_cache, mock_bases_df):
        """State callback returns 2 figures."""
        from app.tabs.tab_bases import update_bases_state

        store_data = make_bases_store(mock_bases_df)
        result = update_bases_state(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_detail_callback(self, seed_bases_cache, mock_bases_df):
        """Detail callback returns 4 figures."""
        from app.tabs.tab_bases import update_bases_detail

        store_data = make_bases_store(mock_bases_df)
        result = update_bases_detail(store_data)
        assert len(result) == 4
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_component_filter(self, seed_bases_cache, mock_bases_df):
        """Filtering by component works through the store."""
        from app.tabs.tab_bases import update_bases_filter, update_bases_maps

        store_data = update_bases_filter(
            components=["Army Active"],
            statuses=None,
            states=None,
            joints=None,
        )
        result = update_bases_maps(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)


# ═══════════════════════════════════════════════════════════════════
# Healthcare Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestHealthcareCallbacks:
    def test_filter_callback(self, seed_healthcare_cache, mock_healthcare_df):
        """Filter callback returns valid JSON store data."""
        from app.tabs.tab_healthcare import filter_healthcare_data

        result = filter_healthcare_data(specialties=None, keyword=None)
        assert result is not None

    def test_distribution_callback(self, seed_healthcare_cache, mock_healthcare_df):
        """Distribution callback returns 2 figures."""
        from app.tabs.tab_healthcare import update_health_distribution

        store_data = make_health_store(mock_healthcare_df)
        result = update_health_distribution(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_analysis_callback(self, seed_healthcare_cache, mock_healthcare_df):
        """Analysis callback returns 3 figures."""
        from app.tabs.tab_healthcare import update_health_analysis

        store_data = make_health_store(mock_healthcare_df)
        result = update_health_analysis(store_data)
        assert len(result) == 3
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_keywords_table_callback(self, seed_healthcare_cache, mock_healthcare_df):
        """Keywords+table callback returns figure + list."""
        from app.tabs.tab_healthcare import update_health_keywords_table

        store_data = make_health_store(mock_healthcare_df)
        result = update_health_keywords_table(store_data)
        assert len(result) == 2
        assert isinstance(result[0], go.Figure)
        assert isinstance(result[1], list)

    def test_specialty_filter(self, seed_healthcare_cache, mock_healthcare_df):
        """Filtering by specialty narrows results."""
        from app.tabs.tab_healthcare import filter_healthcare_data, update_health_distribution

        store_data = filter_healthcare_data(
            specialties=["Orthopedic"],
            keyword=None,
        )
        result = update_health_distribution(store_data)
        assert len(result) == 2

    def test_keyword_filter(self, seed_healthcare_cache, mock_healthcare_df):
        """Keyword search filters data by keyword match."""
        from app.tabs.tab_healthcare import filter_healthcare_data, update_health_keywords_table

        store_data = filter_healthcare_data(
            specialties=None,
            keyword="knee",
        )
        result = update_health_keywords_table(store_data)
        assert len(result) == 2

    def test_show_transcription_no_selection(self, seed_healthcare_cache):
        """No selection returns collapsed state."""
        from app.tabs.tab_healthcare import show_transcription

        is_open, text = show_transcription(
            selected_rows=None,
            data=None,
        )
        assert is_open is False
        assert text == ""


# ═══════════════════════════════════════════════════════════════════
# ECG Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestEcgCallbacks:
    def test_update_class_distribution(self, seed_ecg_cache):
        """Distribution callback returns a Figure."""
        from app.tabs.tab_ecg import update_class_distribution

        fig = update_class_distribution(dataset="mitbih", scale="linear")
        assert isinstance(fig, go.Figure)

    def test_update_class_distribution_log_scale(self, seed_ecg_cache):
        """Log scale also works."""
        from app.tabs.tab_ecg import update_class_distribution

        fig = update_class_distribution(dataset="mitbih", scale="log")
        assert isinstance(fig, go.Figure)

    def test_update_waveform_overlay(self, seed_ecg_cache):
        """Waveform overlay returns a Figure."""
        from app.tabs.tab_ecg import update_waveform_overlay

        fig = update_waveform_overlay(dataset="mitbih")
        assert isinstance(fig, go.Figure)

    def test_update_features(self, seed_ecg_cache):
        """Features callback returns a Figure."""
        from app.tabs.tab_ecg import update_features

        fig = update_features(dataset="mitbih")
        assert isinstance(fig, go.Figure)

    def test_update_correlation(self, seed_ecg_cache):
        """Correlation heatmap returns a Figure."""
        from app.tabs.tab_ecg import update_correlation

        fig = update_correlation(dataset="mitbih")
        assert isinstance(fig, go.Figure)

    def test_update_pca_scatter(self, seed_ecg_cache):
        """PCA scatter returns a Figure."""
        from app.tabs.tab_ecg import update_pca_scatter

        fig = update_pca_scatter(dataset="mitbih")
        assert isinstance(fig, go.Figure)

    def test_update_class_options_mitbih(self, seed_ecg_cache):
        """MIT-BIH has 5 class options."""
        from app.tabs.tab_ecg import update_class_options

        options, default = update_class_options(dataset="mitbih")
        assert len(options) == 5
        assert default == "Normal (N)"

    def test_update_class_options_ptbdb(self, seed_ecg_cache):
        """PTB dataset has 2 classes."""
        from app.tabs.tab_ecg import update_class_options

        options, default = update_class_options(dataset="ptbdb")
        assert len(options) == 2
        assert default == "Normal"


# ═══════════════════════════════════════════════════════════════════
# Combined Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestCombinedCallbacks:
    def test_filter_callback(self, seed_equipment_cache, seed_bases_cache):
        """Filter callback returns valid JSON store data."""
        from app.tabs.tab_combined import update_combined_store

        result = update_combined_store(regions=None, min_bases=0)
        assert result is not None
        data = json.loads(result)
        assert "combined" in data
        assert "branch_by_state" in data
        assert "selected_states" in data

    def test_maps_callback(self, seed_equipment_cache, seed_bases_cache):
        """Maps callback returns 2 figures."""
        from app.tabs.tab_combined import update_combined_store, update_combined_maps

        store_data = update_combined_store(regions=None, min_bases=0)
        result = update_combined_maps(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_scatter_callback(self, seed_equipment_cache, seed_bases_cache):
        """Scatter callback returns 3 figures."""
        from app.tabs.tab_combined import update_combined_store, update_combined_scatter

        store_data = update_combined_store(regions=None, min_bases=0)
        result = update_combined_scatter(store_data)
        assert len(result) == 3
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_bars_callback(self, seed_equipment_cache, seed_bases_cache):
        """Bars callback returns 3 figures."""
        from app.tabs.tab_combined import update_combined_store, update_combined_bars

        store_data = update_combined_store(regions=None, min_bases=0)
        result = update_combined_bars(store_data)
        assert len(result) == 3
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_advanced_callback(self, seed_equipment_cache, seed_bases_cache):
        """Advanced callback returns 2 figures."""
        from app.tabs.tab_combined import update_combined_store, update_combined_advanced

        store_data = update_combined_store(regions=None, min_bases=0)
        result = update_combined_advanced(store_data)
        assert len(result) == 2
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_region_filter(self, seed_equipment_cache, seed_bases_cache):
        """Region filter returns valid output."""
        from app.tabs.tab_combined import update_combined_store, update_combined_scatter

        store_data = update_combined_store(regions=["South"], min_bases=0)
        result = update_combined_scatter(store_data)
        assert len(result) == 3
        for fig in result:
            assert isinstance(fig, go.Figure)


# ═══════════════════════════════════════════════════════════════════
# ECG Utility Function Tests
# ═══════════════════════════════════════════════════════════════════


class TestEcgUtilities:
    def test_generate_ecg_beat_length(self):
        """Generated beat has requested length."""
        from app.tabs.tab_ecg import _generate_ecg_beat

        beat = _generate_ecg_beat(300)
        assert len(beat) == 300

    def test_generate_ecg_beat_default_length(self):
        """Default beat length produces output."""
        from app.tabs.tab_ecg import _generate_ecg_beat

        beat = _generate_ecg_beat()
        assert len(beat) > 0
        assert all(isinstance(v, float) for v in beat)

    def test_generate_ecg_beat_with_class(self):
        """Class-specific parameters modify the beat shape."""
        from app.tabs.tab_ecg import _generate_ecg_beat

        normal = _generate_ecg_beat(200, "Normal (N)")
        abnormal = _generate_ecg_beat(200, "Abnormal")
        assert len(normal) == 200
        assert len(abnormal) == 200
        # Different classes should produce different waveforms
        assert normal != abnormal

    def test_detect_ecg_fiducials_synthetic_beat(self):
        """Fiducial detection on a synthetic normal beat finds R peak."""
        from app.tabs.tab_ecg import _generate_ecg_beat, detect_ecg_fiducials

        beat = _generate_ecg_beat(200, "Normal (N)")
        fiducials = detect_ecg_fiducials(beat)

        assert fiducials["R"] is not None
        assert fiducials["R"]["amplitude"] > 0.5

    def test_detect_ecg_fiducials_flat_signal(self):
        """Flat signal returns all None fiducials."""
        from app.tabs.tab_ecg import detect_ecg_fiducials

        flat = [0.0] * 200
        fiducials = detect_ecg_fiducials(flat)
        assert fiducials["R"] is None
        assert fiducials["Q"] is None
        assert fiducials["S"] is None
        assert fiducials["P"] is None
        assert fiducials["T"] is None
