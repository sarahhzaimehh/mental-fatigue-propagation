# Mental Fatigue Propagation Across the Lap

## 🏎️ Project Overview
Estimate a driver's Cognitive Load Index (CLI) around any GR Cup lap (no GPS required) using raw telemetry. The Streamlit dashboard walks through loading telemetry, segmenting the lap, computing steering/throttle/brake metrics, deriving CLI in [0,1], and visualizing both a CLI line plot and a track heatmap.

## 📊 Features
- **Cognitive Load Index (CLI):** Weighted, normalized blend of steering entropy, throttle jerk, brake panic, and lateral instability with smoothing.
- **Track Map Heatmap:** Dead‑reckoning track reconstruction colored by CLI.
- **Insights:** Top/bottom stress segments with primary causes plus summary metrics.
- **Track‑agnostic:** Works with any GR Cup session that matches the official telemetry schema.

## 🛠️ Installation
1) Python 3.9+  
2) Install deps:
```bash
pip install -r requirements.txt
```

## 🚀 Usage
1) Place the official GR Cup telemetry CSV(s) in `data/`. No race data ships with this repo.  
2) Run the dashboard:
```bash
streamlit run app.py
```
3) In the sidebar pick `vehicle_id`, lap, and desired segment count, then click **Run Analysis**.

If `data/` is empty, the app shows a friendly prompt instead of crashing.

## 📂 Project Structure
```
app.py                  # Streamlit entry point
requirements.txt        # Python dependencies
data/                   # Drop telemetry CSVs here (README inside)
screenshots/            # Example output
src/
  load_data.py          # File discovery + header/column normalization
  processor.py          # Lap extraction + dead-reckoning track build
  segment_lap.py        # Distance-based lap segmentation
  compute_metrics.py    # Steering entropy, throttle jerk, brake panic, etc.
  cli_model.py          # Normalize + weighted CLI + smoothing
  track_map.py          # CLI-colored matplotlib track map
  insights.py           # High/low stress segments + explanations
```

## 🧠 Methodology (CLI)
CLI = 0.4 * steering_entropy + 0.3 * throttle_jerk + 0.2 * brake_panic + 0.1 * lat_instability.  
Signals are normalized (0-1), averaged in a rolling window for stability, and mapped to segments for insights and heatmaps. Dead-reckoning integrates speed and steering to approximate the track shape when GPS is absent.
