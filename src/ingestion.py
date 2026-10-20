from pathlib import Path
import pandas as pd


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Location of the original dataset
RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "IndiaAffectedWaterQualityAreas.csv"
)


def inspect_dataset():
    print("=" * 60)
    print("WATER QUALITY DATA PIPELINE")
    print("STAGE 1: DATA INGESTION")
    print("=" * 60)

    # Check whether the CSV exists
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {RAW_FILE}"
        )

    print("\nReading dataset...")

    # Load the CSV
    df = pd.read_csv(RAW_FILE)

    # Display dataset information
    print("\nDataset loaded successfully!")
    print(f"Total records: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")

    print("\nColumn names:")
    for column in df.columns:
        print(f"- {column}")

    print("\nFirst 5 records:")
    print(df.head().to_string(index=False))

    print("\nData types:")
    print(df.dtypes.to_string())

    print("\nMissing values:")
    print(df.isnull().sum().to_string())

    print("\nDuplicate records:")
    print(df.duplicated().sum())

    print("\nDataset inspection completed!")


if __name__ == "__main__":
    inspect_dataset()