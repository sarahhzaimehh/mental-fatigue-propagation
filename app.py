import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import src.cli_model as cli_model
import src.compute_metrics as compute_metrics
import src.insights as insights
import src.load_data as load_data
import src.segment_lap as segment_lap
import src.track_map as track_map

# Set page config
st.set_page_config(
    page_title="Cognitive Load Analysis - GR Cup",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and Description
st.title("🏎️ Driver Cognitive Load Analysis")
st.markdown("""
**Project:** Mental Fatigue Propagation Across the Lap  
**Series:** Toyota GR Cup

This dashboard visualizes a race driver's **Cognitive Load Index (CLI)**, derived from telemetry signals such as steering entropy, throttle jerk, and brake panic. 
It helps identify which parts of the track induce the highest mental stress.
""")

DATA_DIR = Path("data")

# --- Sidebar Controls ---
st.sidebar.header("Data Configuration")

data_files = load_data.scan_data_directory(DATA_DIR)

if not data_files['telemetry']:
    st.sidebar.error("Place the GR Cup telemetry CSV inside the data/ folder to begin.")
    st.info("No telemetry detected. Add the official GR Cup CSVs to the data/ folder and rerun.")
    st.stop()

st.sidebar.success(f"Telemetry detected: {os.path.basename(data_files['telemetry'])}")


@st.cache_data(show_spinner=False)
def cached_vehicles(path: str):
    return load_data.get_available_vehicles(path)


@st.cache_data(show_spinner=False)
def cached_laps(path: str, vehicle: str):
    return load_data.get_available_laps(path, vehicle)


vehicles = cached_vehicles(data_files['telemetry'])
if not vehicles:
    st.sidebar.error("No vehicles found in telemetry.")
    st.stop()
vehicle_id = st.sidebar.selectbox("Select Vehicle ID", vehicles)

laps = cached_laps(data_files['telemetry'], vehicle_id)
if not laps:
    st.sidebar.error("No laps found for this vehicle.")
    st.stop()
lap_number = st.sidebar.selectbox("Select Lap", laps)

num_segments = st.sidebar.slider("Number of Segments", min_value=40, max_value=80, value=60, step=5)
run_requested = st.sidebar.button("Run Analysis", type="primary")

current_config = {
    'vehicle_id': vehicle_id,
    'lap': lap_number,
    'segments': num_segments,
    'telemetry': data_files['telemetry']
}

should_run = run_requested or 'final_df' not in st.session_state or st.session_state.get('last_config') != current_config

if should_run:
    with st.spinner("Processing telemetry, segmenting lap, and computing CLI..."):
        try:
            df = load_data.load_session(data_files['telemetry'], vehicle_id, lap_number)
        except Exception as e:
            st.error(f"Error processing data: {e}")
            st.stop()

        df_segmented = segment_lap.segment_lap(df, num_segments=num_segments)
        metrics_df = compute_metrics.compute_segment_metrics(df_segmented)
        metrics_df = cli_model.compute_cli(metrics_df)

        metric_cols = ['segment_id', 'section_id', 'CLI', 'CLI_smooth',
                       'steering_entropy', 'throttle_jerk', 'brake_panic',
                       'lat_instability', 'long_jerk']
        metric_cols = [c for c in metric_cols if c in metrics_df.columns]

        final_df = pd.merge(df_segmented, metrics_df[metric_cols], on='segment_id', how='left')
        final_df['vehicle_id'] = vehicle_id
        final_df['lap'] = lap_number
        if 'section_id' not in final_df.columns:
            final_df['section_id'] = final_df['segment_id']

        st.session_state['final_df'] = final_df
        st.session_state['metrics_df'] = metrics_df
        st.session_state['last_config'] = current_config

if 'final_df' in st.session_state and not st.session_state['final_df'].empty:
    final_df = st.session_state['final_df']
    metrics_df = st.session_state['metrics_df']

    results = insights.compute_insights(final_df)
    segment_col = results.get('segment_col', 'segment_id')
    cli_col = results.get('cli_col', 'CLI_smooth')

    st.subheader("Session Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Max CLI", f"{results['max_cli']:.2f}")
    col2.metric("Avg CLI", f"{results['avg_cli']:.2f}")
    max_seg_val = results['max_stress_segment'][segment_col] if not results['max_stress_segment'].empty else "-"
    col3.metric("Max Stress Segment", f"#{int(max_seg_val)}" if max_seg_val != "-" else "-")
    col4.metric("Primary Stressor", results['common_cause'])

    st.divider()

    col_map, col_graph = st.columns([1, 1])

    with col_map:
        st.subheader("📍 Cognitive Load Track Map")
        fig_map = track_map.plot_track_map(final_df)
        st.pyplot(fig_map)
        st.caption("Map reconstructed via dead-reckoning. Red = High Load.")

    with col_graph:
        st.subheader("📈 CLI vs. Lap Segment")
        fig_line, ax_line = plt.subplots(figsize=(10, 6))
        if not metrics_df.empty:
            ax_line.plot(metrics_df['segment_id'], metrics_df[cli_col], color='blue', linewidth=2, label='CLI (Smoothed)')
            ax_line.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='High Load Threshold')
        ax_line.set_xlabel("Track Segment")
        ax_line.set_ylabel("Cognitive Load Index")
        ax_line.set_title("Mental Fatigue Propagation")
        ax_line.legend()
        ax_line.grid(True, alpha=0.3)
        st.pyplot(fig_line)

    st.divider()

    st.subheader("🔍 Detailed Insights")
    tab1, tab2 = st.tabs(["High Load Segments", "Low Load Segments"])

    with tab1:
        st.markdown("### Top 5 High-Stress Areas")
        if not results['top_5_high'].empty:
            st.dataframe(results['top_5_high'][[segment_col, cli_col, 'Primary Cause']].style.format({cli_col: '{:.4f}'}))
            st.info(f"The driver struggles most in these sections, primarily due to **{results['common_cause']}**.")
        else:
            st.info("No high-load segments found.")

    with tab2:
        st.markdown("### Top 5 Low-Stress Areas")
        if not results['top_5_low'].empty:
            st.dataframe(results['top_5_low'][[segment_col, cli_col]].style.format({cli_col: '{:.4f}'}))
            st.success("The driver is most relaxed in these sections.")
        else:
            st.info("No low-load segments found.")
else:
    st.info("👈 Select a Vehicle and Lap from the sidebar, then click 'Run Analysis'.")
