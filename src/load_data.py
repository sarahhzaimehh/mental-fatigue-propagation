import pandas as pd
import os
import glob

def scan_data_directory(data_dir='data'):
    """
    Scans the data directory for required files.
    Returns a dictionary with file paths.
    """
    files = {
        'telemetry': None,
        'analysis': None,
        'weather': None,
        'lap_time': None
    }
    
    # Search patterns
    patterns = {
        'telemetry': '*telemetry_data.csv',
        'analysis': '*AnalysisEndurance*.CSV', # Case sensitive check might be needed
        'weather': '*Weather*.CSV',
        'lap_time': '*lap_time*.csv'
    }
    
    for key, pattern in patterns.items():
        # Case insensitive search
        matches = glob.glob(os.path.join(data_dir, pattern)) + \
                  glob.glob(os.path.join(data_dir, pattern.lower())) + \
                  glob.glob(os.path.join(data_dir, pattern.upper()))
        
        # Also search recursively in subdirectories (like "Race 1")
        if not matches:
             matches = glob.glob(os.path.join(data_dir, '**', pattern), recursive=True) + \
                       glob.glob(os.path.join(data_dir, '**', pattern.lower()), recursive=True) + \
                       glob.glob(os.path.join(data_dir, '**', pattern.upper()), recursive=True)

        if matches:
            files[key] = matches[0] # Pick the first match
            
    return files

def get_available_vehicles(telemetry_file):
    """
    Scans the telemetry file for unique vehicle_ids.
    Reads in chunks to be memory efficient.
    """
    if not telemetry_file or not os.path.exists(telemetry_file):
        return []
        
    unique_vehicles = set()
    try:
        # Read only vehicle_id column
        # Note: The file might be headerless or have malformed header as discovered before.
        # We'll try to detect header or use the known column names from process_telemetry.py
        
        # Known columns from previous exploration
        names = ['expire_at', 'lap', 'meta_event', 'meta_session', 'meta_source', 'meta_time', 
                 'original_vehicle_id', 'outing', 'telemetry_name', 'telemetry_value', 
                 'timestamp', 'vehicle_id', 'vehicle_number']
                 
        # Try reading first few lines to check header
        with open(telemetry_file, 'r') as f:
            first_line = f.readline()
            
        has_header = 'vehicle_id' in first_line
        
        chunk_size = 100000
        read_args = {
            'chunksize': chunk_size,
            'usecols': ['vehicle_id'],
            'on_bad_lines': 'skip'
        }
        
        if not has_header:
            read_args['names'] = names
            read_args['header'] = 0 # Skip the first line if it's garbage/data treated as header
        
        for chunk in pd.read_csv(telemetry_file, **read_args):
            if 'vehicle_id' in chunk.columns:
                unique_vehicles.update(chunk['vehicle_id'].dropna().unique())
                
    except Exception as e:
        print(f"Error scanning vehicles: {e}")
        return []
        
    return sorted(list(unique_vehicles))

def get_available_laps(telemetry_file, vehicle_id):
    """
    Scans for available laps for a specific vehicle.
    """
    if not telemetry_file or not os.path.exists(telemetry_file):
        return []
        
    unique_laps = set()
    try:
        names = ['expire_at', 'lap', 'meta_event', 'meta_session', 'meta_source', 'meta_time', 
                 'original_vehicle_id', 'outing', 'telemetry_name', 'telemetry_value', 
                 'timestamp', 'vehicle_id', 'vehicle_number']
                 
        with open(telemetry_file, 'r') as f:
            first_line = f.readline()
        has_header = 'vehicle_id' in first_line
        
        read_args = {
            'chunksize': 100000,
            'usecols': ['vehicle_id', 'lap'],
            'on_bad_lines': 'skip'
        }
        
        if not has_header:
            read_args['names'] = names
            read_args['header'] = 0
            
        for chunk in pd.read_csv(telemetry_file, **read_args):
            if 'vehicle_id' in chunk.columns and 'lap' in chunk.columns:
                laps = chunk[chunk['vehicle_id'] == vehicle_id]['lap'].dropna().unique()
                unique_laps.update(laps)
                
    except Exception as e:
        print(f"Error scanning laps: {e}")
        return []
        
    return sorted(list(unique_laps))

def load_telemetry(file_path):
    """
    Legacy function for loading cleaned telemetry.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    df = pd.read_csv(file_path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df
