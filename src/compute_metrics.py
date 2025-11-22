import pandas as pd
import numpy as np
from scipy.stats import entropy

def calculate_shannon_entropy(series, bins=20):
    """
    Calculates Shannon entropy of a signal's histogram.
    """
    counts, _ = np.histogram(series, bins=bins, density=True)
    # Filter zero counts to avoid log(0)
    counts = counts[counts > 0]
    return entropy(counts)

def compute_segment_metrics(df):
    """
    Computes metrics for each segment.
    """
    metrics = []
    
    grouped = df.groupby('segment_id')
    
    for segment_id, group in grouped:
        # Skip empty segments
        if group.empty:
            continue
            
        # 1. Steering Entropy (Using Shannon Entropy of the angle distribution as a proxy for complexity)
        # A more complex driver workload often leads to more corrective inputs -> higher entropy
        steering_entropy = calculate_shannon_entropy(group['Steering_Angle'])
        
        # 2. Throttle Jerk (Micro-corrections)
        # First derivative of throttle (approx)
        throttle_diff = group['throttle'].diff().fillna(0).abs()
        throttle_jerk = throttle_diff.mean()
        
        # 3. Brake Panic (Sudden high pressure changes)
        brake_diff = group['brake_pressure'].diff().fillna(0)
        # We care about sudden INCREASES (panic)
        brake_panic = brake_diff[brake_diff > 0].mean() if not brake_diff[brake_diff > 0].empty else 0
        
        # 4. Lateral Instability (Variance in lateral acceleration)
        lat_instability = group['accy'].std()
        
        # 5. Longitudinal Jerk (Variance or mean jerk)
        long_jerk = group['accx'].diff().fillna(0).abs().mean()
        
        metrics.append({
            'segment_id': segment_id,
            'steering_entropy': steering_entropy,
            'throttle_jerk': throttle_jerk,
            'brake_panic': brake_panic,
            'lat_instability': lat_instability,
            'long_jerk': long_jerk,
            'avg_dist': group['Laptrigger_lapdist_dls'].mean() # For plotting
        })
        
    return pd.DataFrame(metrics)

if __name__ == "__main__":
    # Test stub
    pass
