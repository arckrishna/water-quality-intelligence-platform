from pathlib import Path
import time

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Water Quality Intelligence Platform",
    page_icon="💧",
    layout="wide",
)

API_BASE_URL = "http://127.0.0.1:8000"


# ==================================================
# 2. API HELPERS
# ==================================================

def api_get(endpoint, params=None):
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
        return None


def api_post(endpoint):
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        st.error(f"Pipeline request failed: {exc}")
        return None


# ==================================================
# 3. HEADER
# ==================================================

st.title("💧 Water Quality Intelligence Platform")

st.markdown(
    """
    An interactive data engineering platform for exploring
    historical water-quality reports across India.
    """
)

st.caption(
    "Python | Pandas | Parquet | DuckDB | FastAPI | Streamlit"
)

st.divider()


# ==================================================
# 4. BACKEND CONNECTION
# ==================================================

health = api_get("/api/health")

if not health:
    st.warning(
        "Backend unavailable. Start it using:\n\n"
        "`python -m uvicorn backend.main:app --reload`"
    )
    st.stop()

st.success("Backend connected successfully")


# ==================================================
# 5. PIPELINE CONTROL
# ==================================================

st.header("⚙️ Pipeline Monitoring")

col1, col2 = st.columns([1, 2])

with col1:
    if st.button(
        "▶ Run Pipeline",
        type="primary",
        use_container_width=True,
    ):
        result = api_post("/api/pipeline/run")

        if result:
            st.session_state["pipeline_job_id"] = result["job_id"]
            st.session_state.pop("pipeline_job_details", None)
            st.success("Pipeline job submitted.")

with col2:
    job_id = st.session_state.get("pipeline_job_id")

    if job_id:
        st.code(f"Job ID: {job_id}")
    else:
        st.info("Start a pipeline to view execution progress.")


# ==================================================
# 6. PIPELINE STATUS AND PROGRESS
# ==================================================

job_id = st.session_state.get("pipeline_job_id")

if job_id:
    details = api_get(f"/api/pipeline/status/{job_id}")

    if details:
        st.session_state["pipeline_job_details"] = details

        status = details.get("status", "unknown")
        progress = details.get("progress", 0)

        status_col, progress_col = st.columns(2)

        with status_col:
            st.subheader("Current Status")

            if status == "completed":
                st.success("✅ Pipeline completed")
            elif status == "running":
                st.info("🔄 Pipeline running")
            elif status == "queued":
                st.info("⏳ Pipeline queued")
            else:
                st.error(f"❌ Pipeline {status}")

        with progress_col:
            st.subheader("Execution Progress")
            st.progress(min(max(progress, 0), 100))
            st.write(f"**{progress}% complete**")

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Completed Steps",
            details.get("completed_steps", 0),
        )

        metric2.metric(
            "Total Steps",
            details.get("total_steps", 0),
        )

        metric3.metric(
            "Pipeline Status",
            status.upper(),
        )

        st.write(f"**Message:** {details.get('message', '')}")

        time_col1, time_col2 = st.columns(2)

        with time_col1:
            st.write("**Started at**")
            st.write(details.get("started_at") or "Not started")

        with time_col2:
            st.write("**Finished at**")
            st.write(details.get("finished_at") or "Not finished")

        st.subheader("Pipeline Steps")

        steps = details.get("steps", [])

        if steps:
            step_df = pd.DataFrame([
                {
                    "Step": step.get("step", ""),
                    "Status": step.get("status", "unknown").upper(),
                    "Return Code": step.get("return_code"),
                    "Started At": step.get("started_at"),
                    "Completed At": step.get("completed_at"),
                }
                for step in steps
            ])

            st.dataframe(
                step_df,
                use_container_width=True,
                hide_index=True,
            )

            for step in steps:
                label = (
                    f"{step.get('status', 'unknown').upper()} — "
                    f"{step.get('step', 'Pipeline step')}"
                )

                with st.expander(label):
                    if step.get("stdout"):
                        st.markdown("**Output**")
                        st.code(step["stdout"][-3000:])

                    if step.get("stderr"):
                        st.markdown("**Error / diagnostic output**")
                        st.code(step["stderr"][-3000:])

        if status == "running":
            if st.button("Refresh Pipeline Status"):
                st.rerun()

            st.caption(
                "Use Refresh Pipeline Status to check the latest progress."
            )

        elif status == "failed":
            st.error(
                "The pipeline failed. Expand the failed step above "
                "to inspect its diagnostic output."
            )

        else:
            st.success("Pipeline execution details are available.")


st.divider()


st.header("📊 Dataset Overview")

summary = api_get("/api/summary")

if not summary:
    st.stop()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Records",
    f"{summary['total_records']:,}",
)

col2.metric(
    "States / Regions",
    summary["total_states"],
)

col3.metric(
    "Districts",
    summary["total_districts"],
)

col4.metric(
    "Quality Parameters",
    summary["total_parameters"],
)

st.caption(
    f"Historical reporting period: "
    f"{summary['first_year']}–{summary['last_year']}"
)


# ==================================================
# 8. FETCH ANALYTICS
# ==================================================

states_result = api_get("/api/states", params={"limit": 100})
parameters_result = api_get("/api/parameters")
years_result = api_get("/api/years")
districts_result = api_get("/api/districts", params={"limit": 10})

if not all([
    states_result,
    parameters_result,
    years_result,
    districts_result,
]):
    st.error("Unable to load all analytics.")
    st.stop()

states_df = pd.DataFrame(states_result["data"])
parameters_df = pd.DataFrame(parameters_result["data"])
years_df = pd.DataFrame(years_result["data"])
districts_df = pd.DataFrame(districts_result["data"])


