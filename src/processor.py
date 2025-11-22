import pandas as pd
import numpy as np

def process_lap_data(telemetry_file, vehicle_id, lap):
    """
    Processes raw telemetry for a specific vehicle and lap.
    Performs pivoting, cleaning, and dead reckoning.
    """
    print(f"Processing {vehicle_id} Lap {lap} from {telemetry_file}...")
    
    # Column names for raw data (based on known format)
    names = ['expire_at', 'lap', 'meta_event', 'meta_session', 'meta_source', 'meta_time', 
             'original_vehicle_id', 'outing', 'telemetry_name', 'telemetry_value', 
             'timestamp', 'vehicle_id', 'vehicle_number']
    
    # 1. Load and Filter Data
    chunks = []
    chunk_size = 100000
    
    # Check header
    with open(telemetry_file, 'r') as f:
        first_line = f.readline()
    has_header = 'vehicle_id' in first_line
    
    read_args = {
        'chunksize': chunk_size,
        'on_bad_lines': 'skip',
        'low_memory': False
    }
    if not has_header:
        read_args['names'] = names
        read_args['header'] = 0
        
    for chunk in pd.read_csv(telemetry_file, **read_args):
        # Filter by vehicle and lap
        if 'vehicle_id' in chunk.columns and 'lap' in chunk.columns:
            filtered = chunk[
                (chunk['vehicle_id'] == vehicle_id) & 
                (chunk['lap'] == lap)
            ]
            if not filtered.empty:
                chunks.append(filtered)
                
    if not chunks:
        raise ValueError(f"No data found for {vehicle_id} Lap {lap}")
        
    df_raw = pd.concat(chunks)
    
    # 2. Pivot Data
    # We need 'timestamp' as index, 'telemetry_name' as columns, 'telemetry_value' as values
    # Also keep 'vehicle_id', 'lap', 'vehicle_number'
    
    # Ensure timestamp is datetime
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
    
    # Pivot
    df_pivot = df_raw.pivot_table(
        index=['timestamp', 'vehicle_id', 'lap'], 
        columns='telemetry_name', 
        values='telemetry_value',
        aggfunc='first' # Handle duplicates
    ).reset_index()
    
    # Forward fill / Backward fill to handle async signals
    df_pivot = df_pivot.sort_values('timestamp').ffill().bfill()
    
    # 3. Rename Columns to Standard Names
    # Map raw names to standard names used in pipeline
    # Standard: Steering_Angle, throttle, brake_pressure, accx, accy, speed
    rename_map = {
        'ath': 'throttle',
        'pbrake_f': 'brake_pressure',
        'accx_can': 'accx',
        'accy_can': 'accy',
        'Steering_Angle': 'Steering_Angle', # Already good
        'speed': 'speed'
    }
    df_pivot = df_pivot.rename(columns=rename_map)
    
    # Ensure all required columns exist
    required_cols = ['Steering_Angle', 'throttle', 'brake_pressure', 'accx', 'accy', 'speed']
    for col in required_cols:
        if col not in df_pivot.columns:
            df_pivot[col] = 0.0 # Fill missing with 0
            
    # 4. Normalize Signals
    # Steering: -450 to 450 -> -1 to 1 (approx)
    df_pivot['Steering_Angle'] = df_pivot['Steering_Angle'] / 450.0
    
    # Throttle: 0 to 100 -> 0 to 1
    if df_pivot['throttle'].max() > 1.0:
        df_pivot['throttle'] = df_pivot['throttle'] / 100.0
        
    # Brake: Normalize by max observed
    if df_pivot['brake_pressure'].max() > 0:
        df_pivot['brake_pressure'] = df_pivot['brake_pressure'] / df_pivot['brake_pressure'].max()
        
    # 5. Dead Reckoning (Track Map)
    # Calculate X, Y from Speed and Steering
    
    # Parameters for GR86 (Approx)
    L = 2.57 # Wheelbase
    steering_ratio = 13.5
    
    # Time delta
    df_pivot['dt'] = df_pivot['timestamp'].diff().dt.total_seconds().fillna(0)
    
    # Wheel angle (rad)
    # Steering_Angle is normalized -1 to 1, so revert to deg then to rad? 
    # Wait, we normalized it above. Let's use the raw-ish value (deg)
    # Actually, let's revert normalization for physics calc
    steer_deg = df_pivot['Steering_Angle'] * 450.0
    wheel_angle = np.radians(steer_deg / steering_ratio)
    
    # Speed (m/s) - assuming input is km/h? Or m/s? 
    # Usually speed in CAN is km/h. Let's check max value.
    if df_pivot['speed'].max() > 100: # Likely km/h
        speed_ms = df_pivot['speed'] / 3.6
    else:
        speed_ms = df_pivot['speed']
        
    # Yaw Rate (rad/s)
    # yaw_rate = v / L * tan(delta)
    yaw_rate = (speed_ms / L) * np.tan(wheel_angle)
    
    # Heading (psi)
    heading = (yaw_rate * df_pivot['dt']).cumsum()
    
    # Velocity components
    vx = speed_ms * np.cos(heading)
    vy = speed_ms * np.sin(heading)
    
    # Position
    df_pivot['X'] = (vx * df_pivot['dt']).cumsum()
    df_pivot['Y'] = (vy * df_pivot['dt']).cumsum()
    
    # Map X/Y to longitude/latitude for compatibility with pipeline
    df_pivot['longitude'] = df_pivot['X']
    df_pivot['latitude'] = df_pivot['Y']
    
    # 6. Calculate Lap Distance (Laptrigger_lapdist_dls)
    # Integrate speed
    df_pivot['Laptrigger_lapdist_dls'] = (speed_ms * df_pivot['dt']).cumsum()
    
    return df_pivot
