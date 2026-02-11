"""One-time ECG data precomputation script.

Processes the large ECG CSV files (~555MB) and generates a compact JSON cache (~2MB)
containing precomputed statistics, sample waveforms, and correlation matrices.

Usage:
    python3 scripts/precompute_ecg_samples.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.loader import _precompute_ecg
from app.config import ECG_CACHE

if __name__ == "__main__":
    print("Precomputing ECG data...")
    _precompute_ecg()
    size_mb = os.path.getsize(ECG_CACHE) / (1024 * 1024)
    print(f"Done! Cache saved to {ECG_CACHE} ({size_mb:.1f} MB)")