# ==================================================
# 9. FILTERS
# ==================================================

st.sidebar.header("🔎 Dashboard Filters")

state_options = sorted(
    states_df["state_name"].dropna().unique().tolist()
)

parameter_options = sorted(
    parameters_df["quality_parameter"].dropna().unique().tolist()
)

selected_states = st.sidebar.multiselect(
    "Select State(s)",
    state_options,
)

selected_parameters = st.sidebar.multiselect(
    "Select Quality Parameter(s)",
    parameter_options,
)

filtered_states = states_df.copy()
filtered_parameters = parameters_df.copy()
filtered_districts = districts_df.copy()

if selected_states:
    filtered_states = filtered_states[
        filtered_states["state_name"].isin(selected_states)
    ]

    filtered_districts = filtered_districts[
        filtered_districts["state_name"].isin(selected_states)
    ]

if selected_parameters:
    filtered_parameters = filtered_parameters[
        filtered_parameters["quality_parameter"].isin(
            selected_parameters
        )
    ]


# ==================================================
# 10. STATE CHART
# ==================================================

st.divider()
st.header("📍 State-wise Records")

if not filtered_states.empty:
    state_chart = px.bar(
        filtered_states.sort_values("total_records"),
        x="total_records",
        y="state_name",
        orientation="h",
        title="Reported Records by State / Region",
        labels={
            "total_records": "Number of Records",
            "state_name": "State / Region",
        },
    )

    st.plotly_chart(
        state_chart,
        use_container_width=True,
    )
else:
    st.info("No state records match your filters.")


# ==================================================
# 11. QUALITY PARAMETERS
# ==================================================

left, right = st.columns(2)

with left:
    st.subheader("🧪 Quality Parameters")

    if not filtered_parameters.empty:
        parameter_chart = px.pie(
            filtered_parameters,
            names="quality_parameter",
            values="total_records",
            hole=0.4,
            title="Records by Quality Parameter",
        )

        st.plotly_chart(
            parameter_chart,
            use_container_width=True,
        )
    else:
        st.info("No parameter records match your filters.")


# ==================================================
# 12. YEARLY ANALYTICS
# ==================================================

with right:
    st.subheader("📅 Yearly Distribution")

    year_chart = px.line(
        years_df.sort_values("year"),
        x="year",
        y="total_records",
        markers=True,
        title="Reported Records by Year",
        labels={
            "year": "Year",
            "total_records": "Number of Records",
        },
    )

    st.plotly_chart(
        year_chart,
        use_container_width=True,
    )


# ==================================================
# 13. DISTRICT ANALYTICS
# ==================================================

st.divider()
st.header("🏙️ District Analysis")

if not filtered_districts.empty:
    district_chart = px.bar(
        filtered_districts,
        x="district_name",
        y="total_records",
        color="state_name",
        title="Top Districts by Reported Records",
        labels={
            "district_name": "District",
            "total_records": "Number of Records",
            "state_name": "State / Region",
        },
    )

    st.plotly_chart(
        district_chart,
        use_container_width=True,
    )

    st.dataframe(
        filtered_districts,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No districts match your selected states.")


# ==================================================
# ==================================================
# 14. DATA QUALITY REPORT
# ==================================================

st.divider()
st.header("🔍 Data Quality Report")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

QUALITY_REPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "analytics"
    / "data_quality_report.csv"
)

if QUALITY_REPORT_FILE.exists():
    quality_df = pd.read_csv(QUALITY_REPORT_FILE)

    if {"metric", "value"}.issubset(quality_df.columns):
        quality_metrics = dict(
            zip(quality_df["metric"], quality_df["value"])
        )

        def metric_as_int(name):
            try:
                return int(float(quality_metrics.get(name, 0)))
            except (TypeError, ValueError):
                return 0

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Original Records",
            f"{metric_as_int('original_records'):,}"
        )
        col2.metric(
            "Duplicates Removed",
            f"{metric_as_int('duplicates_removed'):,}"
        )
        col3.metric(
            "Final Records",
            f"{metric_as_int('final_records'):,}"
        )

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Invalid Dates",
            f"{metric_as_int('invalid_dates'):,}"
        )
        col5.metric(
            "Missing Values",
            f"{metric_as_int('missing_values_total'):,}"
        )
        col6.metric(
            "Total Columns",
            f"{metric_as_int('total_columns'):,}"
        )

        validation_status = str(
            quality_metrics.get("validation_status", "Unknown")
        )

        if validation_status.lower() == "passed":
            st.success("✅ Data quality validation passed.")
        else:
            st.warning(
                f"⚠️ Data quality validation status: {validation_status}"
            )

        st.subheader("Detailed Quality Report")
        st.dataframe(
            quality_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            label="⬇️ Download Data Quality Report",
            data=QUALITY_REPORT_FILE.read_bytes(),
            file_name="data_quality_report.csv",
            mime="text/csv",
        )
    else:
        st.error(
            "The data quality report CSV must contain 'metric' and 'value' columns."
        )
else:
    st.info(
        "Data quality report not found. Run the ETL pipeline to generate it."
    )


# 15. DOWNLOAD ANALYTICS
# ==================================================

st.divider()
st.header("⬇️ Export Analytics")

csv_data = filtered_states.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download State Analytics CSV",
    data=csv_data,
    file_name="water_quality_state_analytics.csv",
    mime="text/csv",
)


# ==================================================
# 16. FOOTER
# ==================================================

st.divider()

st.caption(
    "Water Quality Intelligence Platform | Data Engineering Mini Project"
)

st.caption(
    "This application analyzes historical reported water-quality issues. "
    "It does not provide live sensor measurements or establish current "
    "drinking-water safety."
)