# Datasets

This directory contains four curated datasets sourced from [Kaggle](https://www.kaggle.com/) that span defense logistics, biomedical signal processing, healthcare documentation, and geospatial military infrastructure. Together, they form the data foundation for a planned **web-based visualization application**.

## Datasets at a Glance

| Dataset | Directory | Records | Size | Domain |
|---------|-----------|---------|------|--------|
| Military Equipment for Local Law Enforcement | `Military_Equipment_for_Local_Law_Enforcement/` | 130,958 | ~22 MB | Defense / Law Enforcement |
| ECG Heartbeat Classification | `ecg_data/` | 123,998 | ~555 MB | Biomedical Signal Processing |
| Healthcare Documentation Database | `healthcare_documentation/` | 3,836 | ~18 MB | Medical Transcription |
| US Military Bases | `military_bases/` | 776 | ~27 MB | Geospatial / Defense Infrastructure |

## Directory Structure

```
datasets/
├── README.md
├── Military_Equipment_for_Local_Law_Enforcement/
│   ├── README.md
│   ├── dod_all_states.csv
│   └── AllStatesAndTerritoriesQTR4FY21.xlsx
├── ecg_data/
│   ├── README.md
│   ├── mitbih_train.csv
│   ├── mitbih_test.csv
│   ├── ptbdb_abnormal.csv
│   └── ptbdb_normal.csv
├── healthcare_documentation/
│   ├── README.md
│   └── Healthcare Documentation Database.csv
└── military_bases/
    ├── README.md
    └── military-bases.csv
```

## Dataset Summaries

### 1. Military Equipment for Local Law Enforcement

Records of excess Department of Defense property transferred to local law enforcement agencies under the **1033 Program** (formally the Law Enforcement Support Office program). Covers all U.S. states and territories, including item descriptions, quantities, acquisition values, and receiving agency information.

- **Source:** [Kaggle — Military Equipment for Local Law Enforcement](https://www.kaggle.com/datasets/jpmiller/military-equipment-for-local-law-enforcement)
- **Key columns:** State, Agency Name, Item Name, Quantity, Acquisition Value, Ship Date

### 2. ECG Heartbeat Classification

Pre-processed and segmented ECG signal data from the MIT-BIH Arrhythmia Dataset and the PTB Diagnostic ECG Database. Each row is a single heartbeat represented as 187 normalized signal samples plus a class label. Designed for heartbeat classification tasks.

- **Source:** [Kaggle — ECG Heartbeat Categorization Dataset](https://www.kaggle.com/datasets/shayanfazeli/heartbeat)
- **Subsets:** MIT-BIH (5-class arrhythmia), PTB (binary normal/abnormal)

### 3. Healthcare Documentation Database

A collection of medical transcription records spanning multiple clinical specialties. Each record includes the transcription text, a cleaned version, the associated medical specialty, and extracted keywords.

- **Source:** [Kaggle — Healthcare Documentation Database](https://www.kaggle.com/datasets/harshitstark/healthcare-documentation-database)
- **Key columns:** medical_specialty, transcription, keywords

### 4. US Military Bases

Geographic data on U.S. military installations, including precise boundary geometries (GeoJSON polygons), operational status, service branch component, and state/territory location.

- **Source:** [Kaggle — US Military Bases](https://www.kaggle.com/datasets/mexwell/us-military-bases)
- **Key columns:** Site Name, Geo Point, Geo Shape, COMPONENT, State Terr, Oper Stat

## Planned Visualization Application

These datasets are intended to power a deployable web-based visualization application. Potential visualization approaches include:

- **Interactive maps** of military equipment distribution by state and military base locations
- **ECG waveform viewer** with classification overlays
- **Medical specialty dashboards** with transcription search and keyword analysis
- **Cross-dataset views** linking military base locations with equipment transfer data

## Data Usage Notes

- All datasets were obtained from publicly available Kaggle sources. Refer to each dataset's Kaggle page for specific licensing and terms of use.
- Some files are large (the `ecg_data/` directory alone is over 550 MB). Consider using streaming or chunked loading strategies in the visualization application.
- The `military-bases.csv` file uses a **semicolon (`;`) delimiter** rather than the standard comma delimiter.
- The ECG CSV files contain **no header row**; columns are positional (187 signal values + 1 class label).
