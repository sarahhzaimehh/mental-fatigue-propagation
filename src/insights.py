import pandas as pd
import numpy as np

def compute_insights(df):
    """
    Analyzes the dataframe to find top high/low load segments and primary causes.
    Returns a dictionary with the results.
    """
    # Group by section_id to get unique segments
    segment_cols = ['section_id', 'CLI', 'CLI_smooth', 
                    'steering_entropy', 'throttle_jerk', 'brake_panic', 
                    'lat_instability', 'long_jerk']
    
    # Check if columns exist
    available_cols = [c for c in segment_cols if c in df.columns]
    
    # Remove section_id from available_cols if present to avoid duplication on reset_index
    if 'section_id' in available_cols:
        available_cols.remove('section_id')

    df_segments = df.groupby('section_id')[available_cols].first().reset_index()
    
    # Normalize metrics for comparison (0-1 scale) to find "cause"
    metrics = ['steering_entropy', 'throttle_jerk', 'brake_panic', 'lat_instability', 'long_jerk']
    df_norm = df_segments.copy()
    
    for m in metrics:
        if m in df_norm.columns:
            min_val = df_norm[m].min()
            max_val = df_norm[m].max()
            if max_val - min_val > 0:
                df_norm[f'{m}_norm'] = (df_norm[m] - min_val) / (max_val - min_val)
            else:
                df_norm[f'{m}_norm'] = 0

    # Define weights
    weights = {
        'steering_entropy': 0.4,
        'throttle_jerk': 0.3,
        'brake_panic': 0.2,
        'lat_instability': 0.1,
        'long_jerk': 0.0
    }

    def get_primary_cause(row):
        max_val = -1
        cause = "Unknown"
        for m in metrics:
            norm_col = f'{m}_norm'
            if norm_col in row:
                w = weights.get(m, 0.1)
                weighted_val = row[norm_col] * w
                if weighted_val > max_val:
                    max_val = weighted_val
                    cause = m
        return cause

    df_segments['Primary Cause'] = df_norm.apply(get_primary_cause, axis=1)

    # Top 5 High Load
    top_5_high = df_segments.sort_values('CLI_smooth', ascending=False).head(5)
    
    # Top 5 Low Load
    top_5_low = df_segments.sort_values('CLI_smooth', ascending=True).head(5)

    # Stats
    avg_cli = df_segments['CLI_smooth'].mean()
    max_cli = df_segments['CLI_smooth'].max()
    
    # Most common cause in high load areas (top 20%)
    high_load_threshold = df_segments['CLI_smooth'].quantile(0.8)
    high_load_segments = df_segments[df_segments['CLI_smooth'] >= high_load_threshold]
    if not high_load_segments.empty:
        common_cause = high_load_segments['Primary Cause'].mode()[0]
    else:
        common_cause = "N/A"
        
    # Identify "Stressful Corner" (Segment with Max CLI)
    max_stress_segment = df_segments.loc[df_segments['CLI_smooth'].idxmax()]
    
    # Identify "Least Stressful Corner"
    min_stress_segment = df_segments.loc[df_segments['CLI_smooth'].idxmin()]

    return {
        'top_5_high': top_5_high,
        'top_5_low': top_5_low,
        'avg_cli': avg_cli,
        'max_cli': max_cli,
        'common_cause': common_cause,
        'max_stress_segment': max_stress_segment,
        'min_stress_segment': min_stress_segment,
        'df_segments': df_segments
    }
