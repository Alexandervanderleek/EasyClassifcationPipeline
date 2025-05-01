#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classifier Desktop Application - Main Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.config import AppConfig
from app.ui.first_run_dialog import FirstRunDialog

def main():
    """Application entry point"""
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("ML Classifier Trainer")
    app.setOrganizationName("ClassifierProject")
    
    # Load application configuration
    config = AppConfig()
    
    # Check if this is the first run
    if config.is_first_run():
        # Show first run dialog
        dialog = FirstRunDialog()
        
        # Define callback for when setup is complete
        def on_setup_complete(api_url, api_key):
            # Update config with new credentials
            config.update_credentials(api_url, api_key)
            
            # Create and show the main window
            show_main_window(app, config)
        
        # Connect signal
        dialog.setup_complete.connect(on_setup_complete)
        
        # Show dialog
        dialog.exec()
        
        # If the dialog was closed without saving valid credentials, exit the app
        if config.is_first_run():
            print("First run setup was not completed. Exiting.")
            sys.exit(0)
    else:
        # Normal startup - show main window
        show_main_window(app, config)
    
    # Start the event loop
    sys.exit(app.exec())

def show_main_window(app, config):
    """Create and show the main window"""
    main_window = MainWindow(config)
    main_window.show()
    
    app.aboutToQuit.connect(lambda: cleanup(main_window))

def cleanup(main_window):
    """Clean up resources before exiting"""
    # Save config
    main_window.config.save_config()
    
    # Close API service
    main_window.api_service.close()
    
    # Stop any running services
    if hasattr(main_window.collect_tab, 'camera_service'):
        main_window.collect_tab.camera_service.stop_camera()

if __name__ == "__main__":
    main()