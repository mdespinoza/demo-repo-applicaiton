"""Shared test fixtures for the Dash data visualization dashboard."""

import pytest
import pandas as pd
import numpy as np

# ── Cache Isolation ──────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_loader_cache():
    """Clear the in-memory loader cache before AND after every test.

    Prevents test pollution — one test's cached data leaking into another.
    """
    from app.data import loader

    loader._cache.clear()
    yield
    loader._cache.clear()


# ── Mock DataFrames ──────────────────────────────────────────────────


@pytest.fixture
def mock_equipment_df():
    """Minimal equipment DataFrame mimicking load_equipment() output."""
    return pd.DataFrame(
        {
            "State": ["CA", "CA", "TX", "TX", "NY"],
            "Agency Name": ["LAPD", "LAPD", "HPD", "DPD", "NYPD"],
            "NSN": [
                "1005-01-001-0001",
                "2320-01-002-0002",
                "1005-01-003-0003",
                "5820-01-004-0004",
                "1005-01-005-0005",
            ],
            "Item Name": ["RIFLE", "TRUCK", "RIFLE", "RADIO", "RIFLE"],
            "Quantity": [10, 2, 5, 20, 15],
            "UI": ["Each", "Each", "Each", "Each", "Each"],
            "Acquisition Value": [5000.0, 50000.0, 2500.0, 10000.0, 7500.0],
            "DEMIL Code": ["D", "A", "D", "A", "D"],
            "Ship Date": pd.to_datetime(["2020-01-15", "2020-06-01", "2019-03-10", "2021-07-20", "2020-11-05"]),
            "Year": [2020.0, 2020.0, 2019.0, 2021.0, 2020.0],
            "Category": [
                "Weapons & Firearms",
                "Vehicles & Transport",
                "Weapons & Firearms",
                "Communications & Electronics",
                "Weapons & Firearms",
            ],
            "Station Type": ["State", "State", "State", "State", "State"],
        }
    )


@pytest.fixture
def mock_bases_df():
    """Minimal bases DataFrame mimicking load_bases() output."""
    return pd.DataFrame(
        {
            "COMPONENT": [
                "Army Active",
                "Air Force Active",
                "Navy Active",
                "Army Active",
                "Air Force Active",
            ],
            "Site Name": [
                "Fort Hood",
                "Edwards AFB",
                "Naval Station Norfolk",
                "Fort Bragg",
                "Nellis AFB",
            ],
            "State Terr": ["Texas", "California", "Virginia", "North Carolina", "Nevada"],
            "Oper Stat": ["Active", "Active", "Active", "Active", "Active"],
            "Joint Base": ["N/A", "N/A", "N/A", "N/A", "N/A"],
            "lat": [31.13, 34.91, 36.95, 35.14, 36.24],
            "lon": [-97.78, -117.88, -76.29, -79.00, -115.03],
            "AREA": [880.0, 470.0, 34.0, 640.0, 560.0],
            "PERIMETER": [120.0, 90.0, 25.0, 100.0, 95.0],
        }
    )


@pytest.fixture
def mock_healthcare_df():
    """Minimal healthcare DataFrame mimicking load_healthcare() output."""
    return pd.DataFrame(
        {
            "Serial No": [0, 1, 2, 3, 4],
            "description": [
                "Patient with allergies",
                "Knee replacement surgery",
                "Annual physical exam",
                "Cardiac catheterization",
                "Skin biopsy results",
            ],
            "medical_specialty": [
                "Allergy / Immunology",
                "Orthopedic",
                "General Medicine",
                "Cardiovascular / Pulmonary",
                "Dermatology",
            ],
            "sample_name": ["Sample A", "Sample B", "Sample C", "Sample D", "Sample E"],
            "transcription": [
                "Full transcription text A " * 20,
                "Full transcription text B " * 30,
                "Full transcription text C " * 10,
                "Full transcription text D " * 25,
                "Full transcription text E " * 15,
            ],
            "keywords": [
                "allergy, rhinitis, nasal, sprays",
                "orthopedic, knee, replacement, surgery, joint",
                "general medicine, physical, exam, routine",
                "cardiovascular, catheterization, cardiac, stent",
                "dermatology, biopsy, skin, lesion",
            ],
            "cleaned_transcription": [
                "cleaned text A " * 20,
                "cleaned text B " * 30,
                "cleaned text C " * 10,
                "cleaned text D " * 25,
                "cleaned text E " * 15,
            ],
            "transcription_length": [300, 450, 150, 375, 225],
        }
    )


@pytest.fixture
def mock_ecg_precomputed():
    """Minimal ECG precomputed data mimicking load_ecg_precomputed() output."""
    rng = np.random.RandomState(42)
    n_points = 187  # matches real ECG signal length

    def make_split(class_map, n_samples=5):
        split = {
            "class_distribution": {},
            "mean_waveforms": {},
            "std_waveforms": {},
            "samples": {},
            "features": {},
        }
        for class_name in class_map.values():
            split["class_distribution"][class_name] = n_samples * 10
            split["mean_waveforms"][class_name] = rng.rand(n_points).tolist()
            split["std_waveforms"][class_name] = (rng.rand(n_points) * 0.1).tolist()
            split["samples"][class_name] = rng.rand(n_samples, n_points).tolist()
            split["features"][class_name] = {
                "peak_amplitude": float(rng.rand()),
                "energy": float(rng.rand() * 100),
                "zero_crossings": float(rng.randint(10, 50)),
            }
        return split

    mitbih_classes = {
        0: "Normal (N)",
        1: "Supraventricular (S)",
        2: "Ventricular (V)",
        3: "Fusion (F)",
        4: "Unknown (Q)",
    }
    ptbdb_classes = {0: "Normal", 1: "Abnormal"}

    mitbih_train = make_split(mitbih_classes)
    mitbih_test = make_split(mitbih_classes)
    ptbdb_train = make_split(ptbdb_classes)
    ptbdb_test = make_split(ptbdb_classes)

    n_mitbih = len(mitbih_classes)
    n_ptbdb = len(ptbdb_classes)

    return {
        "mitbih": {
            "class_names": mitbih_classes,
            "splits": {"train": mitbih_train, "test": mitbih_test},
            "correlation_matrix": {
                "classes": list(mitbih_classes.values()),
                "matrix": np.eye(n_mitbih).tolist(),
            },
            "pca_embedding": {
                "x": rng.rand(n_mitbih * 5).tolist(),
                "y": rng.rand(n_mitbih * 5).tolist(),
                "labels": [name for name in mitbih_classes.values() for _ in range(5)],
                "explained_variance": [0.65, 0.20],
            },
        },
        "ptbdb": {
            "class_names": ptbdb_classes,
            "splits": {"train": ptbdb_train, "test": ptbdb_test},
            "correlation_matrix": {
                "classes": list(ptbdb_classes.values()),
                "matrix": np.eye(n_ptbdb).tolist(),
            },
            "pca_embedding": {
                "x": rng.rand(n_ptbdb * 5).tolist(),
                "y": rng.rand(n_ptbdb * 5).tolist(),
                "labels": [name for name in ptbdb_classes.values() for _ in range(5)],
                "explained_variance": [0.70, 0.15],
            },
        },
    }


# ── Dash App Fixture ────────────────────────────────────────────────


@pytest.fixture
def dash_app():
    """Provide the Dash app instance for callback testing.

    Returns the app object so tests can invoke registered callbacks.
    Note: This does NOT start a server.
    """
    from app.main import app

    return app
