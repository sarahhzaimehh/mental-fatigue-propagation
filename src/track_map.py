import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

def plot_track_map(df):
    """
    Generates the track map figure.
    """
    # Create custom colormap: Blue (Low) -> Yellow (Med) -> Red (High)
    colors = ["blue", "yellow", "red"]
    cmap = LinearSegmentedColormap.from_list("fatigue_cmap", colors)

    # Prepare data for LineCollection
    # Points are (longitude, latitude) - which are actually X, Y proxies
    # Center the map (using min subtraction as requested)
    x_raw = df['longitude']
    y_raw = df['latitude']
    
    # Smooth the signals
    # Check if we have enough data for rolling window
    window = 20
    if len(df) > window:
        x = x_raw.rolling(window, center=True).mean().bfill().ffill().values
        y = y_raw.rolling(window, center=True).mean().bfill().ffill().values
    else:
        x = x_raw.values
        y = y_raw.values
    
    x = x - x.min()
    y = y - y.min()
    
    # Rotate by 30 degrees
    theta = np.radians(30)
    x_rot = x * np.cos(theta) - y * np.sin(theta)
    y_rot = x * np.sin(theta) + y * np.cos(theta)
    
    # Scale coordinates (Normalize to 0-1)
    if x_rot.max() != 0:
        x_rot = x_rot / x_rot.max()
    if y_rot.max() != 0:
        y_rot = y_rot / y_rot.max()
        
    # Stretch Y slightly
    y_rot = y_rot * 1.3
    
    # Use rotated and scaled coordinates
    x = x_rot
    y = y_rot
    
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create figure with dark background
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(12, 10), facecolor='#111111')
    ax = plt.gca()
    ax.set_facecolor('#111111')
    
    # Create LineCollection
    # We color by CLI_smooth.
    lc = LineCollection(segments, cmap=cmap, norm=plt.Normalize(0, 1))
    lc.set_array(df['CLI_smooth'].iloc[:-1])
    lc.set_linewidth(5) # Thicker line
    
    ax.add_collection(lc)
    
    # Auto scale limits
    ax.autoscale()
    ax.set_aspect('equal', 'box') 

    # Add colorbar
    cbar = plt.colorbar(lc, ax=ax, shrink=0.7)
    cbar.set_label('Cognitive Load Index (CLI)', color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

    # Labels and Title
    vehicle_id = df['vehicle_id'].iloc[0] if 'vehicle_id' in df.columns else 'Unknown'
    lap_num = df['lap'].iloc[0] if 'lap' in df.columns else '?'
    
    # Get Lap Time if available
    lap_time_str = ""
    if 'lap_time' in df.columns and not pd.isna(df['lap_time'].iloc[0]):
        lap_time_str = f" | Lap Time: {df['lap_time'].iloc[0]}"
        
    plt.title(f"Driver {vehicle_id} Cognitive Load Map - COTA (Lap {lap_num}{lap_time_str})", color='white', fontsize=14, pad=20)
    plt.text(0.5, 1.02, "Dead-reckoning reconstruction (no GPS available)", 
             transform=ax.transAxes, ha='center', va='bottom', color='#aaaaaa', fontsize=10)
    
    # Configure axis labels but hide ticks and spines for clean look
    plt.xlabel('Track X (normalized)', color='white')
    plt.ylabel('Track Y (normalized)', color='white')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.grid(False)
    
    # Add Section Markers (approximate)
    if 'section_id' in df.columns:
        for i in range(0, len(df), len(df)//10):
            row = df.iloc[i]
            # Use the smoothed and normalized coordinates
            plt.text(x[i], y[i], str(int(row['section_id'])), 
                     fontsize=8, color='white', ha='center', va='center', 
                     bbox=dict(facecolor='#333333', alpha=0.7, edgecolor='none', pad=1))

    # Highlight Top 3 High Load Segments
    # Use nlargest to get indices of top 3 values
    top_3 = df['CLI_smooth'].nlargest(3)
    
    for rank, (idx, val) in enumerate(top_3.items(), 1):
        # Ensure idx is within bounds of x/y (it should be as they come from df)
        if idx < len(x):
            # Plot marker
            plt.plot(x[idx], y[idx], 'o', color='#ff0000', markersize=12, markeredgecolor='white', markeredgewidth=2, zorder=10)
            
            # Add label with some offset
            plt.annotate(f"High Load #{rank}\n({val:.2f})", 
                         xy=(x[idx], y[idx]), 
                         xytext=(10, 10), textcoords='offset points',
                         fontsize=9, color='white', fontweight='bold',
                         arrowprops=dict(arrowstyle='->', color='white'),
                         bbox=dict(facecolor='#ff0000', alpha=0.8, edgecolor='none', pad=3),
                         zorder=11)

    return fig
