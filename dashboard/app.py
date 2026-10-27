from pathlib import Path
import time
import json
import re

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
  page_title="Water Quality Intelligence Platform",
  layout="wide",
)

API_BASE_URL = "http://127.0.0.1:8000"


# ==================================================
# PREMIUM WATER INTELLIGENCE VISUAL THEME
# ==================================================
st.markdown(
  """
  <style>
  :root {
    --ink: #102A3A;
    --deep: #092B35;
    --deep-2: #123D48;
    --teal: #2D8A87;
    --blue: #3677A5;
    --page: #F2F6F7;
    --panel: #FFFFFF;
    --line: #DCE6E9;
    --muted: #657985;
  }
  .stApp { background: var(--page); color: var(--ink); font-family: Inter, "Segoe UI", Arial, sans-serif; }
  [data-testid="stHeader"] { background: rgba(242,246,247,.92); }
  [data-testid="stSidebar"] { background: linear-gradient(180deg, #092B35 0%, #0E3943 72%, #102F39 100%); border-right: 1px solid #214C55; }
  [data-testid="stSidebar"] * { color: #E7F0F2 !important; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #B8CDD2 !important; }
  [data-testid="stSidebar"] [data-baseweb="tag"] { background: #2D7779 !important; border-color: #2D7779 !important; }
  [data-testid="stSidebar"] [data-baseweb="tag"] * { color: #FFFFFF !important; }
  [data-testid="stSidebar"] div[role="radiogroup"] label { padding: .42rem .55rem; border-radius: 8px; }
  [data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: rgba(255,255,255,.08); }
  h1, h2, h3 { color: var(--ink) !important; font-family: Inter, "Segoe UI", Arial, sans-serif; letter-spacing: -.025em; }
  h1 { font-size: 2.15rem !important; font-weight: 750 !important; }
  h2 { font-size: 1.5rem !important; font-weight: 720 !important; }
  h3 { font-size: 1.12rem !important; font-weight: 700 !important; }
  p, label, [data-testid="stCaptionContainer"] { color: var(--muted); }
  .hero-panel { position: relative; overflow: hidden; padding: 1.65rem 1.8rem 1.45rem; margin: .2rem 0 1.25rem; border-radius: 16px; background: linear-gradient(112deg, #DCEEF0 0%, #EAF3F4 42%, #B9D5D8 100%); border: 1px solid #D1E3E6; }
  .hero-panel:after { content: ""; position: absolute; width: 330px; height: 330px; right: -70px; top: -170px; border-radius: 50%; border: 38px solid rgba(31,105,116,.10); box-shadow: 0 0 0 28px rgba(31,105,116,.05), 0 0 0 70px rgba(31,105,116,.035); }
  .hero-kicker { font-size: .72rem; letter-spacing: .19em; text-transform: uppercase; color: #2D7779; font-weight: 800; margin-bottom: .55rem; }
  .hero-title { font-size: clamp(1.75rem, 3vw, 2.65rem); line-height: 1.08; font-weight: 800; letter-spacing: -.045em; color: #0B2E3D; max-width: 820px; }
  .hero-subtitle { font-size: 1rem; margin-top: .65rem; color: #47636D; max-width: 780px; }
  .hero-meta { margin-top: 1rem; display: flex; gap: .55rem; flex-wrap: wrap; }
  .hero-pill { display: inline-block; padding: .3rem .62rem; border-radius: 999px; border: 1px solid rgba(25,95,104,.18); color: #245963; background: rgba(255,255,255,.48); font-size: .72rem; font-weight: 700; letter-spacing: .02em; }
  [data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; box-shadow: 0 3px 12px rgba(17,54,67,.035); min-height: 108px; }
  [data-testid="stMetricLabel"] { color: #5E747F !important; font-weight: 700; font-size: .78rem !important; text-transform: uppercase; letter-spacing: .045em; }
  [data-testid="stMetricValue"] { color: var(--ink) !important; font-weight: 800; letter-spacing: -.035em; }
  [data-testid="stMetricDelta"] { font-size: .75rem; }
  .stButton > button, .stDownloadButton > button { background: #176A70; color: #FFFFFF; border: 1px solid #176A70; border-radius: 8px; font-weight: 700; padding: .48rem .9rem; box-shadow: none; transition: background .15s ease, border-color .15s ease; }
  .stButton > button:hover, .stDownloadButton > button:hover { background: #0E4D58; color: #FFFFFF; border-color: #0E4D58; transform: translateY(-1px); }
  [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  div[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 10px; background: #FFFFFF; }
  div[data-testid="stAlert"] { border-radius: 9px; }
  div[data-testid="stPlotlyChart"] { background: #FFFFFF; border: 1px solid #E2EAEC; border-radius: 12px; padding: 6px 6px 0; }
  hr { border-color: var(--line) !important; }
  .section-eyebrow { font-size: .7rem; font-weight: 800; letter-spacing: .15em; text-transform: uppercase; color: #2D8A87; }
  @media (max-width: 800px) { .hero-panel { padding: 1.1rem; } .hero-title { font-size: 1.75rem; } }
  </style>
  """,
  unsafe_allow_html=True,
)

