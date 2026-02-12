"""Integration tests for Dash callback functions.

Tests call callback functions directly with mock data injected
into the loader cache. Each callback's return values are validated
for correct types and structure.
"""

import pytest
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


# ═══════════════════════════════════════════════════════════════════
# Equipment Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestEquipmentCallbacks:
    def test_update_equipment_no_filters(self, seed_equipment_cache):
        """Callback with no filters returns all 11 outputs."""
        from app.tabs.tab_equipment import update_equipment

        result = update_equipment(
            states=None,
            year_range=[2019, 2021],
            categories=None,
            map_metric="value",
        )
        assert len(result) == 11

        # First output is KPI children (html component)
        kpis = result[0]
        assert kpis is not None

        # Remaining 10 outputs should be Plotly figures
        for fig in result[1:]:
            assert isinstance(fig, go.Figure)

    def test_update_equipment_state_filter(self, seed_equipment_cache):
        """Filtering by state should still return valid figures."""
        from app.tabs.tab_equipment import update_equipment

        result = update_equipment(
            states=["CA"],
            year_range=[2019, 2021],
            categories=None,
            map_metric="count",
        )
        assert len(result) == 11
        for fig in result[1:]:
            assert isinstance(fig, go.Figure)

    def test_update_equipment_category_filter(self, seed_equipment_cache):
        """Filtering by category narrows the data."""
        from app.tabs.tab_equipment import update_equipment

        result = update_equipment(
            states=None,
            year_range=[2019, 2021],
            categories=["Weapons & Firearms"],
            map_metric="value",
        )
        assert len(result) == 11


# ═══════════════════════════════════════════════════════════════════
# Bases Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestBasesCallbacks:
    def test_update_bases_no_filters(self, seed_bases_cache):
        """Callback with no filters returns 10 figure outputs."""
        from app.tabs.tab_bases import update_bases

        result = update_bases(
            components=None,
            statuses=None,
            states=None,
            joints=None,
        )
        assert len(result) == 10
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_update_bases_component_filter(self, seed_bases_cache):
        """Filtering by component returns valid figures."""
        from app.tabs.tab_bases import update_bases

        result = update_bases(
            components=["Army Active"],
            statuses=None,
            states=None,
            joints=None,
        )
        assert len(result) == 10
        for fig in result:
            assert isinstance(fig, go.Figure)


# ═══════════════════════════════════════════════════════════════════
# Healthcare Tab Callbacks
# ═══════════════════════════════════════════════════════════════════


class TestHealthcareCallbacks:
    def test_update_healthcare_no_filters(self, seed_healthcare_cache):
        """Callback with no filters returns 7 outputs."""
        from app.tabs.tab_healthcare import update_healthcare

        result = update_healthcare(specialties=None, keyword=None)
        assert len(result) == 7

        # First 6 are figures
        for fig in result[:6]:
            assert isinstance(fig, go.Figure)

        # Last one is table data (list of dicts)
        table_data = result[6]
        assert isinstance(table_data, list)

    def test_update_healthcare_specialty_filter(self, seed_healthcare_cache):
        """Filtering by specialty narrows results."""
        from app.tabs.tab_healthcare import update_healthcare

        result = update_healthcare(
            specialties=["Orthopedic"],
            keyword=None,
        )
        assert len(result) == 7

    def test_update_healthcare_keyword_filter(self, seed_healthcare_cache):
        """Keyword search filters data by keyword match."""
        from app.tabs.tab_healthcare import update_healthcare

        result = update_healthcare(
            specialties=None,
            keyword="knee",
        )
        assert len(result) == 7

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
    def test_update_combined_no_filters(self, seed_equipment_cache, seed_bases_cache):
        """Combined callback returns 10 figures."""
        from app.tabs.tab_combined import update_combined

        result = update_combined(regions=None, min_bases=0)
        assert len(result) == 10
        for fig in result:
            assert isinstance(fig, go.Figure)

    def test_update_combined_region_filter(self, seed_equipment_cache, seed_bases_cache):
        """Region filter returns valid output."""
        from app.tabs.tab_combined import update_combined

        result = update_combined(regions=["South"], min_bases=0)
        assert len(result) == 10
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
