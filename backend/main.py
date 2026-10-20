from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.pipeline_manager import get_job, start_pipeline


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

PARQUET_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "water_quality_cleaned.parquet"
)


# ==================================================
# 2. CREATE FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Water Quality Intelligence API",
    description=(
        "API for exploring historical water-quality "
        "issue records across India and managing pipeline runs."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# 3. DATABASE HELPER
# ==================================================

def get_connection():
    if not PARQUET_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Cleaned dataset not found. "
                "Run python src/etl_pipeline.py first."
            ),
        )

    con = duckdb.connect(database=":memory:")

    try:
        parquet_path = PARQUET_FILE.as_posix()
        escaped_path = parquet_path.replace("'", "''")

        con.execute(
            f"""
            CREATE VIEW water_quality AS
            SELECT *
            FROM read_parquet('{escaped_path}')
            """
        )

        return con

    except Exception:
        con.close()
        raise


# ==================================================
# 4. HOME
# ==================================================

@app.get("/")
def home():
    return {
        "message": "Welcome to Water Quality Intelligence API",
        "status": "running",
        "documentation": "/docs",
    }


# ==================================================
# 5. HEALTH CHECK
# ==================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Water Quality Intelligence API",
    }


# ==================================================
# 6. OVERALL SUMMARY
# ==================================================

@app.get("/api/summary")
def get_summary():
    con = get_connection()

    try:
        result = con.execute(
            """
            SELECT
                COUNT(*) AS total_records,
                COUNT(DISTINCT state_name) AS total_states,
                COUNT(DISTINCT district_name) AS total_districts,
                COUNT(DISTINCT quality_parameter) AS total_parameters,
                MIN(year) AS first_year,
                MAX(year) AS last_year
            FROM water_quality
            """
        ).fetchone()

        return {
            "total_records": result[0],
            "total_states": result[1],
            "total_districts": result[2],
            "total_parameters": result[3],
            "first_year": result[4],
            "last_year": result[5],
        }

    finally:
        con.close()


# ==================================================
# 7. STATE STATISTICS
# ==================================================

@app.get("/api/states")
def get_states(limit: int = Query(default=10, ge=1, le=100)):
    con = get_connection()

    try:
        rows = con.execute(
            """
            SELECT state_name, COUNT(*) AS total_records
            FROM water_quality
            GROUP BY state_name
            ORDER BY total_records DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()

        return {
            "count": len(rows),
            "data": [
                {"state_name": row[0], "total_records": row[1]}
                for row in rows
            ],
        }

    finally:
        con.close()


# ==================================================
# 8. QUALITY PARAMETER STATISTICS
# ==================================================

@app.get("/api/parameters")
def get_parameters():
    con = get_connection()

    try:
        rows = con.execute(
            """
            SELECT quality_parameter, COUNT(*) AS total_records
            FROM water_quality
            GROUP BY quality_parameter
            ORDER BY total_records DESC
            """
        ).fetchall()

        return {
            "count": len(rows),
            "data": [
                {
                    "quality_parameter": row[0],
                    "total_records": row[1],
                }
                for row in rows
            ],
        }

    finally:
        con.close()


# ==================================================
# 9. YEARLY STATISTICS
# ==================================================

@app.get("/api/years")
def get_years():
    con = get_connection()

    try:
        rows = con.execute(
            """
            SELECT year, COUNT(*) AS total_records
            FROM water_quality
            GROUP BY year
            ORDER BY year
            """
        ).fetchall()

        return {
            "count": len(rows),
            "data": [
                {"year": row[0], "total_records": row[1]}
                for row in rows
            ],
        }

    finally:
        con.close()


# ==================================================
# 10. DISTRICT STATISTICS
# ==================================================

@app.get("/api/districts")
def get_districts(
    state: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
):
    con = get_connection()

    try:
        if state:
            rows = con.execute(
                """
                SELECT state_name, district_name,
                       COUNT(*) AS total_records
                FROM water_quality
                WHERE state_name = ?
                GROUP BY state_name, district_name
                ORDER BY total_records DESC
                LIMIT ?
                """,
                [state, limit],
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT state_name, district_name,
                       COUNT(*) AS total_records
                FROM water_quality
                GROUP BY state_name, district_name
                ORDER BY total_records DESC
                LIMIT ?
                """,
                [limit],
            ).fetchall()

        return {
            "count": len(rows),
            "data": [
                {
                    "state_name": row[0],
                    "district_name": row[1],
                    "total_records": row[2],
                }
                for row in rows
            ],
        }

    finally:
        con.close()


# ==================================================
# 11. START PIPELINE
# ==================================================

@app.post("/api/pipeline/run", status_code=202)
def trigger_pipeline():
    try:
        job = start_pipeline()

        return {
            "message": "Pipeline job accepted.",
            "job_id": job["job_id"],
            "status": job["status"],
            "status_url": f"/api/pipeline/status/{job['job_id']}",
        }

    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


# ==================================================
# 12. CHECK PIPELINE STATUS
# ==================================================

@app.get("/api/pipeline/status/{job_id}")
def pipeline_status(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Pipeline job not found.",
        )

    return job