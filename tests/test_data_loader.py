"""Comprehensive unit tests for app.data.loader module."""
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, mock_open

from app.data import loader
from app.config import get_equipment_category


# ═══════════════════════════════════════════════════════════════════
# Helper function tests
# ═══════════════════════════════════════════════════════════════════


class TestGetEquipmentCategory:
    """Test the NSN -> category mapping function."""

    def test_weapons_nsn(self):
        assert get_equipment_category("1005-01-001-0001") == "Weapons & Firearms"

    def test_vehicle_nsn(self):
        assert get_equipment_category("2320-01-002-0002") == "Vehicles & Transport"

    def test_communications_nsn(self):
        assert get_equipment_category("5820-01-004-0004") == "Communications & Electronics"

    def test_aircraft_nsn(self):
        assert get_equipment_category("1510-01-345-6789") == "Aircraft & Parts"

    def test_unknown_prefix_returns_other(self):
        assert get_equipment_category("9999-01-000-0000") == "Other"

    def test_none_returns_other(self):
        assert get_equipment_category(None) == "Other"

    def test_integer_returns_other(self):
        assert get_equipment_category(12345) == "Other"

    def test_short_string_returns_other(self):
        assert get_equipment_category("5") == "Other"

    def test_empty_string_returns_other(self):
        assert get_equipment_category("") == "Other"


