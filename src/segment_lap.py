import pandas as pd
import numpy as np

def segment_lap(df, num_segments=60):
    """
    Segments the lap into equal distance parts.
    """
    # Ensure sorted by distance
    df = df.sort_values('Laptrigger_lapdist_dls').reset_index(drop=True)
    
    max_dist = df['Laptrigger_lapdist_dls'].max()
    segment_length = max_dist / num_segments
    
    # Assign segment ID
    # We use floor division, but clip to num_segments-1 for the very last point
    df['segment_id'] = (df['Laptrigger_lapdist_dls'] // segment_length).astype(int)
    df['segment_id'] = df['segment_id'].clip(upper=num_segments - 1)
    
    return df

if __name__ == "__main__":
    # Test stub
    try:
        from load_data import load_telemetry
        df = load_telemetry()
        df_seg = segment_lap(df)
        print(f"Segmented into {df_seg['segment_id'].nunique()} segments.")
    except ImportError:
        print("load_data module not found for testing.")
