# ECG Heartbeat Classification Data

## Sample Data vs Full Dataset

This repository includes **trimmed sample versions** of the ECG data for demonstration and testing purposes:

| Sample File | Rows | Classes | Size | Source |
|-------------|------|---------|------|--------|
| `mitbih_train_sample.csv` | 500 | 5 | ~1.1 MB | 100 samples/class from full training set |
| `mitbih_test_sample.csv` | 500 | 5 | ~1.2 MB | 100 samples/class from full test set |
| `ptbdb_normal_sample.csv` | 100 | 1 | ~0.3 MB | 100 samples from normal heartbeats |
| `ptbdb_abnormal_sample.csv` | 100 | 1 | ~0.2 MB | 100 samples from abnormal heartbeats |

**Total sample size:** ~2.8 MB (0.5% of original dataset)

### To use the full dataset:

1. Download the complete files from [Kaggle - ECG Heartbeat Categorization Dataset](https://www.kaggle.com/datasets/shayanfazeli/heartbeat)
2. Extract and place in `datasets/ecg_data/`:
   - `mitbih_train.csv` (392 MB, 87,554 rows)
   - `mitbih_test.csv` (98 MB, 21,892 rows)
   - `ptbdb_normal.csv` (18 MB, 4,046 rows)
   - `ptbdb_abnormal.csv` (47 MB, 10,506 rows)
3. The application will automatically use the full dataset if available, otherwise falls back to samples

### Sample Creation:

- Samples were created using stratified random sampling with `random_state=42`
- Class distributions are preserved (100 samples per class)
- All 188 columns (187 signal points + 1 label) are maintained
- Sample files use identical CSV format (no headers, comma-delimited)
- Run `python3 create_trimmed_samples.py` to regenerate samples from full dataset

## Overview

This dataset contains pre-processed and segmented electrocardiogram (ECG) signals derived from two well-known physiology databases:

1. **MIT-BIH Arrhythmia Dataset** — Multi-class arrhythmia classification (5 classes)
2. **PTB Diagnostic ECG Database** — Binary classification (normal vs. abnormal)

Each row represents a single heartbeat that has been extracted, padded/truncated to a fixed length, and normalized to the range [0.0, 1.0]. The last value in each row is the class label.

## Source

- **Kaggle:** [ECG Heartbeat Categorization Dataset](https://www.kaggle.com/datasets/shayanfazeli/heartbeat)
- **Original sources:**
  - [MIT-BIH Arrhythmia Database](https://www.physionet.org/content/mitdb/1.0.0/) (PhysioNet)
  - [PTB Diagnostic ECG Database](https://www.physionet.org/content/ptbdb/1.0.0/) (PhysioNet)

## Files

### Full Dataset (not included in repository)

| File | Size | Records | Source Database | Purpose |
|------|------|---------|-----------------|---------|
| `mitbih_train.csv` | 392 MB | 87,554 | MIT-BIH Arrhythmia | Training set |
| `mitbih_test.csv` | 98 MB | 21,892 | MIT-BIH Arrhythmia | Test set |
| `ptbdb_abnormal.csv` | 47 MB | 10,506 | PTB Diagnostic | Abnormal heartbeats |
| `ptbdb_normal.csv` | 18 MB | 4,046 | PTB Diagnostic | Normal heartbeats |

**Total:** 123,998 heartbeat records across all files, approximately 555 MB combined.

### Sample Dataset (included in repository)

| File | Size | Records | Source Database | Purpose |
|------|------|---------|-----------------|---------|
| `mitbih_train_sample.csv` | 1.1 MB | 500 | MIT-BIH Arrhythmia | Training set sample (100/class) |
| `mitbih_test_sample.csv` | 1.2 MB | 500 | MIT-BIH Arrhythmia | Test set sample (100/class) |
| `ptbdb_abnormal_sample.csv` | 0.2 MB | 100 | PTB Diagnostic | Abnormal heartbeats sample |
| `ptbdb_normal_sample.csv` | 0.3 MB | 100 | PTB Diagnostic | Normal heartbeats sample |

**Total:** 1,200 heartbeat records across all sample files, approximately 2.8 MB combined.

## Data Format

- **Delimiter:** Comma (`,`)
- **Header row:** None. All files lack column headers.
- **Columns per row:** 188
  - Columns 1–187: Normalized ECG signal amplitude values (floating-point, range 0.0 to 1.0)
  - Column 188: Class label (floating-point representation of an integer class)
- **Number format:** Scientific notation (e.g., `9.779411554336547852e-01`)

### Column Structure

| Column Index | Description |
|-------------|-------------|
| 1 – 187 | Sequential ECG amplitude values representing one heartbeat, resampled to 187 time steps and normalized to [0, 1] |
| 188 | Classification label for this heartbeat (see class definitions below) |

## Class Labels

### MIT-BIH Arrhythmia Dataset (5 classes)

| Label | Class Code | Description | Clinical Significance |
|-------|-----------|-------------|----------------------|
| 0.0 | N | Normal beat | Normal sinus rhythm |
| 1.0 | S | Supraventricular ectopic beat | Premature or ectopic beats originating above the ventricles |
| 2.0 | V | Ventricular ectopic beat | Premature or ectopic beats originating in the ventricles |
| 3.0 | F | Fusion beat | A beat resulting from simultaneous activation from two different sources |
| 4.0 | Q | Unknown / Unclassifiable beat | Beats that could not be classified into the above categories |

### PTB Diagnostic ECG Database (2 classes)

| Label | Description |
|-------|-------------|
| 0.0 | Normal heartbeat |
| 1.0 | Abnormal heartbeat (various cardiac pathologies) |

The PTB data is pre-split into separate files by class (`ptbdb_normal.csv` and `ptbdb_abnormal.csv`) rather than using a train/test split. To use both classes together, concatenate the files and create your own train/test splits.

## Data Characteristics

- **Signal preprocessing:** Each heartbeat was extracted from the raw ECG recording using R-peak detection, then resampled to exactly 187 time steps and amplitude-normalized to [0, 1].
- **Class imbalance (MIT-BIH):** The dataset is significantly imbalanced. Normal beats (class 0) dominate, while Fusion (class 3) and Unknown (class 4) beats are rare. This should be considered when designing visualizations or classifiers.
- **File sizes:** The combined size exceeds 550 MB. Loading all files simultaneously may require significant memory. Consider chunked reading or sampling for interactive visualizations.

## Potential Visualization Ideas

- **Waveform viewer:** Interactive line chart rendering individual ECG heartbeats, with navigation controls to browse through records and color-coded class labels
- **Class distribution:** Bar charts showing the distribution of heartbeat classes in each dataset, highlighting class imbalance
- **Average waveform overlay:** Compute and plot the mean ECG waveform for each class, overlaid on the same axes to show morphological differences
- **Signal amplitude heatmap:** Display a heatmap where each row is a heartbeat and columns are time steps, with color intensity representing amplitude
- **Train/test comparison:** Side-by-side distribution comparison between training and test sets for the MIT-BIH data
- **Interactive classifier demo:** Allow users to select a heartbeat, view its waveform, and see a predicted classification
