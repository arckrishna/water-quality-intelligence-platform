from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Input: original CSV dataset
RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "IndiaAffectedWaterQualityAreas.csv"
)

# Output: cleaned Parquet dataset
PROCESSED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "water_quality_cleaned.parquet"
)

# Output: data quality report
QUALITY_REPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "analytics"
    / "data_quality_report.csv"
)


# ============================================================
# ETL PIPELINE
# ============================================================

def run_etl():

    print("=" * 60)
    print("WATER QUALITY DATA ENGINEERING PIPELINE")
    print("STAGE 2: ETL PROCESSING")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. CHECK RAW DATASET
    # --------------------------------------------------------

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {RAW_FILE}"
        )

    # --------------------------------------------------------
    # 2. EXTRACT RAW DATA
    # --------------------------------------------------------

    print("\n1. Extracting raw data...")

    df = pd.read_csv(RAW_FILE)

    original_count = len(df)

    print(f"Original records: {original_count:,}")

    # Initialize data quality statistics
    quality_stats = {
        "original_records": original_count,
        "invalid_dates": 0,
        "duplicates_removed": 0,
        "final_records": 0,
        "total_columns": len(df.columns),
        "missing_values_total": 0,
        "missing_values_by_column": "",
        "validation_status": "In Progress",
    }

    # --------------------------------------------------------
    # 3. STANDARDIZE COLUMN NAMES
    # --------------------------------------------------------

    print("\n2. Standardizing column names...")

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    print("Column names standardized.")

    # --------------------------------------------------------
    # 4. CLEAN TEXT FIELDS
    # --------------------------------------------------------

    print("\n3. Cleaning text fields...")

    text_columns = df.select_dtypes(
        include=["object", "str"]
    ).columns

    for column in text_columns:
        df[column] = df[column].str.strip()

    print("Leading and trailing whitespace removed.")

    # --------------------------------------------------------
    # 5. CHECK MISSING VALUES
    # --------------------------------------------------------

    print("\n4. Checking missing values...")

    missing_by_column = df.isna().sum()

    missing_values_total = int(missing_by_column.sum())

    missing_details = {
        column: int(count)
        for column, count in missing_by_column.items()
        if count > 0
    }

    quality_stats["missing_values_total"] = (
        missing_values_total
    )

    quality_stats["missing_values_by_column"] = str(
        missing_details
    )

    print(
        f"Total missing values: {missing_values_total:,}"
    )

    if missing_details:
        print("Columns containing missing values:")

        for column, count in missing_details.items():
            print(f"- {column}: {count:,}")
    else:
        print("No missing values found.")

    # --------------------------------------------------------
    # 6. CONVERT AND VALIDATE DATES
    # --------------------------------------------------------

    print("\n5. Converting dates...")

    if "year" not in df.columns:
        raise ValueError(
            "Required date column 'year' was not found."
        )

    df["sample_date"] = pd.to_datetime(
        df["year"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    invalid_dates = int(
        df["sample_date"].isna().sum()
    )

    quality_stats["invalid_dates"] = invalid_dates

    print(f"Invalid dates: {invalid_dates:,}")

    # Stop if dates cannot be interpreted
    if invalid_dates > 0:
        quality_stats["validation_status"] = "Failed"

        raise ValueError(
            f"{invalid_dates} invalid dates were found. "
            "Check the source data before continuing."
        )

    # Extract integer year
    df["year"] = df["sample_date"].dt.year

    # Remove temporary date column
    df = df.drop(columns=["sample_date"])

    # --------------------------------------------------------
    # 7. REMOVE DUPLICATE RECORDS
    # --------------------------------------------------------

    print("\n6. Removing duplicate records...")

    duplicates_before = int(
        df.duplicated().sum()
    )

    quality_stats["duplicates_removed"] = (
        duplicates_before
    )

    df = df.drop_duplicates().copy()

    print(
        f"Duplicate records removed: {duplicates_before:,}"
    )

    print(
        f"Records after deduplication: {len(df):,}"
    )

    # --------------------------------------------------------
    # 8. VALIDATE ESSENTIAL FIELDS
    # --------------------------------------------------------

    print("\n7. Validating essential fields...")

    required_columns = [
        "state_name",
        "district_name",
        "quality_parameter",
        "year",
    ]

    # Check whether required columns exist
    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        quality_stats["validation_status"] = "Failed"

        raise ValueError(
            f"Required columns are missing: {missing_columns}"
        )

    # Check for missing values in required columns
    for column in required_columns:

        if df[column].isna().any():

            quality_stats["validation_status"] = "Failed"

            raise ValueError(
                f"Missing values found in {column}"
            )

    print("Essential-field validation passed.")

    # --------------------------------------------------------
    # 9. SAVE CLEANED DATASET
    # --------------------------------------------------------

    print("\n8. Saving processed data...")

    PROCESSED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_parquet(
        PROCESSED_FILE,
        index=False,
        compression="snappy"
    )

    print(
        f"Processed dataset saved to:\n{PROCESSED_FILE}"
    )

    # --------------------------------------------------------
    # 10. UPDATE FINAL STATISTICS
    # --------------------------------------------------------

    quality_stats["final_records"] = len(df)

    quality_stats["total_columns"] = len(df.columns)

    quality_stats["validation_status"] = "Passed"

    # --------------------------------------------------------
    # 11. GENERATE DATA QUALITY REPORT
    # --------------------------------------------------------

    print("\n9. Generating data quality report...")

    QUALITY_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report_rows = [
        {
            "metric": metric,
            "value": value,
        }
        for metric, value in quality_stats.items()
    ]

    report_df = pd.DataFrame(report_rows)

    report_df.to_csv(
        QUALITY_REPORT_FILE,
        index=False
    )

    print(
        f"Data quality report saved to:\n"
        f"{QUALITY_REPORT_FILE}"
    )

    # --------------------------------------------------------
    # 12. PRINT FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ETL COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print(f"Original records: {original_count:,}")

    print(
        f"Duplicates removed: {duplicates_before:,}"
    )

    print(f"Final records: {len(df):,}")

    print(f"Total columns: {len(df.columns)}")

    print(
        f"Total missing values: "
        f"{quality_stats['missing_values_total']:,}"
    )

    print(f"Invalid dates: {invalid_dates:,}")

    print(
        f"Validation status: "
        f"{quality_stats['validation_status']}"
    )

    print("\nFinal column names:")

    for column in df.columns:
        print(f"- {column}")

    print("\nData quality report generated successfully.")


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    run_etl()