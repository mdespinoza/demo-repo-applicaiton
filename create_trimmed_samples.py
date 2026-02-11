#!/usr/bin/env python3
"""
Create trimmed sample versions of ECG dataset files for repository inclusion.

This script reads the full ECG dataset files and creates smaller sample versions
by selecting a fixed number of samples per class using stratified random sampling.
The sample files maintain the exact CSV format (no headers, 188 columns) and can
be used for demonstration and testing purposes.
"""

import os
import pandas as pd
from pathlib import Path


def create_trimmed_sample(input_path, output_path, samples_per_class=100, random_state=42):
    """
    Create a trimmed sample from a full ECG dataset file.

    Args:
        input_path: Path to the full dataset CSV file
        output_path: Path where the sample CSV should be saved
        samples_per_class: Number of samples to select per class (default: 100)
        random_state: Random seed for reproducibility (default: 42)

    Returns:
        Dictionary with statistics about the created sample
    """
    print(f"\nProcessing: {input_path}")

    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"  ⚠️  File not found: {input_path}")
        return None

    # Read the full dataset (no header, 188 columns)
    df = pd.read_csv(input_path, header=None)
    original_rows = len(df)

    # Extract label column (last column, index 187)
    df['label'] = df[187].astype(int)

    # Get class distribution
    class_counts = df['label'].value_counts().sort_index()
    print(f"  Original: {original_rows:,} rows")
    print(f"  Classes: {dict(class_counts)}")

    # Sample from each class
    sampled_dfs = []
    actual_samples = {}

    for label in sorted(class_counts.index):
        class_df = df[df['label'] == label]
        n_samples = min(samples_per_class, len(class_df))

        if n_samples > 0:
            sampled = class_df.sample(n=n_samples, random_state=random_state)
            sampled_dfs.append(sampled)
            actual_samples[label] = n_samples

    # Combine all samples and shuffle
    result_df = pd.concat(sampled_dfs, ignore_index=True)
    result_df = result_df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    # Drop the temporary label column to maintain original format
    result_df = result_df.drop('label', axis=1)

    # Save to output file (no header, preserve format)
    result_df.to_csv(output_path, header=False, index=False)

    # Get file sizes
    original_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    sample_size_mb = os.path.getsize(output_path) / (1024 * 1024)

    print(f"  Sample: {len(result_df):,} rows ({dict(actual_samples)})")
    print(f"  Size: {original_size_mb:.1f} MB → {sample_size_mb:.2f} MB ({sample_size_mb/original_size_mb*100:.1f}%)")
    print(f"  ✓ Saved: {output_path}")

    return {
        'input_file': input_path,
        'output_file': output_path,
        'original_rows': original_rows,
        'sample_rows': len(result_df),
        'original_size_mb': original_size_mb,
        'sample_size_mb': sample_size_mb,
        'classes': actual_samples
    }


def main():
    """Main function to create all trimmed sample files."""

    print("=" * 80)
    print("ECG Dataset Trimmed Sample Creation")
    print("=" * 80)
    print(f"Samples per class: 100")
    print(f"Random seed: 42")

    # Define input and output file paths
    base_dir = Path(__file__).parent / "datasets" / "ecg_data"

    files_to_process = [
        ("mitbih_train.csv", "mitbih_train_sample.csv"),
        ("mitbih_test.csv", "mitbih_test_sample.csv"),
        ("ptbdb_normal.csv", "ptbdb_normal_sample.csv"),
        ("ptbdb_abnormal.csv", "ptbdb_abnormal_sample.csv"),
    ]

    # Process each file
    results = []
    for input_filename, output_filename in files_to_process:
        input_path = base_dir / input_filename
        output_path = base_dir / output_filename

        result = create_trimmed_sample(str(input_path), str(output_path))
        if result:
            results.append(result)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if results:
        total_original_size = sum(r['original_size_mb'] for r in results)
        total_sample_size = sum(r['sample_size_mb'] for r in results)
        total_original_rows = sum(r['original_rows'] for r in results)
        total_sample_rows = sum(r['sample_rows'] for r in results)

        print(f"\nFiles created: {len(results)}")
        print(f"Total rows: {total_original_rows:,} → {total_sample_rows:,}")
        print(f"Total size: {total_original_size:.1f} MB → {total_sample_size:.2f} MB")
        print(f"Compression: {total_sample_size/total_original_size*100:.1f}%")

        print("\n✓ All sample files created successfully!")
        print("\nNext steps:")
        print("  1. Update .gitignore to track sample files")
        print("  2. Update datasets/ecg_data/README.md with sample information")
        print("  3. Commit sample files to repository")
    else:
        print("\n⚠️  No files were processed. Check that full dataset files exist.")
        print("\nExpected files in datasets/ecg_data/:")
        print("  - mitbih_train.csv")
        print("  - mitbih_test.csv")
        print("  - ptbdb_normal.csv")
        print("  - ptbdb_abnormal.csv")

    print("=" * 80)


if __name__ == "__main__":
    main()
