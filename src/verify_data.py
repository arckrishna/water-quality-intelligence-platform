from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PARQUET_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "water_quality_cleaned.parquet"
)


def verify_data():
    print("=" * 50)
    print("PARQUET DATA VERIFICATION")
    print("=" * 50)

    if not PARQUET_FILE.exists():
        raise FileNotFoundError(
            f"Parquet file not found: {PARQUET_FILE}"
        )

    df = pd.read_parquet(PARQUET_FILE)

    print(f"\nFile size: {PARQUET_FILE.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"Total records: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")

    print("\nData types:")
    print(df.dtypes)

    print("\nFirst 5 records:")
    print(df.head().to_string(index=False))

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nVerification successful!")


if __name__ == "__main__":
    verify_data()