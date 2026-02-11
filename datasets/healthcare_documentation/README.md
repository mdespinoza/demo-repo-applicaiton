# Healthcare Documentation Database

## Overview

This dataset is a collection of medical transcription records spanning a variety of clinical specialties. Each record contains a patient encounter transcription along with metadata including the medical specialty, a sample name, extracted keywords, and a pre-cleaned version of the transcription text. The data is useful for healthcare NLP tasks, text analysis, and building specialty-specific documentation tools.

## Source

- **Kaggle:** [Healthcare Documentation Database](https://www.kaggle.com/datasets/harshitstark/healthcare-documentation-database)

## Files

| File | Format | Size | Records | Columns |
|------|--------|------|---------|---------|
| `Healthcare Documentation Database.csv` | CSV (comma-delimited) | 18 MB | 3,836 rows | 7 |

### Notes

- The file name contains spaces. When referencing it in code, wrap the path in quotes or escape the spaces.
- Includes a header row as the first line.
- Standard comma-delimited CSV. Fields containing commas are enclosed in double quotes.
- Some transcription text fields are lengthy (multiple paragraphs of clinical documentation).

## Column Documentation

| # | Column Name | Data Type | Description | Example |
|---|------------|-----------|-------------|---------|
| 1 | **Serial No** | Integer | Sequential row identifier, zero-indexed | `0`, `1`, `2` |
| 2 | **description** | String | Brief one-line clinical summary of the patient encounter | `A 23-year-old white female presents with complaint of allergies.` |
| 3 | **medical_specialty** | String | The clinical specialty associated with the transcription | `Allergy / Immunology`, `Bariatrics`, `Cardiovascular / Pulmonary` |
| 4 | **sample_name** | String | A descriptive title or label for the transcription record | `Allergic Rhinitis`, `Laparoscopic Gastric Bypass Consult - 2` |
| 5 | **transcription** | String (long text) | The full medical transcription text, typically structured with sections such as SUBJECTIVE, OBJECTIVE, ASSESSMENT, and PLAN. May span multiple paragraphs. | *(See data file for full examples)* |
| 6 | **keywords** | String (comma-separated) | Extracted clinical keywords relevant to the transcription | `allergy / immunology, allergic rhinitis, allergies, asthma, nasal sprays` |
| 7 | **cleaned_transcription** | String (long text) | A preprocessed version of the transcription with stop words removed, text lowercased, and punctuation stripped. Intended for NLP/text analysis use. | `23yearold white female present complaint allergy...` |

## Data Characteristics

- **Medical specialties covered:** Multiple specialties including Allergy/Immunology, Bariatrics, Cardiovascular/Pulmonary, Orthopedics, Neurology, and others.
- **Text length:** Transcription fields vary significantly in length, from brief notes to multi-page detailed encounter records.
- **Preprocessing:** The `cleaned_transcription` column provides a ready-to-use text representation for NLP pipelines (tokenization, TF-IDF, embeddings, etc.).
- **Keywords:** The `keywords` column provides manually or semi-automatically extracted terms, useful for tagging, search indexing, or faceted navigation.

## Potential Visualization Ideas

- **Specialty distribution:** Bar chart or treemap showing the number of transcriptions per medical specialty
- **Keyword cloud:** Word cloud or bubble chart generated from the `keywords` column, filterable by specialty
- **Transcription length analysis:** Histogram or box plot of transcription lengths by specialty, revealing which specialties tend to produce longer documentation
- **Keyword co-occurrence network:** Interactive graph where keywords are nodes and edges connect keywords that frequently appear in the same record
- **Searchable transcript viewer:** Full-text search interface over transcriptions with highlighted keyword matches and specialty filtering
- **Specialty similarity matrix:** Heatmap showing similarity between specialties based on shared keywords or transcription vocabulary
