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
    EQUIPMENT_CACHE,
    BASES_CACHE,
    HEALTHCARE_CACHE,
)
from app.logging_config import get_logger

logger = get_logger(__name__)

# Increase CSV field size limit for GeoJSON polygons
csv.field_size_limit(sys.maxsize)

_cache = {}


def _cache_is_fresh(cache_path, source_path):
    """Check if a cache file exists and is newer than its source CSV."""
    if not os.path.exists(cache_path):
        return False
    if not os.path.exists(source_path):
        return False
    return os.path.getmtime(cache_path) >= os.path.getmtime(source_path)


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

    # Try persistent Parquet cache first
    if _cache_is_fresh(EQUIPMENT_CACHE, EQUIPMENT_CSV):
        try:
            logger.info("Loading equipment from Parquet cache: %s", EQUIPMENT_CACHE)
            df = pd.read_parquet(EQUIPMENT_CACHE)
            _cache["equipment"] = df
            return df
        except Exception:
            logger.warning("Failed to read equipment cache, falling back to CSV")

    try:
        logger.info("Loading equipment data from %s", EQUIPMENT_CSV)
        df = pd.read_csv(
            EQUIPMENT_CSV,
            low_memory=False,
            dtype={
                "State": "category",
                "Agency Name": str,
                "NSN": str,
                "Item Name": str,
                "DEMIL Code": str,
                "Station Type": str,
            },
        )

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
        # Vectorized category mapping using NSN prefix lookup
        nsn_prefix = df["NSN"].str[:2].fillna("")
        category_map = {
            "10": "Weapons & Firearms",
            "11": "Weapons & Firearms",
            "12": "Weapons & Firearms",
            "13": "Ammunition & Explosives",
            "14": "Weapons & Firearms",
            "15": "Aircraft & Parts",
            "16": "Aircraft & Parts",
            "17": "Aircraft & Parts",
            "19": "Ships & Marine",
            "20": "Ships & Marine",
            "22": "Vehicles & Transport",
            "23": "Vehicles & Transport",
            "24": "Vehicles & Transport",
            "25": "Vehicles & Transport",
            "26": "Vehicles & Transport",
            "28": "Engines & Power",
            "29": "Engines & Power",
            "34": "Industrial Equipment",
            "35": "Industrial Equipment",
            "36": "Industrial Equipment",
            "37": "Industrial Equipment",
            "38": "Construction Equipment",
            "39": "Construction Equipment",
            "42": "Safety & Fire Equipment",
            "49": "Maintenance Equipment",
            "51": "Tools",
            "52": "Tools",
            "53": "Tools",
            "58": "Communications & Electronics",
            "59": "Communications & Electronics",
            "60": "Communications & Electronics",
            "61": "Communications & Electronics",
            "65": "Medical Equipment",
            "66": "Scientific Equipment",
            "67": "Imaging Equipment",
            "68": "Chemicals",
            "69": "Training & Simulation",
            "70": "IT & Computing",
            "71": "Furniture & Supplies",
            "72": "Furniture & Supplies",
            "73": "Furniture & Supplies",
            "74": "Office Equipment",
            "75": "Office Equipment",
            "84": "Clothing & Textiles",
            "83": "Clothing & Textiles",
            "85": "Personal Gear",
        }
        df["Category"] = nsn_prefix.map(category_map).fillna("Other").astype("category")
        df["DEMIL Code"] = df["DEMIL Code"].fillna("Unknown").str.strip()
        df["Station Type"] = df["Station Type"].fillna("Unknown").str.strip()

        logger.info("Equipment data loaded: %d rows", len(df))
        _cache["equipment"] = df
        # Persist to Parquet cache
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            df.to_parquet(EQUIPMENT_CACHE, index=False)
            logger.info("Equipment cache written: %s", EQUIPMENT_CACHE)
        except Exception:
            logger.warning("Failed to write equipment cache")
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

    # Try persistent Parquet cache first
    if _cache_is_fresh(BASES_CACHE, BASES_CSV):
        try:
            logger.info("Loading bases from Parquet cache: %s", BASES_CACHE)
            df = pd.read_parquet(BASES_CACHE)
            _cache["bases"] = df
            return df
        except Exception:
            logger.warning("Failed to read bases cache, falling back to CSV")

    try:
        logger.info("Loading bases data from %s", BASES_CSV)
        df = pd.read_csv(
            BASES_CSV,
            sep=";",
            encoding="utf-8-sig",
            engine="python",
            dtype={
                "COMPONENT": str,
                "Site Name": str,
                "State Terr": str,
                "Oper Stat": str,
                "Joint Base": str,
            },
        )

        validate_dataframe(
            df,
            ["Geo Point", "COMPONENT", "Site Name", "State Terr", "Oper Stat", "Joint Base", "AREA", "PERIMETER"],
            name="Bases",
        )

        # Vectorized Geo Point parsing (replaces row-wise .apply())
        geo = df["Geo Point"].dropna().str.split(",", expand=True)
        if len(geo.columns) >= 2:
            df["lat"] = pd.to_numeric(geo[0].str.strip(), errors="coerce")
            df["lon"] = pd.to_numeric(geo[1].str.strip(), errors="coerce")
        else:
            df["lat"] = np.nan
            df["lon"] = np.nan
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
        # Persist to Parquet cache
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            df.to_parquet(BASES_CACHE, index=False)
            logger.info("Bases cache written: %s", BASES_CACHE)
        except Exception:
            logger.warning("Failed to write bases cache")
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

    # Try persistent Parquet cache first
    if _cache_is_fresh(HEALTHCARE_CACHE, HEALTHCARE_CSV):
        try:
            logger.info("Loading healthcare from Parquet cache: %s", HEALTHCARE_CACHE)
            df = pd.read_parquet(HEALTHCARE_CACHE)
            _cache["healthcare"] = df
            return df
        except Exception:
            logger.warning("Failed to read healthcare cache, falling back to CSV")

    try:
        logger.info("Loading healthcare data from %s", HEALTHCARE_CSV)
        df = pd.read_csv(
            HEALTHCARE_CSV,
            low_memory=False,
            dtype={
                "medical_specialty": "category",
                "sample_name": str,
                "description": str,
                "keywords": str,
                "cleaned_transcription": str,
            },
        )

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
        # Persist to Parquet cache
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            df.to_parquet(HEALTHCARE_CACHE, index=False)
            logger.info("Healthcare cache written: %s", HEALTHCARE_CACHE)
        except Exception:
            logger.warning("Failed to write healthcare cache")
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