class TestValidateDataframe:
    """Test the validate_dataframe() helper."""

    def test_valid_dataframe(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        assert loader.validate_dataframe(df, ["a", "b"]) is True

    def test_empty_dataframe_is_valid(self):
        df = pd.DataFrame({"a": [], "b": []})
        assert loader.validate_dataframe(df, ["a", "b"]) is True

    def test_missing_columns_raises(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="Missing required columns"):
            loader.validate_dataframe(df, ["a", "b"])

    def test_non_dataframe_raises(self):
        with pytest.raises(ValueError, match="Expected DataFrame"):
            loader.validate_dataframe("not a df", ["a"])

    def test_none_raises(self):
        with pytest.raises(ValueError, match="Expected DataFrame"):
            loader.validate_dataframe(None, ["a"])

    def test_custom_name_in_error(self):
        with pytest.raises(ValueError, match="MyData"):
            loader.validate_dataframe(42, ["a"], name="MyData")


# ═══════════════════════════════════════════════════════════════════
# load_equipment() tests
# ═══════════════════════════════════════════════════════════════════


class TestLoadEquipment:
    """Test equipment data loading, caching, and error handling."""

    @patch("app.data.loader.pd.read_csv")
    def test_returns_dataframe_with_transformations(self, mock_csv):
        """Verify successful loading processes all transformations."""
        mock_csv.return_value = pd.DataFrame({
            "State": ["CA"],
            "Agency Name": [" LAPD "],
            "NSN": ["1005-01-001-0001"],
            "Item Name": ["RIFLE"],
            "Quantity": ["10"],
            "Acquisition Value": ["5000.00"],
            "DEMIL Code": ["D"],
            "Ship Date": ["2020-01-15"],
            "Station Type": ["State"],
            "UI": ["Each"],
        })

        df = loader.load_equipment()

        assert len(df) == 1
        assert df["Agency Name"].iloc[0] == "LAPD"  # stripped
        assert df["Acquisition Value"].dtype == float
        assert df["Quantity"].dtype == int
        assert pd.api.types.is_datetime64_any_dtype(df["Ship Date"])
        assert "Year" in df.columns
        assert "Category" in df.columns
        assert df["Category"].iloc[0] == "Weapons & Firearms"

    @patch("app.data.loader.pd.read_csv")
    def test_caching_returns_same_object(self, mock_csv):
        """Second call should return cached result without re-reading CSV."""
        mock_csv.return_value = pd.DataFrame({
            "State": ["CA"], "Agency Name": ["LAPD"],
            "NSN": ["1005-01-001-0001"], "Item Name": ["RIFLE"],
            "Quantity": [10], "Acquisition Value": [5000.0],
            "DEMIL Code": ["D"], "Ship Date": ["2020-01-15"],
            "Station Type": ["State"], "UI": ["Each"],
        })

        df1 = loader.load_equipment()
        df2 = loader.load_equipment()

        assert mock_csv.call_count == 1
        assert df1 is df2

    @patch("app.data.loader.pd.read_csv", side_effect=FileNotFoundError("not found"))
    def test_file_not_found_returns_empty(self, mock_csv):
        """Missing file should return empty DataFrame, not crash."""
        df = loader.load_equipment()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("app.data.loader.pd.read_csv", side_effect=pd.errors.ParserError("corrupt"))
    def test_parser_error_returns_empty(self, mock_csv):
        """Corrupted CSV should return empty DataFrame."""
        df = loader.load_equipment()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("app.data.loader.pd.read_csv")
    def test_coercion_of_bad_values(self, mock_csv):
        """Non-numeric values should be coerced, not crash."""
        mock_csv.return_value = pd.DataFrame({
            "State": ["CA"], "Agency Name": ["LAPD"],
            "NSN": ["1005-01-001-0001"], "Item Name": ["RIFLE"],
            "Quantity": ["INVALID"], "Acquisition Value": ["NOT_A_NUMBER"],
            "DEMIL Code": [None], "Ship Date": ["not-a-date"],
            "Station Type": [None], "UI": ["Each"],
        })

        df = loader.load_equipment()
        assert df["Acquisition Value"].iloc[0] == 0.0
        assert df["Quantity"].iloc[0] == 0
        assert pd.isna(df["Ship Date"].iloc[0])
        assert df["DEMIL Code"].iloc[0] == "Unknown"
        assert df["Station Type"].iloc[0] == "Unknown"

    @patch("app.data.loader.pd.read_csv")
    def test_empty_dataframe_cached(self, mock_csv):
        """Error path caches empty DataFrame to avoid repeated failures."""
        mock_csv.side_effect = FileNotFoundError("missing")
        loader.load_equipment()
        assert "equipment" in loader._cache
        assert loader._cache["equipment"].empty


# ═══════════════════════════════════════════════════════════════════
# load_bases() tests
# ═══════════════════════════════════════════════════════════════════


class TestLoadBases:
    """Test bases data loading, geo parsing, and error handling."""

    @patch("app.data.loader.pd.read_csv")
    def test_success_with_geo_parsing(self, mock_csv):
        mock_csv.return_value = pd.DataFrame({
            "Geo Point": ["31.23, -85.65", "34.91, -117.88"],
            "COMPONENT": [" Army Active ", "Air Force Active"],
            "Site Name": ["Fort Rucker", "Edwards AFB"],
            "State Terr": ["Alabama", "California"],
            "Oper Stat": ["Active", None],
            "Joint Base": ["N/A", None],
            "AREA": ["880", "470"],
            "PERIMETER": ["120", "90"],
        })

        df = loader.load_bases()
        assert len(df) == 2
        assert df["lat"].iloc[0] == pytest.approx(31.23, abs=0.01)
        assert df["lon"].iloc[0] == pytest.approx(-85.65, abs=0.01)
        assert df["COMPONENT"].iloc[0] == "Army Active"  # stripped
        assert df["Oper Stat"].iloc[1] == "Unknown"  # fillna

    @patch("app.data.loader.pd.read_csv")
    def test_invalid_geo_point_dropped(self, mock_csv):
        """Rows with unparseable Geo Point should be dropped."""
        mock_csv.return_value = pd.DataFrame({
            "Geo Point": ["INVALID", "34.91, -117.88"],
            "COMPONENT": ["Army", "Air Force"],
            "Site Name": ["Base A", "Base B"],
            "State Terr": ["Alabama", "California"],
            "Oper Stat": ["Active", "Active"],
            "Joint Base": ["N/A", "N/A"],
            "AREA": [100, 200],
            "PERIMETER": [50, 60],
        })

        df = loader.load_bases()
        assert len(df) == 1  # Only valid row kept

    @patch("app.data.loader.pd.read_csv", side_effect=FileNotFoundError)
    def test_file_not_found_returns_empty(self, mock_csv):
        df = loader.load_bases()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("app.data.loader.pd.read_csv")
    def test_caching(self, mock_csv):
        mock_csv.return_value = pd.DataFrame({
            "Geo Point": ["31.23, -85.65"],
            "COMPONENT": ["Army Active"],
            "Site Name": ["Fort Rucker"],
            "State Terr": ["Alabama"],
            "Oper Stat": ["Active"],
            "Joint Base": ["N/A"],
            "AREA": [880],
            "PERIMETER": [120],
        })

        loader.load_bases()
        loader.load_bases()
        assert mock_csv.call_count == 1


# ═══════════════════════════════════════════════════════════════════
# load_healthcare() tests
# ═══════════════════════════════════════════════════════════════════


class TestLoadHealthcare:
    """Test healthcare data loading and error handling."""

    @patch("app.data.loader.pd.read_csv")
    def test_success_with_transformations(self, mock_csv):
        mock_csv.return_value = pd.DataFrame({
            "Serial No": [0],
            "description": ["Patient with allergies"],
            "medical_specialty": [" Allergy / Immunology "],
            "sample_name": ["Sample A"],
            "transcription": ["text"],
            "keywords": [" allergy, rhinitis, "],
            "cleaned_transcription": ["cleaned text here"],
        })

        df = loader.load_healthcare()
        assert len(df) == 1
        assert df["medical_specialty"].iloc[0] == "Allergy / Immunology"  # stripped
        assert "transcription_length" in df.columns
        assert df["transcription_length"].iloc[0] == len("cleaned text here")
        assert df["keywords"].iloc[0] == "allergy, rhinitis"  # rstripped comma

    @patch("app.data.loader.pd.read_csv", side_effect=FileNotFoundError)
    def test_file_not_found_returns_empty(self, mock_csv):
        df = loader.load_healthcare()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("app.data.loader.pd.read_csv")
    def test_caching(self, mock_csv):
        mock_csv.return_value = pd.DataFrame({
            "Serial No": [0], "description": ["test"],
            "medical_specialty": ["Specialty"],
            "sample_name": ["A"], "transcription": ["text"],
            "keywords": ["kw"], "cleaned_transcription": ["text"],
        })
        loader.load_healthcare()
        loader.load_healthcare()
        assert mock_csv.call_count == 1

    @patch("app.data.loader.pd.read_csv", side_effect=pd.errors.ParserError("bad"))
    def test_parser_error_returns_empty(self, mock_csv):
        df = loader.load_healthcare()
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ═══════════════════════════════════════════════════════════════════
# load_ecg_precomputed() tests
# ═══════════════════════════════════════════════════════════════════


class TestLoadEcgPrecomputed:
    """Test ECG precomputed data loading and error handling."""

    @patch("app.data.loader.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    @patch("app.data.loader.json.load")
    def test_success(self, mock_json, mock_file, mock_exists):
        expected = {"mitbih": {"class_names": {}, "splits": {}}, "ptbdb": {}}
        mock_json.return_value = expected

        data = loader.load_ecg_precomputed()
        assert data == expected

    @patch("app.data.loader.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    @patch("app.data.loader.json.load")
    def test_caching(self, mock_json, mock_file, mock_exists):
        mock_json.return_value = {"mitbih": {}, "ptbdb": {}}

        loader.load_ecg_precomputed()
        loader.load_ecg_precomputed()
        assert mock_json.call_count == 1

    @patch("app.data.loader.os.path.exists", return_value=False)
    @patch("app.data.loader._precompute_ecg", return_value=None)
    def test_precompute_failure_returns_empty(self, mock_precompute, mock_exists):
        """If cache missing and precompute fails, return empty structure."""
        data = loader.load_ecg_precomputed()
        assert "mitbih" in data
        assert "ptbdb" in data
        assert data["mitbih"]["splits"] == {}

    @patch("app.data.loader.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="NOT JSON")
    @patch("app.data.loader.json.load", side_effect=json.JSONDecodeError("bad", "", 0))
    def test_corrupted_cache_returns_empty(self, mock_json, mock_file, mock_exists):
        """Corrupted JSON cache should return empty structure."""
        data = loader.load_ecg_precomputed()
        assert "mitbih" in data
        assert "ptbdb" in data

    @patch("app.data.loader.os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found_returns_empty(self, mock_file, mock_exists):
        data = loader.load_ecg_precomputed()
        assert "mitbih" in data
        assert "ptbdb" in data
