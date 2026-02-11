# US Military Bases

## Overview

This dataset contains geographic and administrative information on U.S. military installations across the United States and its territories. Each record includes the installation's name, service branch component, operational status, state/territory, and precise boundary geometry in GeoJSON format. The data is well-suited for geospatial analysis and map-based visualizations.

## Source

- **Kaggle:** [US Military Bases](https://www.kaggle.com/datasets/mexwell/us-military-bases)

## Files

| File | Format | Size | Records | Columns |
|------|--------|------|---------|---------|
| `military-bases.csv` | CSV (**semicolon-delimited**) | 27 MB | 776 rows | 14 |

### Important Format Notes

- **Delimiter:** This file uses a **semicolon (`;`)** as the field separator, not a comma. When loading with pandas, use:
  ```python
  pd.read_csv('military-bases.csv', sep=';')
  ```
- Includes a header row as the first line.
- The `Geo Shape` column contains embedded JSON (GeoJSON geometry objects) with internal commas and double quotes. The semicolon delimiter avoids conflicts with these embedded commas.
- The large file size (27 MB for only 776 rows) is primarily due to the detailed GeoJSON polygon coordinate data in the `Geo Shape` column.

## Column Documentation

| # | Column Name | Data Type | Description | Example |
|---|------------|-----------|-------------|---------|
| 1 | **Geo Point** | String (lat, lon) | Centroid coordinates of the installation as `latitude, longitude` | `31.2309993833, -85.6506347178` |
| 2 | **Geo Shape** | String (GeoJSON) | Boundary geometry as a GeoJSON object. Typically a `Polygon` type with coordinate arrays defining the perimeter. | `{"coordinates": [[[-85.65, 31.23],...]], "type": "Polygon"}` |
| 3 | **OBJECTID_1** | Integer | Primary object identifier | `26` |
| 4 | **OBJECTID** | Integer | Secondary object identifier from the original data source | `65` |
| 5 | **COMPONENT** | String | Military service branch and component type | `Army Active`, `Air Force Reserve`, `Navy Active` |
| 6 | **Site Name** | String | Official name of the military installation | `Allen Stagefield AL`, `Fort Bragg` |
| 7 | **Joint Base** | String | If part of a joint base, the joint base name; otherwise `N/A` | `N/A`, `JB Andrews` |
| 8 | **State Terr** | String | Full name of the U.S. state or territory | `Alabama`, `California`, `Guam` |
| 9 | **COUNTRY** | String | Country where the installation is located | `United States` |
| 10 | **Oper Stat** | String | Operational status of the installation | `Active`, `Closed`, `Realigned` |
| 11 | **PERIMETER** | Float | Perimeter measurement of the installation boundary (units depend on source projection) | `1.64138338` |
| 12 | **AREA** | Float | Area measurement of the installation (units depend on source projection) | `0.17657484` |
| 13 | **Shape_Leng** | Float | Length of the boundary shape in projected coordinate units | `3170.633` |
| 14 | **Shape_Area** | Float | Area of the boundary shape in projected coordinate units | `627423.995` |

## Data Characteristics

- **Geographic scope:** Primarily U.S. domestic installations; the `COUNTRY` field is `United States` for all records.
- **Service branches:** Includes Army, Navy, Air Force, Marine Corps, and their Active, Reserve, and Guard components.
- **Operational statuses:** Mix of Active, Closed, and Realigned installations.
- **GeoJSON detail:** The `Geo Shape` column contains detailed polygon boundaries, not just point locations. This enables rendering of actual installation footprints on maps.
- **Joint bases:** Some installations are part of joint bases (multi-service shared installations), indicated in the `Joint Base` column.

## Potential Visualization Ideas

- **Interactive map:** Render installation boundaries as polygons on a Leaflet or Mapbox map, with popups showing site name, component, and operational status. Use `Geo Shape` for boundary polygons and `Geo Point` for marker placement.
- **Choropleth by state:** Color-code states by the number of military installations or total installation area.
- **Component/branch filter:** Toggle map layers by service branch (Army, Navy, Air Force, Marine Corps) and component (Active, Reserve, Guard).
- **Operational status view:** Color-code installations by operational status (Active, Closed, Realigned).
- **Joint base highlighting:** Visually group and highlight installations that belong to the same joint base.
- **Area/perimeter analysis:** Scatter plot or ranked bar chart of installations by area, filterable by state or branch.
- **Cross-dataset linkage:** Overlay military base locations with the equipment transfer data from the `Military_Equipment_for_Local_Law_Enforcement` dataset to explore geographic proximity between bases and law enforcement agencies receiving equipment.
