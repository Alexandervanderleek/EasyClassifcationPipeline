#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper utility functions for the application
"""

import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import QProgressDialog
from PySide6.QtCore import Qt

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

def create_busy_indicator(parent, title, message, modal=True):
    """Create a busy indicator dialog"""
    progress = QProgressDialog(message, "Cancel", 0, 0, parent)
    progress.setWindowTitle(title)
    progress.setWindowModality(Qt.WindowModal if modal else Qt.NonModal)
    progress.setMinimumDuration(500)  # Show after 500ms
    progress.setValue(0)
    progress.setAutoClose(False)
    progress.setCancelButton(None)  # No cancel button
    
    return progress

def validate_model_files(project_path):
    """Check if model files exist and return status"""
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