"""Application configuration: paths, constants, color palette."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "datasets")
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")

# Dataset paths
EQUIPMENT_CSV = os.path.join(DATASET_DIR, "Military_Equipment_for_Local_Law_Enforcement", "dod_all_states.csv")
ECG_DIR = os.path.join(DATASET_DIR, "ecg_data")
BASES_CSV = os.path.join(DATASET_DIR, "military_bases", "military-bases.csv")
HEALTHCARE_CSV = os.path.join(DATASET_DIR, "healthcare_documentation", "Healthcare Documentation Database.csv")

# Cache paths
ECG_CACHE = os.path.join(CACHE_DIR, "ecg_precomputed.json")

# Color palette — modern dark theme
COLORS = {
    "primary": "#0B0F19",  # Deep navy base
    "secondary": "#38BDF8",  # Electric blue accent
    "success": "#34D399",  # Emerald green
    "warning": "#FBBF24",  # Amber
    "danger": "#FB7185",  # Rose
    "info": "#22D3EE",  # Cyan
    "light": "#E2E8F0",  # Light slate text
    "dark": "#0B0F19",  # Deep navy
    "background": "#0B0F19",  # Base background
    "card_bg": "#151D2E",  # Card surface
    "accent": "#818CF8",  # Indigo accent
    "muted": "#64748B",  # Muted slate
    "border": "rgba(99, 125, 175, 0.12)",
}

# Military branch colors (bright for dark backgrounds)
BRANCH_COLORS = {
    "Army": "#34D399",
    "Navy": "#38BDF8",
    "Air Force": "#818CF8",
    "Marine Corps": "#FB7185",
    "Joint": "#FBBF24",
    "Other": "#94A3B8",
}

# ECG class labels
MITBIH_CLASSES = {0: "Normal (N)", 1: "Supraventricular (S)", 2: "Ventricular (V)", 3: "Fusion (F)", 4: "Unknown (Q)"}
PTBDB_CLASSES = {0: "Normal", 1: "Abnormal"}

# Federal Supply Class mapping (NSN first 4 digits)
FSC_CATEGORIES = {
    "10": "Weapons",
    "11": "Nuclear Ordnance",
    "12": "Fire Control Equipment",
    "13": "Ammunition & Explosives",
    "14": "Guided Missiles",
    "15": "Aircraft",
    "16": "Aircraft Components",
    "17": "Aircraft Launch Equipment",
    "19": "Ships & Marine Equipment",
    "20": "Ship Components",
    "22": "Railway Equipment",
    "23": "Motor Vehicles",
    "24": "Tractors",
    "25": "Vehicular Equipment",
    "26": "Tires & Tubes",
    "28": "Engines & Turbines",
    "29": "Engine Accessories",
    "30": "Mechanical Power Transmission",
    "31": "Bearings",
    "32": "Woodworking Machinery",
    "34": "Metalworking Machinery",
    "35": "Service & Trade Equipment",
    "36": "Special Industry Machinery",
    "37": "Agricultural Machinery",
    "38": "Construction Equipment",
    "39": "Materials Handling Equipment",
    "40": "Rope, Cable, Chain",
    "41": "Refrigeration Equipment",
    "42": "Fire Fighting Equipment",
    "43": "Pumps & Compressors",
    "44": "Furnace & Heating",
    "45": "Plumbing & HVAC",
    "46": "Water Purification",
    "47": "Pipe & Tubing",
    "48": "Valves",
    "49": "Maintenance Equipment",
    "51": "Hand Tools",
    "52": "Measuring Tools",
    "53": "Hardware & Abrasives",
    "54": "Prefabricated Structures",
    "55": "Lumber & Millwork",
    "56": "Construction Materials",
    "58": "Communications Equipment",
    "59": "Electrical Components",
    "60": "Fiber Optics",
    "61": "Electric Wire & Cable",
    "62": "Lighting Fixtures",
    "63": "Alarm & Signal Systems",
    "65": "Medical Equipment",
    "66": "Instruments & Lab Equipment",
    "67": "Photographic Equipment",
    "68": "Chemicals",
    "69": "Training Aids",
    "70": "IT Equipment",
    "71": "Furniture",
    "72": "Household Furnishings",
    "73": "Food Preparation Equipment",
    "74": "Office Machines",
    "75": "Office Supplies",
    "76": "Books & Maps",
    "77": "Musical Instruments",
    "78": "Recreational Equipment",
    "79": "Cleaning Equipment",
    "80": "Brushes & Paints",
    "81": "Containers & Packaging",
    "83": "Textiles & Leather",
    "84": "Clothing",
    "85": "Toiletries",
    "87": "Agricultural Supplies",
    "88": "Live Animals",
    "89": "Subsistence (Food)",
    "91": "Fuels & Lubricants",
    "93": "Nonmetallic Materials",
    "94": "Nonmetallic Crude Materials",
    "95": "Metal Bars & Sheets",
    "96": "Ores & Minerals",
    "99": "Miscellaneous",
}


# Simplified category mapping
def get_equipment_category(nsn):
    """Map NSN to a simplified equipment category."""
    if not isinstance(nsn, str) or len(nsn) < 2:
        return "Other"
    prefix = nsn[:2]
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
    return category_map.get(prefix, "Other")


# US state abbreviation to full name mapping
STATE_ABBREV_TO_NAME = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
    "PR": "Puerto Rico",
    "VI": "Virgin Islands",
    "GU": "Guam",
    "AS": "American Samoa",
}

STATE_NAME_TO_ABBREV = {v: k for k, v in STATE_ABBREV_TO_NAME.items()}

# US Census regions
CENSUS_REGIONS = {
    "CT": "Northeast",
    "ME": "Northeast",
    "MA": "Northeast",
    "NH": "Northeast",
    "RI": "Northeast",
    "VT": "Northeast",
    "NJ": "Northeast",
    "NY": "Northeast",
    "PA": "Northeast",
    "IL": "Midwest",
    "IN": "Midwest",
    "MI": "Midwest",
    "OH": "Midwest",
    "WI": "Midwest",
    "IA": "Midwest",
    "KS": "Midwest",
    "MN": "Midwest",
    "MO": "Midwest",
    "NE": "Midwest",
    "ND": "Midwest",
    "SD": "Midwest",
    "DE": "South",
    "FL": "South",
    "GA": "South",
    "MD": "South",
    "NC": "South",
    "SC": "South",
    "VA": "South",
    "DC": "South",
    "WV": "South",
    "AL": "South",
    "KY": "South",
    "MS": "South",
    "TN": "South",
    "AR": "South",
    "LA": "South",
    "OK": "South",
    "TX": "South",
    "AZ": "West",
    "CO": "West",
    "ID": "West",
    "MT": "West",
    "NV": "West",
    "NM": "West",
    "UT": "West",
    "WY": "West",
    "AK": "West",
    "CA": "West",
    "HI": "West",
    "OR": "West",
    "WA": "West",
}

REGION_COLORS = {
    "Northeast": "#38BDF8",
    "Midwest": "#34D399",
    "South": "#FB7185",
    "West": "#FBBF24",
}

# DEMIL (Demilitarization) code labels
DEMIL_LABELS = {
    "A": "Non-MLI (No Destruction)",
    "B": "Demil w/ Demil Procedures",
    "C": "Demil w/ Key Point Removal",
    "D": "Controlled Demil",
    "E": "DoD Sponsored Export Controlled",
    "F": "USML Items (Munitions List)",
    "G": "Purple – Government Furnished",
    "Q": "Conditional (Commodity)",
    "P": "Depleted Uranium",
    "Unknown": "Unknown / Not Classified",
}

# US state populations (2020 Census estimates) for per-capita normalization
STATE_POPULATION = {
    "AL": 5024279,
    "AK": 733391,
    "AZ": 7151502,
    "AR": 3011524,
    "CA": 39538223,
    "CO": 5773714,
    "CT": 3605944,
    "DE": 989948,
    "FL": 21538187,
    "GA": 10711908,
    "HI": 1455271,
    "ID": 1839106,
    "IL": 12812508,
    "IN": 6785528,
    "IA": 3190369,
    "KS": 2937880,
    "KY": 4505836,
    "LA": 4657757,
    "ME": 1362359,
    "MD": 6177224,
    "MA": 7029917,
    "MI": 10077331,
    "MN": 5706494,
    "MS": 2961279,
    "MO": 6154913,
    "MT": 1084225,
    "NE": 1961504,
    "NV": 3104614,
    "NH": 1377529,
    "NJ": 9288994,
    "NM": 2117522,
    "NY": 20201249,
    "NC": 10439388,
    "ND": 779094,
    "OH": 11799448,
    "OK": 3959353,
    "OR": 4237256,
    "PA": 13002700,
    "RI": 1097379,
    "SC": 5118425,
    "SD": 886667,
    "TN": 6910840,
    "TX": 29145505,
    "UT": 3271616,
    "VT": 643077,
    "VA": 8631393,
    "WA": 7614893,
    "WV": 1793716,
    "WI": 5893718,
    "WY": 576851,
    "DC": 689545,
    "PR": 3285874,
    "VI": 87146,
    "GU": 168485,
    "AS": 49710,
}

# Plotly template defaults
PLOTLY_TEMPLATE = "plotly_dark"
