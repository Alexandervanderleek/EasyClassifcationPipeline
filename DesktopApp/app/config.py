#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Application configuration and settings
"""

import os
import json
from pathlib import Path

class AppConfig:
    """Handles application configuration and settings"""
    
    def __init__(self):
        # Default configuration values
        self.api_endpoint = os.getenv("API_URL", "http://awseb--awseb-kebw5lnvlcta-858866289.eu-west-1.elb.amazonaws.com")
        self.camera_index = 0
        self.default_project_name = "my_classifier"
        self.default_epochs = 10
        self.default_batch_size = 32
        self.default_learning_rate = 0.0001
        self.api_key = os.getenv("API_KEY", "alexsnewsecretkey")
        
        # Paths
        self.user_home = str(Path.home())
        self.base_dir = os.path.join(self.user_home, "classifier_projects")
        self.config_file = os.path.join(self.user_home, ".classifier_config.json")
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Load saved configuration if available
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update configuration
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config_data = {
                "api_endpoint": self.api_endpoint,
                "camera_index": self.camera_index,
                "default_project_name": self.default_project_name,
                "default_epochs": self.default_epochs,
                "default_batch_size": self.default_batch_size,
                "default_learning_rate": self.default_learning_rate
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
                
            return True
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
            return False

    def get_project_path(self, project_name):
        """Get full path to project directory"""
        return os.path.join(self.base_dir, project_name)