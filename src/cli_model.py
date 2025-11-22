import pandas as pd
import numpy as np

def normalize_series(series):
    """
    Min-Max normalization to 0-1 range.
    """
    min_val = series.min()
    max_val = series.max()
    if max_val - min_val == 0:
        return series * 0
    return (series - min_val) / (max_val - min_val)

def compute_cli(metrics_df):
    """
    Computes Cognitive Load Index (CLI) from metrics.
    """
    df = metrics_df.copy()
    
    # Normalize metrics
    # Higher values should indicate higher load
    df['norm_steering'] = normalize_series(df['steering_entropy'])
    df['norm_throttle'] = normalize_series(df['throttle_jerk'])
    df['norm_brake'] = normalize_series(df['brake_panic'])
    df['norm_lat'] = normalize_series(df['lat_instability'])
    
    # CLI Formula (Weighted Sum)
    # Weights can be adjusted. Assuming Steering is most indicative of cognitive load (corrections).
    w_steering = 0.4
    w_throttle = 0.3
    w_brake = 0.2
    w_lat = 0.1
    
    df['CLI'] = (
        w_steering * df['norm_steering'] +
        w_throttle * df['norm_throttle'] +
        w_brake * df['norm_brake'] +
        w_lat * df['norm_lat']
    )
    
    # Smooth CLI
    # Rolling average over 3 segments to reduce noise
    df['CLI_smooth'] = df['CLI'].rolling(window=3, center=True, min_periods=1).mean()
    
    return df

if __name__ == "__main__":
    # Test stub
    pass
