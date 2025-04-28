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
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()