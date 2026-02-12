"""Smoke tests demonstrating fixture usage and basic test patterns."""

import pandas as pd


class TestFixtureUsage:
    """Verify that test fixtures produce correct data structures."""

    def test_equipment_fixture_columns(self, mock_equipment_df):
        required = {
            "State",
            "Agency Name",
            "NSN",
            "Item Name",
            "Quantity",
            "Acquisition Value",
            "Year",
            "Category",
        }
        assert required.issubset(set(mock_equipment_df.columns))

    def test_equipment_fixture_types(self, mock_equipment_df):
        assert mock_equipment_df["Acquisition Value"].dtype == float
        assert pd.api.types.is_datetime64_any_dtype(mock_equipment_df["Ship Date"])

    def test_bases_fixture_has_coordinates(self, mock_bases_df):
        assert "lat" in mock_bases_df.columns
        assert "lon" in mock_bases_df.columns
        assert mock_bases_df["lat"].notna().all()

    def test_healthcare_fixture_has_transcription(self, mock_healthcare_df):
        assert "transcription_length" in mock_healthcare_df.columns
        assert (mock_healthcare_df["transcription_length"] > 0).all()

    def test_ecg_fixture_structure(self, mock_ecg_precomputed):
        assert "mitbih" in mock_ecg_precomputed
        assert "ptbdb" in mock_ecg_precomputed
        assert "train" in mock_ecg_precomputed["mitbih"]["splits"]
        assert "samples" in mock_ecg_precomputed["mitbih"]["splits"]["train"]

    def test_cache_is_clear_between_tests(self):
        from app.data.loader import _cache

        assert len(_cache) == 0, "Cache should be empty at test start"
