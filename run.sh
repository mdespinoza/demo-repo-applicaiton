#!/bin/bash
# Run the Data Visualization Dashboard
cd "$(dirname "$0")"
pip install -r requirements.txt --quiet
python3 app/main.py