PLOTLY_TEMPLATE = "simple_white"
OCEAN_COLORS = ["#246A8C", "#3D9C9A", "#80B9B4", "#E3B66B", "#D97867", "#7D91A2"]


# ==================================================
# 2. API HELPERS
# ==================================================

@st.cache_data(ttl=60, show_spinner=False)
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

st.markdown(
  """
  <div class="hero-panel">
    <div class="hero-kicker">Water / Intelligence</div>
    <div class="hero-title">Water Quality Intelligence Platform</div>
    <div class="hero-subtitle">Exploring India's historical water-quality reports through data engineering, geographic analysis, and transparent reporting.</div>
    <div class="hero-meta">
      <span class="hero-pill">HISTORICAL DATA · 2009–2012</span>
      <span class="hero-pill">550K+ PROCESSED RECORDS</span>
      <span class="hero-pill">PYTHON · DUCKDB · FASTAPI</span>
    </div>
  </div>
  """,
  unsafe_allow_html=True,
)

st.sidebar.markdown(
  """
  <div style="padding:.65rem .35rem 1.05rem; border-bottom:1px solid rgba(226,241,244,.22); margin-bottom:1rem;">
    <div style="font-size:.7rem;letter-spacing:.16em;text-transform:uppercase;color:#82C5C8;font-weight:800;">WATER / INTELLIGENCE</div>
    <div style="font-size:1.12rem;font-weight:800;line-height:1.2;color:#F3FAFB;margin-top:.45rem;">Research Console</div>
    <div style="font-size:.76rem;color:#B8CDD2;margin-top:.35rem;">Historical analysis · India</div>
  </div>
  """,
  unsafe_allow_html=True,
)
st.sidebar.title("Workspace")
active_page = st.sidebar.radio(
  "Go to",
  [
    "Overview",
    "Advanced Analytics & Insights",
    "Pipeline Monitor",
    "State Analysis & Map",
    "Parameter & Yearly Trends",
    "District Analysis",
    "Data Quality",
    "Export Analytics",
  ],
  key="dashboard_navigation",
)
st.sidebar.caption("Explore historical records and analytical summaries.")


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

