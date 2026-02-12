"""Centralized data loading with caching."""

import json
import os
import sys
import csv
import pandas as pd
import numpy as np
from app.config import (
    EQUIPMENT_CSV,
    ECG_DIR,
    BASES_CSV,
    HEALTHCARE_CSV,
    CACHE_DIR,
    ECG_CACHE,
    get_equipment_category,
)
from app.logging_config import get_logger

logger = get_logger(__name__)

# Increase CSV field size limit for GeoJSON polygons
csv.field_size_limit(sys.maxsize)

_cache = {}

# Empty fallback structures for error paths
_EMPTY_ECG = {
    "mitbih": {"class_names": {}, "splits": {}},
    "ptbdb": {"class_names": {}, "splits": {}},
}


def validate_dataframe(df, required_columns, name="DataFrame"):
    """Validate a DataFrame has expected columns.

    Args:
        df: The DataFrame to validate.
        required_columns: List of column names that must be present.
        name: Human-readable name for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If df is not a DataFrame or missing required columns.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"{name}: Expected DataFrame, got {type(df).__name__}")
    if df.empty:
        logger.warning("%s is empty after loading", name)
        return True
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"{name}: Missing required columns: {missing}")
    return True


def load_equipment():
    """Load and preprocess military equipment data.

    Returns:
        pd.DataFrame: Processed equipment data, or empty DataFrame on error.
    """
    if "equipment" in _cache:
        return _cache["equipment"]

    try:
        logger.info("Loading equipment data from %s", EQUIPMENT_CSV)
        df = pd.read_csv(EQUIPMENT_CSV, low_memory=False)

        validate_dataframe(
            df,
            [
                "State",
                "Agency Name",
                "NSN",
                "Item Name",
                "Quantity",
                "Acquisition Value",
                "Ship Date",
                "DEMIL Code",
                "Station Type",
            ],
            name="Equipment",
        )

        df["Agency Name"] = df["Agency Name"].str.strip()
        df["Acquisition Value"] = pd.to_numeric(df["Acquisition Value"], errors="coerce").fillna(0)
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0).astype(int)
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
        df["Year"] = df["Ship Date"].dt.year
        df["Category"] = df["NSN"].apply(get_equipment_category)
        df["DEMIL Code"] = df["DEMIL Code"].fillna("Unknown").astype(str).str.strip()
        df["Station Type"] = df["Station Type"].fillna("Unknown").astype(str).str.strip()

        logger.info("Equipment data loaded: %d rows", len(df))
        _cache["equipment"] = df
        return df

    except FileNotFoundError:
        logger.error("Equipment CSV not found: %s", EQUIPMENT_CSV)
    except pd.errors.ParserError as e:
        logger.error("Failed to parse equipment CSV: %s", e)
    except ValueError as e:
        logger.error("Equipment data validation failed: %s", e)
    except Exception:
        logger.exception("Unexpected error loading equipment data")

    empty = pd.DataFrame(
        columns=[
            "State",
            "Agency Name",
            "NSN",
            "Item Name",
            "Quantity",
            "Acquisition Value",
            "DEMIL Code",
            "Ship Date",
            "Year",
            "Category",
            "Station Type",
            "UI",
        ]
    )
    _cache["equipment"] = empty
    return empty


def load_bases():
    """Load and preprocess military bases data.

    Returns:
        pd.DataFrame: Processed bases data, or empty DataFrame on error.
    """
    if "bases" in _cache:
        return _cache["bases"]

    try:
        logger.info("Loading bases data from %s", BASES_CSV)
        df = pd.read_csv(BASES_CSV, sep=";", encoding="utf-8-sig", engine="python")

        validate_dataframe(
            df,
            ["Geo Point", "COMPONENT", "Site Name", "State Terr", "Oper Stat", "Joint Base", "AREA", "PERIMETER"],
            name="Bases",
        )

        # Parse Geo Point to lat/lon
        def parse_geo_point(gp):
            if pd.isna(gp) or not isinstance(gp, str):
                return pd.Series({"lat": None, "lon": None})
            parts = gp.split(",")
            if len(parts) == 2:
                try:
                    return pd.Series({"lat": float(parts[0].strip()), "lon": float(parts[1].strip())})
                except ValueError:
                    return pd.Series({"lat": None, "lon": None})
            return pd.Series({"lat": None, "lon": None})

        coords = df["Geo Point"].apply(parse_geo_point)
        df["lat"] = coords["lat"]
        df["lon"] = coords["lon"]
        df = df.dropna(subset=["lat", "lon"]).copy()

        # Normalize component names
        df["COMPONENT"] = df["COMPONENT"].str.strip()
        df["Oper Stat"] = df["Oper Stat"].fillna("Unknown").str.strip()
        df["Joint Base"] = df["Joint Base"].fillna("Not Joint").str.strip()
        df["State Terr"] = df["State Terr"].fillna("Unknown").str.strip()
        df["Site Name"] = df["Site Name"].fillna("Unknown").str.strip()
        # Clean numeric columns for AREA and PERIMETER
        df["AREA"] = pd.to_numeric(df["AREA"], errors="coerce").fillna(0)
        df["PERIMETER"] = pd.to_numeric(df["PERIMETER"], errors="coerce").fillna(0)

        logger.info("Bases data loaded: %d rows", len(df))
        _cache["bases"] = df
        return df

    except FileNotFoundError:
        logger.error("Bases CSV not found: %s", BASES_CSV)
    except pd.errors.ParserError as e:
        logger.error("Failed to parse bases CSV: %s", e)
    except ValueError as e:
        logger.error("Bases data validation failed: %s", e)
    except Exception:
        logger.exception("Unexpected error loading bases data")

    empty = pd.DataFrame(
        columns=[
            "COMPONENT",
            "Site Name",
            "State Terr",
            "Oper Stat",
            "Joint Base",
            "lat",
            "lon",
            "AREA",
            "PERIMETER",
        ]
    )
    _cache["bases"] = empty
    return empty


def load_healthcare():
    """Load and preprocess healthcare documentation data.

    Returns:
        pd.DataFrame: Processed healthcare data, or empty DataFrame on error.
    """
    if "healthcare" in _cache:
        return _cache["healthcare"]

    try:
        logger.info("Loading healthcare data from %s", HEALTHCARE_CSV)
        df = pd.read_csv(HEALTHCARE_CSV, low_memory=False)

        validate_dataframe(
            df,
            ["medical_specialty", "cleaned_transcription", "keywords"],
            name="Healthcare",
        )

        df["medical_specialty"] = df["medical_specialty"].str.strip()
        df["transcription_length"] = df["cleaned_transcription"].fillna("").str.len()
        # Clean keywords
        df["keywords"] = df["keywords"].fillna("").str.strip().str.rstrip(",")

        logger.info("Healthcare data loaded: %d rows", len(df))
        _cache["healthcare"] = df
        return df

    except FileNotFoundError:
        logger.error("Healthcare CSV not found: %s", HEALTHCARE_CSV)
    except pd.errors.ParserError as e:
        logger.error("Failed to parse healthcare CSV: %s", e)
    except ValueError as e:
        logger.error("Healthcare data validation failed: %s", e)
    except Exception:
        logger.exception("Unexpected error loading healthcare data")

    empty = pd.DataFrame(
        columns=[
            "Serial No",
            "description",
            "medical_specialty",
            "sample_name",
            "keywords",
            "cleaned_transcription",
            "transcription_length",
        ]
    )
    _cache["healthcare"] = empty
    return empty


def load_ecg_precomputed():
    """Load precomputed ECG data from cache.

    Returns:
        dict: Precomputed ECG statistics, or empty structure on error.
    """
    if "ecg" in _cache:
        return _cache["ecg"]

    try:
        if not os.path.exists(ECG_CACHE):
            logger.info("ECG cache not found, running precomputation...")
            result = _precompute_ecg()
            if result is None:
                logger.error("ECG precomputation failed")
                _cache["ecg"] = _EMPTY_ECG
                return _EMPTY_ECG

        with open(ECG_CACHE, "r") as f:
            data = json.load(f)
        _cache["ecg"] = data
        return data

    except FileNotFoundError:
        logger.error("ECG cache file not found: %s", ECG_CACHE)
    except json.JSONDecodeError as e:
        logger.error("Corrupted ECG cache JSON: %s", e)
    except KeyError as e:
        logger.error("Missing key in ECG cache: %s", e)
    except Exception:
        logger.exception("Unexpected error loading ECG data")

    _cache["ecg"] = _EMPTY_ECG
    return _EMPTY_ECG


def _precompute_ecg():
    """Precompute ECG statistics and samples.

    Returns:
        dict: Computed ECG data, or None on failure.
    """
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        result = {}

        for dataset_name, files, class_map in [
            (
                "mitbih",
                ["mitbih_train.csv", "mitbih_test.csv"],
                {0: "Normal (N)", 1: "Supraventricular (S)", 2: "Ventricular (V)", 3: "Fusion (F)", 4: "Unknown (Q)"},
            ),
            ("ptbdb", ["ptbdb_normal.csv", "ptbdb_abnormal.csv"], {0: "Normal", 1: "Abnormal"}),
        ]:
            dfs = {}
            for fname in files:
                fpath = os.path.join(ECG_DIR, fname)

                # Try full dataset first, fall back to sample if not available
                if not os.path.exists(fpath):
                    # Try sample version
                    sample_fname = fname.replace(".csv", "_sample.csv")
                    fpath = os.path.join(ECG_DIR, sample_fname)
                    if os.path.exists(fpath):
                        logger.info("Using sample data: %s (full dataset not found)", sample_fname)

                if os.path.exists(fpath):
                    df = pd.read_csv(fpath, header=None)
                    split_key = "train" if "train" in fname or "normal" in fname else "test"
                    if "abnormal" in fname:
                        split_key = "test"
                    if "normal" in fname and "abnormal" not in fname:
                        split_key = "train"
                    if "train" in fname:
                        split_key = "train"
                    if "test" in fname:
                        split_key = "test"
                    dfs[split_key] = df

            ds_result = {"class_names": class_map, "splits": {}}

            for split_name, df in dfs.items():
                labels = df.iloc[:, -1].values
                labels = np.round(labels).astype(int)
                signals = df.iloc[:, :-1].values

                split_data = {
                    "class_distribution": {},
                    "mean_waveforms": {},
                    "std_waveforms": {},
                    "samples": {},
                    "features": {},
                }

                for class_id in sorted(set(labels)):
                    class_name = class_map.get(class_id, f"Class {class_id}")
                    mask = labels == class_id
                    class_signals = signals[mask]

                    split_data["class_distribution"][class_name] = int(mask.sum())

                    mean_wf = np.mean(class_signals, axis=0).tolist()
                    std_wf = np.std(class_signals, axis=0).tolist()
                    split_data["mean_waveforms"][class_name] = mean_wf
                    split_data["std_waveforms"][class_name] = std_wf

                    # Sample 50 waveforms per class
                    n_samples = min(50, len(class_signals))
                    idx = np.random.RandomState(42).choice(len(class_signals), n_samples, replace=False)
                    split_data["samples"][class_name] = class_signals[idx].tolist()

                    # Signal features
                    split_data["features"][class_name] = {
                        "peak_amplitude": float(np.mean(np.max(class_signals, axis=1))),
                        "energy": float(np.mean(np.sum(class_signals**2, axis=1))),
                        "zero_crossings": float(
                            np.mean(np.sum(np.diff(np.sign(class_signals - 0.5), axis=1) != 0, axis=1))
                        ),
                    }

                ds_result["splits"][split_name] = split_data

            # For PTB, combine normal and abnormal into train/test splits
            if dataset_name == "ptbdb":
                normal_path = os.path.join(ECG_DIR, "ptbdb_normal.csv")
                abnormal_path = os.path.join(ECG_DIR, "ptbdb_abnormal.csv")

                # Try full dataset first, fall back to sample if not available
                if not os.path.exists(normal_path):
                    normal_path = os.path.join(ECG_DIR, "ptbdb_normal_sample.csv")
                if not os.path.exists(abnormal_path):
                    abnormal_path = os.path.join(ECG_DIR, "ptbdb_abnormal_sample.csv")

                if os.path.exists(normal_path) and os.path.exists(abnormal_path):
                    df_normal = pd.read_csv(normal_path, header=None)
                    df_abnormal = pd.read_csv(abnormal_path, header=None)

                    # Label: normal=0, abnormal=1
                    df_normal.iloc[:, -1] = 0
                    df_abnormal.iloc[:, -1] = 1
                    df_all = pd.concat([df_normal, df_abnormal], ignore_index=True)

                    labels = df_all.iloc[:, -1].values.astype(int)
                    signals = df_all.iloc[:, :-1].values

                    # 80/20 split
                    rng = np.random.RandomState(42)
                    idx = rng.permutation(len(labels))
                    split_point = int(0.8 * len(idx))
                    train_idx, test_idx = idx[:split_point], idx[split_point:]

                    for split_name, sidx in [("train", train_idx), ("test", test_idx)]:
                        split_labels = labels[sidx]
                        split_signals = signals[sidx]
                        split_data = {
                            "class_distribution": {},
                            "mean_waveforms": {},
                            "std_waveforms": {},
                            "samples": {},
                            "features": {},
                        }
                        for class_id in sorted(set(split_labels)):
                            class_name = class_map.get(class_id, f"Class {class_id}")
                            mask = split_labels == class_id
                            class_signals = split_signals[mask]
                            split_data["class_distribution"][class_name] = int(mask.sum())
                            split_data["mean_waveforms"][class_name] = np.mean(class_signals, axis=0).tolist()
                            split_data["std_waveforms"][class_name] = np.std(class_signals, axis=0).tolist()
                            n_samples = min(50, len(class_signals))
                            sample_idx = rng.choice(len(class_signals), n_samples, replace=False)
                            split_data["samples"][class_name] = class_signals[sample_idx].tolist()
                            split_data["features"][class_name] = {
                                "peak_amplitude": float(np.mean(np.max(class_signals, axis=1))),
                                "energy": float(np.mean(np.sum(class_signals**2, axis=1))),
                                "zero_crossings": float(
                                    np.mean(np.sum(np.diff(np.sign(class_signals - 0.5), axis=1) != 0, axis=1))
                                ),
                            }
                        ds_result["splits"][split_name] = split_data

            # Compute correlation matrix between mean waveforms (using train split)
            if "train" in ds_result["splits"]:
                means = ds_result["splits"]["train"]["mean_waveforms"]
                class_names = list(means.keys())
                mean_arr = np.array([means[c] for c in class_names])
                corr = np.corrcoef(mean_arr).tolist()
                ds_result["correlation_matrix"] = {"classes": class_names, "matrix": corr}

            # PCA 2D embedding on sampled waveforms (train split)
            if "train" in ds_result["splits"]:
                samples = ds_result["splits"]["train"]["samples"]
                pca_signals = []
                pca_labels = []
                for class_name, class_samples in samples.items():
                    for s in class_samples:
                        pca_signals.append(s)
                        pca_labels.append(class_name)
                if len(pca_signals) > 2:
                    from sklearn.decomposition import PCA

                    pca_arr = np.array(pca_signals)
                    pca = PCA(n_components=2, random_state=42)
                    embedding = pca.fit_transform(pca_arr)
                    ds_result["pca_embedding"] = {
                        "x": embedding[:, 0].tolist(),
                        "y": embedding[:, 1].tolist(),
                        "labels": pca_labels,
                        "explained_variance": pca.explained_variance_ratio_.tolist(),
                    }

            result[dataset_name] = ds_result

        with open(ECG_CACHE, "w") as f:
            json.dump(result, f)

        return result

    except Exception:
        logger.exception("Failed to precompute ECG data")
        return None
