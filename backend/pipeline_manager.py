import subprocess
import sys
import threading
import uuid

from datetime import datetime, timezone
from pathlib import Path


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

PIPELINE_SCRIPTS = [
    "src/ingestion.py",
    "src/etl_pipeline.py",
    "src/analytics.py",
]

# In-memory job tracking
JOBS = {}

# Lock prevents concurrent pipeline runs
PIPELINE_LOCK = threading.Lock()


# ==================================================
# 2. UTILITY FUNCTIONS
# ==================================================

def current_time():
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def get_job(job_id):
    """Return job information using its ID."""
    return JOBS.get(job_id)


# ==================================================
# 3. BACKGROUND PIPELINE EXECUTION
# ==================================================

def run_pipeline(job_id):
    """
    Run ingestion, ETL, and analytics sequentially
    in a background thread.
    """

    job = JOBS[job_id]

    # Prevent simultaneous pipeline executions
    if not PIPELINE_LOCK.acquire(blocking=False):
        job["status"] = "failed"
        job["message"] = (
            "Another pipeline run is already in progress."
        )
        job["finished_at"] = current_time()
        return

    try:
        job["status"] = "running"
        job["started_at"] = current_time()
        job["message"] = "Pipeline execution started."

        total_steps = len(PIPELINE_SCRIPTS)

        for index, script in enumerate(
            PIPELINE_SCRIPTS,
            start=1,
        ):

            script_path = PROJECT_DIR / script

            # ------------------------------------------
            # Validate script existence
            # ------------------------------------------

            if not script_path.exists():
                raise FileNotFoundError(
                    f"Pipeline script not found: {script_path}"
                )

            # ------------------------------------------
            # Update current step
            # ------------------------------------------

            job["current_step"] = script
            job["message"] = (
                f"Running step {index} of "
                f"{total_steps}: {script}"
            )

            job["progress"] = round(
                ((index - 1) / total_steps) * 100
            )

            # ------------------------------------------
            # Record step start
            # ------------------------------------------

            step_info = {
                "step": script,
                "status": "running",
                "started_at": current_time(),
                "completed_at": None,
                "return_code": None,
                "stdout": "",
                "stderr": "",
            }

            job["steps"].append(step_info)

            # ------------------------------------------
            # Execute script
            # ------------------------------------------

            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(script_path),
                    ],
                    cwd=str(PROJECT_DIR),
                    capture_output=True,
                    text=True,
                    timeout=1800,
                    check=False,
                )

            except subprocess.TimeoutExpired as exc:
                step_info["status"] = "failed"
                step_info["stderr"] = (
                    "Step timed out after 30 minutes."
                )
                step_info["completed_at"] = current_time()

                raise RuntimeError(
                    f"{script} timed out after 30 minutes."
                ) from exc

            # ------------------------------------------
            # Save execution output
            # ------------------------------------------

            step_info["return_code"] = result.returncode
            step_info["stdout"] = result.stdout[-5000:]
            step_info["stderr"] = result.stderr[-5000:]
            step_info["completed_at"] = current_time()

            # ------------------------------------------
            # Handle errors
            # ------------------------------------------

            if result.returncode != 0:
                step_info["status"] = "failed"

                raise RuntimeError(
                    f"{script} failed with exit code "
                    f"{result.returncode}. Check step output."
                )

            # ------------------------------------------
            # Mark step completed
            # ------------------------------------------

            step_info["status"] = "completed"

            job["completed_steps"] = index

            job["progress"] = round(
                (index / total_steps) * 100
            )

            job["message"] = (
                f"Completed step {index} of "
                f"{total_steps}: {script}"
            )

        # ----------------------------------------------
        # All steps completed
        # ----------------------------------------------

        job["status"] = "completed"
        job["progress"] = 100
        job["completed_steps"] = total_steps
        job["message"] = (
            "All pipeline steps completed successfully."
        )

    except Exception as exc:
        job["status"] = "failed"
        job["message"] = str(exc)

    finally:
        job["finished_at"] = current_time()
        job["current_step"] = None

        if PIPELINE_LOCK.locked():
            PIPELINE_LOCK.release()


# ==================================================
# 4. START A PIPELINE JOB
# ==================================================

def start_pipeline():
    """
    Create a job and start background execution.
    """

    # Reject a new run if another is active
    if PIPELINE_LOCK.locked():
        raise RuntimeError(
            "A pipeline run is already in progress."
        )

    job_id = str(uuid.uuid4())

    # ----------------------------------------------
    # Initialize job information
    # ----------------------------------------------

    JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Pipeline job created.",
        "current_step": None,
        "progress": 0,
        "completed_steps": 0,
        "total_steps": len(PIPELINE_SCRIPTS),
        "created_at": current_time(),
        "started_at": None,
        "finished_at": None,
        "steps": [],
    }

    # ----------------------------------------------
    # Start background thread
    # ----------------------------------------------

    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id,),
        daemon=True,
    )

    thread.start()

    return JOBS[job_id]