"""
Main application window
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar,
    QMessageBox, QToolBar, QLabel
)
from PySide6.QtCore import Qt, Slot, QSettings, QSize
from PySide6.QtGui import QAction, QIcon
from app.ui.components import LoadingOverlay

from app.ui.setup_tab import SetupTab
from app.ui.collect_tab import CollectTab
from app.ui.train_tab import TrainTab
from app.ui.deploy_tab import DeployTab
from app.ui.devices_tab import DevicesTab
from app.ui.models_tab import ModelsTab
from app.ui.results_tab import ResultsTab
from app.services.api_service import ApiService
from app.services.model_service import ModelService

class MainWindow(QMainWindow):
    """Main application window with tabs for different operations"""
    
    def __init__(self, config):
        super().__init__()
        
        self.config = config
        self.current_project = None
        
        self.api_service = ApiService(config)
        self.model_service = ModelService(config)
        
        self.api_service.request_finished.connect(self.on_api_request_finished)
        
        self.setup_ui()
        
        self.restore_window_state()
        
    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("ML Classifier Trainer")
        self.setMinimumSize(900, 700)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        self.setCentralWidget(central_widget)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        main_layout.addWidget(self.tab_widget)
        
        self.setup_tab = SetupTab(self)
        self.collect_tab = CollectTab(self)
        self.train_tab = TrainTab(self)
        self.deploy_tab = DeployTab(self)
        self.devices_tab = DevicesTab(self)
        self.results_tab = ResultsTab(self)
        self.models_tab = ModelsTab(self)
        
        self.tab_widget.addTab(self.setup_tab, "Setup")
        self.tab_widget.addTab(self.collect_tab, "Collect Images")
        self.tab_widget.addTab(self.train_tab, "Train Model")
        self.tab_widget.addTab(self.deploy_tab, "Deploy Model")
        self.tab_widget.addTab(self.models_tab, "Models")
        self.tab_widget.addTab(self.devices_tab, "Devices")
        self.tab_widget.addTab(self.results_tab, "Results")
        
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.project_label = QLabel("No project selected")
        self.status_bar.addPermanentWidget(self.project_label)
        
        self.setup_toolbar()
        
        self.update_tabs_state()

        self.loading_overlay = LoadingOverlay(self.centralWidget())
        self.loading_overlay.hide()
        
        self.api_service.request_started.connect(self.on_api_request_started)
        self.api_service.request_finished.connect(self.on_api_request_finished)
        self.api_service.request_error.connect(self.on_api_request_error)
        
    def setup_toolbar(self):
        """Set up the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        new_project_action = QAction("New Project", self)
        new_project_action.triggered.connect(self.setup_tab.create_project)
        toolbar.addAction(new_project_action)
        
        open_project_action = QAction("Open Project", self)
        open_project_action.triggered.connect(self.setup_tab.open_project)
        toolbar.addAction(open_project_action)
        
        toolbar.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.setup_tab.show_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        toolbar.addAction(refresh_action)
    
    def refresh_current_tab(self):
        """Refresh the current tab"""
        current_tab = self.tab_widget.currentWidget()
        
        if hasattr(current_tab, 'on_tab_selected'):
            current_tab.on_tab_selected()
    
    def save_window_state(self):
        """Save window geometry and state"""
        settings = QSettings("ClassifierProject", "ML Classifier Trainer")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        
    def restore_window_state(self):
        """Restore window geometry and state"""
        settings = QSettings("ClassifierProject", "ML Classifier Trainer")
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
    
    @Slot(str, str)
    def on_api_request_error(self, endpoint, error_message):
        """Handle API request error signal"""
        self.hide_loading()
        self.show_error_message("API Error", error_message)

    @Slot(str)
    def on_api_request_started(self, endpoint):
        """Handle API request started signal"""
        if any(x in endpoint for x in ['register', 'create', 'upload', 'delete', 'health']):
            message = "Processing request..."
            if 'register' in endpoint:
                message = "Registering device..."
            elif 'create' in endpoint:
                message = "Creating..."
            elif 'upload' in endpoint:
                message = "Uploading..."
            elif 'health' in endpoint:
                message = "Checking connection..."
            
            self.show_loading(message)
    
    @Slot(int)
    def on_tab_changed(self, index):
        """Handle tab changed event to update tab contents"""
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if i != index and hasattr(tab, 'on_tab_deselected'):
                tab.on_tab_deselected()
        
        current_tab = self.tab_widget.widget(index)
        if hasattr(current_tab, 'on_tab_selected'):
            current_tab.on_tab_selected()
    
    def set_current_project(self, project_name, project_path):
        """Set the current active project"""
        self.current_project = {
            'name': project_name,
            'path': project_path
        }
        
        self.project_label.setText(f"Project: {project_name}")
        
        self.update_tabs_state()
        
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'on_project_changed'):
                tab.on_project_changed(project_name, project_path)
    
    def show_loading(self, message="Loading..."):
        """Show the loading overlay with a message"""
        self.loading_overlay.set_message(message)
        self.loading_overlay.resize(self.centralWidget().size())
        self.loading_overlay.show()
    
    def hide_loading(self):
        """Hide the loading overlay"""
        if self.loading_overlay and self.loading_overlay.isVisible():
            self.loading_overlay.hide()
    
    def update_tabs_state(self):
        """Enable or disable tabs based on project selection"""
        has_project = self.current_project is not None
        
        for i in range(1, self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, has_project)
    
    def show_status_message(self, message, timeout=5000):
        """Show a message in the status bar"""
        self.status_bar.showMessage(message, timeout)
    
    def show_info_message(self, title, message):
        """Show an information message box"""
        QMessageBox.information(self, title, message)
    
    def show_error_message(self, title, message):
        """Show an error message box"""
        QMessageBox.critical(self, title, message)
    
    def show_warning_message(self, title, message):
        """Show a warning message box"""
        QMessageBox.warning(self, title, message)
    
    def confirm_action(self, title, message):
        """Show a confirmation dialog and return True if confirmed"""
        reply = QMessageBox.question(
            self, title, message, 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    @Slot(str, bool, object)
    def on_api_request_finished(self, endpoint, success, data):
        """Handle API request finished signal from the ApiService"""
        if any(x in endpoint for x in ['register', 'create', 'upload', 'delete', 'health']):
            self.hide_loading()
            
        if not success:
            error_type = data.get('error_type', '')
            
            if any(err in error_type for err in ['ConnectionError', 'Timeout', 'ConnectTimeout']):
                if not data.get('is_retry_blocked', False):
                    error_message = data.get('error_message', 'Unknown connection error')
                    
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Critical)
                    msg_box.setWindowTitle("API Connection Error")
                    msg_box.setText(error_message)
                    
                    msg_box.setInformativeText(
                        "The application will automatically retry after a delay.\n"
                        "You can also check your connection and API settings, then try again."
                    )
                    
                    msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Retry)
                    msg_box.setDefaultButton(QMessageBox.Ok)
                    
                    button_clicked = msg_box.exec()
                    
                    if button_clicked == QMessageBox.Retry:
                        self.api_service.reset_connection()
                        
                        self.refresh_current_tab()

    def resizeEvent(self, event):
        """Handle resize events to resize the loading overlay"""
        if self.loading_overlay and self.loading_overlay.isVisible():
            self.loading_overlay.resize(self.centralWidget().size())
        super().resizeEvent(event)

    def closeEvent(self, event):
        """Handle application close event"""
        self.save_window_state()
        
        self.config.save_config()
        
        self.cleanup()
        
        event.accept()
        
    def cleanup(self):
        """Clean up all resources before closing"""
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'on_tab_deselected'):
                tab.on_tab_deselected()
        
        self.api_service.close()
        
        if hasattr(self.collect_tab, 'camera_service'):
            self.collect_tab.camera_service.stop_camera()