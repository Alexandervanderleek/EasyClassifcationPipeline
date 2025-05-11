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
    app = QApplication(sys.argv)
    app.setApplicationName("ML Classifier Trainer")
    app.setOrganizationName("ClassifierProject")
    
    config = AppConfig()
    
    if config.is_first_run():
        dialog = FirstRunDialog()
        
        def on_setup_complete(api_url, api_key):
            config.update_credentials(api_url, api_key)
            
            show_main_window(app, config)
        
        dialog.setup_complete.connect(on_setup_complete)
        
        dialog.exec()
        
        if config.is_first_run():
            sys.exit(0)
    else:
        show_main_window(app, config)
    
    sys.exit(app.exec())

def show_main_window(app, config):
    """Create and show the main window"""
    main_window = MainWindow(config)
    main_window.show()
    
    app.aboutToQuit.connect(lambda: cleanup(main_window))

def cleanup(main_window):
    """Clean up resources before exiting"""
    main_window.config.save_config()
    
    main_window.api_service.close()
    
    if hasattr(main_window.collect_tab, 'camera_service'):
        main_window.collect_tab.camera_service.stop_camera()

if __name__ == "__main__":
    main()