if active_page == "Pipeline Monitor":
  st.header("Pipeline Monitoring")

  col1, col2 = st.columns([1, 2])

  with col1:
    if st.button(
      "Run Pipeline",
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
          st.success("Pipeline completed")
        elif status == "running":
          st.info("Pipeline running")
        elif status == "queued":
          st.info("Pipeline queued")
        else:
          st.error(f"Pipeline {status}")

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


if active_page == "Overview":
  st.header("Dataset Overview")

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

st.sidebar.header("Analysis Filters")

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

if st.sidebar.button("Refresh dashboard data", use_container_width=True):
  api_get.clear()
  st.rerun()

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


if active_page == "Advanced Analytics & Insights":
  st.header("Advanced Analytics & Insights")
  st.caption(
    "Insights are calculated from historical reported-record counts. "
    "They describe the available dataset, not current water safety or contamination levels."
  )

  # Prepare safe numeric copies so malformed/missing API values do not break charts.
  insight_states = filtered_states.copy()
  insight_parameters = filtered_parameters.copy()
  insight_years = years_df.copy()
  insight_districts = filtered_districts.copy()

  for frame, column in [
    (insight_states, "total_records"),
    (insight_parameters, "total_records"),
    (insight_years, "total_records"),
    (insight_districts, "total_records"),
  ]:
    if column in frame.columns:
      frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)

  if "year" in insight_years.columns:
    insight_years["year"] = pd.to_numeric(insight_years["year"], errors="coerce")
    insight_years = insight_years.dropna(subset=["year"]).sort_values("year")

  total_filtered_state_records = (
    float(insight_states["total_records"].sum())
    if "total_records" in insight_states.columns else 0
  )
  total_filtered_parameter_records = (
    float(insight_parameters["total_records"].sum())
    if "total_records" in insight_parameters.columns else 0
  )

  # KPI row
  kpi1, kpi2, kpi3, kpi4 = st.columns(4)
  kpi1.metric("States in current view", f"{len(insight_states):,}")
  kpi2.metric("Reported state records", f"{int(total_filtered_state_records):,}")
  kpi3.metric("Parameters in current view", f"{len(insight_parameters):,}")
  kpi4.metric("Parameter record counts", f"{int(total_filtered_parameter_records):,}")

  st.subheader("Automatically Generated Insights")
  insights = []

  if not insight_states.empty and "total_records" in insight_states.columns:
    top_state = insight_states.sort_values("total_records", ascending=False).iloc[0]
    state_total = float(insight_states["total_records"].sum())
    state_share = (float(top_state["total_records"]) / state_total * 100) if state_total else 0
    insights.append(
      f"**Highest-count state/region:** {top_state['state_name']} has "
      f"{int(top_state['total_records']):,} reported records "
      f"({state_share:.1f}% of the state records currently shown)."
    )

  if not insight_parameters.empty and "total_records" in insight_parameters.columns:
    top_parameter = insight_parameters.sort_values("total_records", ascending=False).iloc[0]
    parameter_total = float(insight_parameters["total_records"].sum())
    parameter_share = (float(top_parameter["total_records"]) / parameter_total * 100) if parameter_total else 0
    insights.append(
      f"**Most frequent reported parameter:** {top_parameter['quality_parameter']} "
      f"has {int(top_parameter['total_records']):,} records "
      f"({parameter_share:.1f}% of parameter records currently shown)."
    )

  if not insight_years.empty and "total_records" in insight_years.columns:
    peak_year = insight_years.sort_values("total_records", ascending=False).iloc[0]
    insights.append(
      f"**Peak reporting year:** {int(peak_year['year'])} has the highest count "
      f"in the available yearly summary ({int(peak_year['total_records']):,} records)."
    )

  if not insight_districts.empty and "total_records" in insight_districts.columns:
    top_district = insight_districts.sort_values("total_records", ascending=False).iloc[0]
    district_label = str(top_district.get("district_name", "Unknown district"))
    state_label = str(top_district.get("state_name", "Unknown state/region"))
    insights.append(
      f"**Top district in the returned district list:** {district_label}, {state_label} "
      f"has {int(top_district['total_records']):,} reported records."
    )

  if insights:
    for insight in insights:
      st.markdown(f"- {insight}")
  else:
    st.info("There is not enough analytics data to generate insights for the current filters.")

  st.divider()
  left_chart, right_chart = st.columns(2)

  with left_chart:
    st.subheader("Top States / Regions")
    if not insight_states.empty and "total_records" in insight_states.columns:
      top_states = insight_states.nlargest(10, "total_records").sort_values("total_records")
      state_insight_chart = px.bar(
        top_states,
        x="total_records",
        y="state_name",
        orientation="h",
        text="total_records",
        title="Top 10 by historical reported-record count",
        labels={"total_records": "Reported records", "state_name": "State / Region"},
        color_discrete_sequence=OCEAN_COLORS,
        template=PLOTLY_TEMPLATE,
      )
      state_insight_chart.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False)
      state_insight_chart.update_layout(yaxis_title=None, xaxis_title="Reported records")
      st.plotly_chart(state_insight_chart, use_container_width=True)
    else:
      st.info("No state data is available for this view.")

  with right_chart:
    st.subheader("Parameter Contribution")
    if not insight_parameters.empty and "total_records" in insight_parameters.columns:
      top_parameters = insight_parameters.nlargest(8, "total_records")
      parameter_insight_chart = px.pie(
        top_parameters,
        names="quality_parameter",
        values="total_records",
        hole=0.48,
        title="Share of reported parameter records",
        color_discrete_sequence=OCEAN_COLORS,
        template=PLOTLY_TEMPLATE,
      )
      parameter_insight_chart.update_traces(textposition="inside", textinfo="percent+label")
      st.plotly_chart(parameter_insight_chart, use_container_width=True)
    else:
      st.info("No parameter data is available for this view.")

  st.divider()
  st.subheader(" Yearly Reporting Pattern")
  if not insight_years.empty and {"year", "total_records"}.issubset(insight_years.columns):
    yearly_chart = px.bar(
      insight_years,
      x="year",
      y="total_records",
      text="total_records",
      title="Historical record counts by year",
      labels={"year": "Year", "total_records": "Reported records"},
      color_discrete_sequence=OCEAN_COLORS,
      template=PLOTLY_TEMPLATE,
    )
    yearly_chart.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False)
    yearly_chart.update_layout(xaxis=dict(dtick=1), yaxis_title="Reported records")
    st.plotly_chart(yearly_chart, use_container_width=True)
  else:
    st.info("No yearly summary is available.")

  st.subheader(" Ranked District Summary")
  if not insight_districts.empty:
    ranked_districts = insight_districts.sort_values("total_records", ascending=False).copy()
    ranked_districts.insert(0, "Rank", range(1, len(ranked_districts) + 1))
    st.dataframe(ranked_districts, use_container_width=True, hide_index=True)
    st.download_button(
      "Download ranked district insights",
      data=ranked_districts.to_csv(index=False).encode("utf-8"),
      file_name="water_quality_ranked_district_insights.csv",
      mime="text/csv",
    )
  else:
    st.info("No district data is available for this view.")


