# Military Equipment for Local Law Enforcement

## Overview

This dataset documents transfers of excess Department of Defense (DoD) property to local law enforcement agencies across the United States under the **1033 Program**. Administered by the Defense Logistics Agency's Law Enforcement Support Office (LESO), the 1033 Program allows the DoD to transfer surplus military equipment to federal, state, and local law enforcement agencies.

The data covers all 50 states and U.S. territories, detailing what equipment was transferred, to which agency, in what quantity, and at what acquisition value.

## Source

- **Kaggle:** [Military Equipment for Local Law Enforcement](https://www.kaggle.com/datasets/jpmiller/military-equipment-for-local-law-enforcement)
- **Original source:** Defense Logistics Agency (DLA) / Law Enforcement Support Office (LESO)

## Files

| File | Format | Size | Records | Description |
|------|--------|------|---------|-------------|
| `dod_all_states.csv` | CSV (comma-delimited) | 15 MB | 130,958 rows | Complete transfer records for all states, 11 columns |
| `AllStatesAndTerritoriesQTR4FY21.xlsx` | Excel (.xlsx) | 6.3 MB | -- | Quarterly snapshot from Q4 FY2021 in native Excel format |

### Notes

- `dod_all_states.csv` includes a header row as the first line.
- Standard comma-delimited CSV encoding.
- Date values are in the format `YYYY-MM-DD HH:MM:SS.SSS`.
- `AllStatesAndTerritoriesQTR4FY21.xlsx` is a native Excel file representing a point-in-time snapshot (Quarter 4, Fiscal Year 2021). It may contain multiple sheets or formatting not present in the CSV.

## Column Documentation

| # | Column Name | Data Type | Description | Example |
|---|------------|-----------|-------------|---------|
| 1 | **State** | String (2-letter abbreviation) | U.S. state or territory where the receiving agency is located | `AL`, `CA`, `TX` |
| 2 | **Agency Name** | String | Name of the law enforcement agency receiving the equipment | `ABBEVILLE POLICE DEPT` |
| 3 | **NSN** | String | National Stock Number — a 13-digit NATO-standardized identifier in the format `NNNN-NN-NNN-NNNN` | `2540-01-565-4700` |
| 4 | **Item Name** | String | Description of the transferred equipment item | `BALLISTIC BLANKET KIT`, `MINE RESISTANT VEHICLE` |
| 5 | **Quantity** | Integer | Number of units transferred in this record | `10`, `1` |
| 6 | **UI** | String | Unit of Issue — the unit of measurement for the quantity | `Kit`, `Each` |
| 7 | **Acquisition Value** | Float (USD) | Original acquisition cost of the item(s) to the DoD | `15871.59`, `658000.0` |
| 8 | **DEMIL Code** | String (single character) | Demilitarization code indicating the level of demilitarization required. Common values: `A` (no demil required), `B` (demil required), `C` (key-point removal), `D` (total destruction), `Q` (provisional) | `D` |
| 9 | **DEMIL IC** | Float / Blank | Demilitarization Integrity Code — provides additional specificity to the DEMIL Code. May be blank. | `1.0`, `3.0` |
| 10 | **Ship Date** | Datetime string | Date the equipment was shipped to the receiving agency, in `YYYY-MM-DD HH:MM:SS.SSS` format | `2018-01-30 00:00:00.000` |
| 11 | **Station Type** | String | Classification of the receiving agency's station type | `State` |

## Data Characteristics

- **Geographic scope:** All 50 U.S. states and territories
- **Temporal range:** Multiple years (check `Ship Date` for exact range)
- **Total records:** 130,958 equipment transfer line items
- **Key identifiers:** NSN provides a standardized lookup for equipment types across records

## Potential Visualization Ideas

- **Choropleth map:** Total acquisition value of equipment transferred per state, with drill-down to agency level
- **Top-N bar charts:** Most common item types transferred, agencies receiving the most equipment, or highest total value by state
- **Time series:** Volume and value of transfers over time, filterable by state or equipment category
- **Equipment category breakdown:** Group items by NSN prefix (Federal Supply Class) and show distribution as treemaps or sunburst charts
- **Agency search:** Searchable table allowing lookup of specific agencies and their equipment inventories
- **DEMIL code analysis:** Distribution of demilitarization requirements across transferred items
