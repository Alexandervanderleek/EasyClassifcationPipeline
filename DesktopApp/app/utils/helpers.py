"""
Utils Package - Utility functions and helpers
"""

from datetime import datetime, timedelta

def format_time_ago(timestamp_str):
    """Format a timestamp as a human-readable 'time ago' string"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        
        if (now - timestamp) < timedelta(minutes=5):
            return "Just now"
        elif (now - timestamp) < timedelta(hours=1):
            minutes = (now - timestamp).seconds // 60
            return f"{minutes} min ago"
        elif (now - timestamp) < timedelta(days=1):
            hours = (now - timestamp).seconds // 3600
            return f"{hours} hours ago"
        else:
            days = (now - timestamp).days
            return f"{days} days ago"
    except:
        return "Unknown"

def validate_model_files(project_path):
    """Check if model files exist and return status"""
    import os
    
    model_h5_path = os.path.join(project_path, "models", "model.h5")
    tflite_path = os.path.join(project_path, "models", "model.tflite")
    metadata_path = os.path.join(project_path, "models", "metadata.json")
    
    return {
        'has_model': os.path.exists(model_h5_path),
        'has_tflite': os.path.exists(tflite_path),
        'has_metadata': os.path.exists(metadata_path),
        'model_path': model_h5_path if os.path.exists(model_h5_path) else None,
        'tflite_path': tflite_path if os.path.exists(tflite_path) else None,
        'metadata_path': metadata_path if os.path.exists(metadata_path) else None
    }