if active_page == "State Analysis & Map":
  # ==================================================
  # 10. STATE CHART
  # ==================================================

  st.divider()
  st.header("State-wise Records")

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
      color_discrete_sequence=OCEAN_COLORS,
      template=PLOTLY_TEMPLATE,
    )

    st.plotly_chart(
      state_chart,
      use_container_width=True,
    )
  else:
    st.info("No state records match your filters.")


  # ==================================================
  # 11. INDIA STATE-WISE CHOROPLETH MAP
  # ==================================================

  st.divider()
  st.header("India State-wise Records Map")
  st.caption(
    "State shading represents historical reported-record counts, not current "
    "water quality or drinking-water safety."
  )

  MAP_PROJECT_ROOT = Path(__file__).resolve().parent.parent
  GEOJSON_CANDIDATES = [
    MAP_PROJECT_ROOT / "data" / "india_states.geojson",
    MAP_PROJECT_ROOT / "data" / "india_states.json",
  ]

  @st.cache_data(show_spinner=False)
  def load_geojson(path_string, modified_time):
    with open(path_string, "r", encoding="utf-8") as geojson_file:
      return json.load(geojson_file)

  geojson_path = next((path for path in GEOJSON_CANDIDATES if path.exists()), None)

  STATE_ALIASES_NORMALIZED = {
    "orissa": "odisha",
    "uttaranchal": "uttarakhand",
    "pondicherry": "puducherry",
    "nctofdelhi": "delhi",
    "andamannicobar": "andamanandnicobar islands".replace(" ", ""),
    "andamanandnicobarislands": "andamanandnicobarislands",
    "jammukashmir": "jammukashmir",
  }

  def normalize_state_name(value):
    value = re.sub(r"[^a-z0-9]", "", str(value).casefold())
    return STATE_ALIASES_NORMALIZED.get(value, value)

  if geojson_path is None:
    st.error(
      "Map boundary file not found. Ensure `data/india_states.geojson` exists "
      "inside your project folder."
    )
  else:
    india_geojson = load_geojson(str(geojson_path), geojson_path.stat().st_mtime)
    name_candidates = ("name", "st_nm", "NAME_1", "state", "NAME", "State_Name")
    geojson_name_key = next(
      (key for key in name_candidates if any(
        feature.get("properties", {}).get(key)
        for feature in india_geojson.get("features", [])
      )),
      None,
    )

    if not geojson_name_key:
      st.error("The GeoJSON does not contain a recognizable state-name property.")
    else:
      # Create normalized keys on both sides so spelling, spaces and punctuation
      # don't prevent state polygons from receiving their data values.
      map_geojson = dict(india_geojson)
      map_geojson["features"] = []
      for original_feature in india_geojson.get("features", []):
        feature = dict(original_feature)
        properties = dict(feature.get("properties", {}))
        properties["_map_key"] = normalize_state_name(properties.get(geojson_name_key, ""))
        feature["properties"] = properties
        map_geojson["features"].append(feature)

      map_df = states_df.copy()
      map_df["state_name"] = map_df["state_name"].astype(str).str.strip()
      map_df["_map_key"] = map_df["state_name"].map(normalize_state_name)

      if selected_states:
        map_df = map_df[map_df["state_name"].isin(selected_states)]

      valid_keys = {
        feature.get("properties", {}).get("_map_key")
        for feature in map_geojson["features"]
      }
      map_df = map_df[map_df["_map_key"].isin(valid_keys)].copy()

      if map_df.empty:
        st.warning("No dataset state names matched the map boundaries. The state chart remains available.")
        with st.expander("Map matching details"):
          st.write("Dataset states:", states_df["state_name"].dropna().astype(str).tolist())
          st.write("GeoJSON states:", [f.get("properties", {}).get(geojson_name_key) for f in map_geojson["features"]])
      else:
        india_choropleth = px.choropleth_map(
          map_df,
          geojson=map_geojson,
          locations="_map_key",
          featureidkey="properties._map_key",
          color="total_records",
          color_continuous_scale=[
            "#E0F7FA", "#A5EAF2", "#52C7D9", "#168AAD", "#126782", "#123B5D"
          ],
          hover_name="state_name",
          hover_data={"total_records": ":,", "_map_key": False},
          map_style="carto-positron",
          zoom=3.25,
          center={"lat": 22.8, "lon": 82.0},
          opacity=0.82,
          labels={"total_records": "Historical reported records"},
          title="Historical reported records by state/region",
        )
        india_choropleth.update_layout(
          height=620,
          margin=dict(l=0, r=0, t=58, b=0),
          paper_bgcolor="rgba(0,0,0,0)",
          font=dict(color="#12304A", family="Arial"),
          coloraxis_colorbar=dict(title="Reported<br>records", thickness=14, len=0.72),
        )
        st.plotly_chart(
          india_choropleth,
          use_container_width=True,
          config={"scrollZoom": True, "displayModeBar": False},
          key="india_state_choropleth",
        )


