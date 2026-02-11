#!/bin/bash

# Download ECG Dataset Helper Script
# This script helps users download the full ECG dataset from Kaggle

set -e

echo "=================================="
echo "ECG Dataset Download Helper"
echo "=================================="
echo ""

# Define target directory
TARGET_DIR="datasets/ecg_data"
DATASET_NAME="shayanfazeli/heartbeat"

# Expected files and their row counts for validation
declare -A EXPECTED_FILES=(
    ["mitbih_train.csv"]=87554
    ["mitbih_test.csv"]=21892
    ["ptbdb_normal.csv"]=4046
    ["ptbdb_abnormal.csv"]=10506
)

# Check if we're in the correct directory
if [ ! -d "datasets" ]; then
    echo "Error: Please run this script from the repository root directory"
    exit 1
fi

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

echo "Target directory: $TARGET_DIR"
echo ""

# Check if kaggle CLI is installed
if ! command -v kaggle &> /dev/null; then
    echo "⚠️  Kaggle CLI is not installed."
    echo ""
    echo "To download automatically, install the Kaggle CLI:"
    echo "  pip install kaggle"
    echo ""
    echo "Then configure your API credentials:"
    echo "  1. Go to https://www.kaggle.com/account"
    echo "  2. Click 'Create New API Token' to download kaggle.json"
    echo "  3. Place kaggle.json in ~/.kaggle/"
    echo "  4. Run: chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    echo "Alternatively, download manually:"
    echo "  1. Visit: https://www.kaggle.com/datasets/$DATASET_NAME"
    echo "  2. Click 'Download' button"
    echo "  3. Extract the ZIP file"
    echo "  4. Copy the following files to $TARGET_DIR/:"
    for file in "${!EXPECTED_FILES[@]}"; do
        echo "     - $file"
    done
    echo ""
    exit 1
fi

# Check if API credentials are configured
if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
    echo "⚠️  Kaggle API credentials not found."
    echo ""
    echo "Please configure your API credentials:"
    echo "  1. Go to https://www.kaggle.com/account"
    echo "  2. Click 'Create New API Token' to download kaggle.json"
    echo "  3. Place kaggle.json in ~/.kaggle/"
    echo "  4. Run: chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    exit 1
fi

# Download dataset
echo "📥 Downloading dataset from Kaggle..."
echo "Dataset: $DATASET_NAME"
echo ""

kaggle datasets download -d "$DATASET_NAME" -p "$TARGET_DIR" --unzip

echo ""
echo "✓ Download complete!"
echo ""

# Validate downloaded files
echo "🔍 Validating downloaded files..."
echo ""

all_valid=true
for file in "${!EXPECTED_FILES[@]}"; do
    file_path="$TARGET_DIR/$file"
    expected_rows=${EXPECTED_FILES[$file]}

    if [ ! -f "$file_path" ]; then
        echo "❌ Missing: $file"
        all_valid=false
    else
        # Count rows (excluding potential header, but these files have no headers)
        actual_rows=$(wc -l < "$file_path" | tr -d ' ')
        file_size=$(du -h "$file_path" | cut -f1)

        if [ "$actual_rows" -eq "$expected_rows" ]; then
            echo "✓ $file ($file_size, $actual_rows rows)"
        else
            echo "⚠️  $file ($file_size, $actual_rows rows - expected $expected_rows)"
            all_valid=false
        fi
    fi
done

echo ""

if [ "$all_valid" = true ]; then
    echo "=================================="
    echo "✓ All files downloaded and validated successfully!"
    echo "=================================="
    echo ""
    echo "You can now run the application with the full dataset:"
    echo "  python3 app/main.py"
    echo ""
else
    echo "=================================="
    echo "⚠️  Some files are missing or have incorrect row counts"
    echo "=================================="
    echo ""
    echo "Please check the files manually or try downloading again."
    echo ""
    exit 1
fi
