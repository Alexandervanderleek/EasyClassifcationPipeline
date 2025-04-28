#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classifier Desktop Application - Main Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.config import AppConfig

def main():
    """Application entry point"""
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("ML Classifier Trainer")
    app.setOrganizationName("ClassifierProject")
    
    # Load application configuration
    config = AppConfig()
    
    # Create and show the main window
    main_window = MainWindow(config)
    main_window.show()
    
    app.aboutToQuit.connect(lambda: cleanup(main_window))
    # Start the event loop
    sys.exit(app.exec())

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