if active_page == "Parameter & Yearly Trends":
  # 12. QUALITY PARAMETERS
  # ==================================================

  left, right = st.columns(2)

  with left:
    st.subheader("Quality Parameters")

    if not filtered_parameters.empty:
      parameter_chart = px.pie(
        filtered_parameters,
        names="quality_parameter",
        values="total_records",
        hole=0.4,
        title="Records by Quality Parameter",
        color_discrete_sequence=OCEAN_COLORS,
        template=PLOTLY_TEMPLATE,
      )

      st.plotly_chart(
        parameter_chart,
        use_container_width=True,
      )
    else:
      st.info("No parameter records match your filters.")


  # ==================================================
  # 13. YEARLY ANALYTICS
  # ==================================================

  with right:
    st.subheader("Yearly Distribution")

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
      color_discrete_sequence=OCEAN_COLORS,
      template=PLOTLY_TEMPLATE,
    )

    st.plotly_chart(
      year_chart,
      use_container_width=True,
    )


if active_page == "District Analysis":
  # ==================================================
  # 14. DISTRICT ANALYTICS
  # ==================================================

  st.divider()
  st.header("District Analysis")

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
      color_discrete_sequence=OCEAN_COLORS,
      template=PLOTLY_TEMPLATE,
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


if active_page == "Data Quality":
  # ==================================================
  # ==================================================
  # 15. DATA QUALITY REPORT
  # ==================================================

  st.divider()
  st.header("Data Quality Report")

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
        st.success(" Data quality validation passed.")
      else:
        st.warning(
          f" Data quality validation status: {validation_status}"
        )

      st.subheader("Detailed Quality Report")
      st.dataframe(
        quality_df,
        use_container_width=True,
        hide_index=True
      )

      st.download_button(
        label="Download Data Quality Report",
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


if active_page == "Export Analytics":
  # 16. DOWNLOAD ANALYTICS
  # ==================================================

  st.divider()
  st.header("Export Analytics")

  csv_data = filtered_states.to_csv(index=False).encode("utf-8")

  st.download_button(
    "Download State Analytics CSV",
    data=csv_data,
    file_name="water_quality_state_analytics.csv",
    mime="text/csv",
  )


# ==================================================
# 17. FOOTER
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
