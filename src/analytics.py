from pathlib import Path
import duckdb

# --------------------------------------------------
# 1. Define project paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

PARQUET_FILE = PROJECT_DIR / "data" / "processed" / "water_quality_cleaned.parquet"
ANALYTICS_DIR = PROJECT_DIR / "data" / "analytics"

# Create analytics folder if it does not exist
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Check whether the cleaned dataset exists
# --------------------------------------------------

if not PARQUET_FILE.exists():
    raise FileNotFoundError(
        f"Cleaned dataset not found: {PARQUET_FILE}\n"
        "Please run: python src/etl_pipeline.py"
    )


# --------------------------------------------------
# 3. Connect to DuckDB and load the dataset
# --------------------------------------------------

print("Connecting to DuckDB...")

con = duckdb.connect(database=":memory:")

try:
    # DuckDB reads the cleaned Parquet file directly.
    # Using a safely escaped path avoids the prepared-parameter
    # error that occurred while creating the view.
    parquet_path = PARQUET_FILE.as_posix()
    escaped_path = parquet_path.replace("'", "''")

    con.execute(
        f"""
        CREATE VIEW water_quality AS
        SELECT *
        FROM read_parquet('{escaped_path}')
        """
    )

    print("Dataset loaded successfully!")


    # --------------------------------------------------
    # 4. Overall dataset summary
    # --------------------------------------------------

    print("\n========== OVERALL SUMMARY ==========")

    summary = con.execute("""
        SELECT
            COUNT(*) AS total_records,
            COUNT(DISTINCT state_name) AS total_states,
            COUNT(DISTINCT district_name) AS total_districts,
            COUNT(DISTINCT quality_parameter) AS total_quality_parameters,
            MIN(year) AS first_year,
            MAX(year) AS last_year
        FROM water_quality
    """).df()

    print(summary.to_string(index=False))


    # --------------------------------------------------
    # 5. Records by state
    # --------------------------------------------------

    print("\n========== TOP 10 STATES ==========")

    records_by_state = con.execute("""
        SELECT
            state_name,
            COUNT(*) AS total_records
        FROM water_quality
        GROUP BY state_name
        ORDER BY total_records DESC
        LIMIT 10
    """).df()

    print(records_by_state.to_string(index=False))

    records_by_state.to_csv(
        ANALYTICS_DIR / "records_by_state.csv",
        index=False
    )


    # --------------------------------------------------
    # 6. Records by water-quality parameter
    # --------------------------------------------------

    print("\n========== RECORDS BY QUALITY PARAMETER ==========")

    records_by_parameter = con.execute("""
        SELECT
            quality_parameter,
            COUNT(*) AS total_records
        FROM water_quality
        GROUP BY quality_parameter
        ORDER BY total_records DESC
    """).df()

    print(records_by_parameter.to_string(index=False))

    records_by_parameter.to_csv(
        ANALYTICS_DIR / "records_by_parameter.csv",
        index=False
    )


    # --------------------------------------------------
    # 7. Records by year
    # --------------------------------------------------

    print("\n========== RECORDS BY YEAR ==========")

    records_by_year = con.execute("""
        SELECT
            year,
            COUNT(*) AS total_records
        FROM water_quality
        GROUP BY year
        ORDER BY year
    """).df()

    print(records_by_year.to_string(index=False))

    records_by_year.to_csv(
        ANALYTICS_DIR / "records_by_year.csv",
        index=False
    )


    # --------------------------------------------------
    # 8. Top 10 districts
    # --------------------------------------------------

    print("\n========== TOP 10 DISTRICTS ==========")

    top_districts = con.execute("""
        SELECT
            state_name,
            district_name,
            COUNT(*) AS total_records
        FROM water_quality
        GROUP BY state_name, district_name
        ORDER BY total_records DESC
        LIMIT 10
    """).df()

    print(top_districts.to_string(index=False))

    top_districts.to_csv(
        ANALYTICS_DIR / "top_districts.csv",
        index=False
    )


    # --------------------------------------------------
    # 9. Completion message
    # --------------------------------------------------

    print("\n========== ANALYTICS COMPLETED ==========")
    print(f"Analytics files saved in: {ANALYTICS_DIR}")

    print("\nGenerated files:")
    print("- records_by_state.csv")
    print("- records_by_parameter.csv")
    print("- records_by_year.csv")
    print("- top_districts.csv")

finally:
    con.close()