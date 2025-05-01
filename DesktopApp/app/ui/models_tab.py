#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Models Tab - Manage models stored on the server
"""

import os
import requests
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QMenu, QCheckBox, QSplitter, QFileDialog
)
from PySide6.QtCore import Qt, Slot, QSize, QTimer, QRunnable, QThreadPool, QObject, Signal
from PySide6.QtGui import QAction, QColor, QFont

class DownloadWorkerSignals(QObject):
        """Signals for the DownloadWorker class"""
        finished = Signal(bool, str)  # success, result
        progress = Signal(int)  # percentage

class DownloadWorker(QRunnable):
    """Worker for downloading files in a background thread"""
    
    def __init__(self, url, file_path):
        super().__init__()
        self.url = url
        self.file_path = file_path
        self.signals = DownloadWorkerSignals()
    
    def run(self):
        try:
            import requests
            import os
            
            # Download the file
            response = requests.get(self.url, stream=True)
            
            if response.status_code != 200:
                self.signals.finished.emit(False, f"Download failed with status code {response.status_code}")
                return
            
            # Get file size for progress reporting
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
            
            # Save the file
            with open(self.file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Report progress if we know the size
                        if total_size > 0:
                            progress = int(downloaded * 100 / total_size)
                            self.signals.progress.emit(progress)
            
            self.signals.finished.emit(True, self.file_path)
        except Exception as e:
            self.signals.finished.emit(False, str(e))

class ModelDetailsPanel(QWidget):
    """Panel for showing model details"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QFormLayout(self)
        
        # Model details labels
        self.model_id_label = QLabel("N/A")
        layout.addRow("Model ID:", self.model_id_label)
        
        self.project_name_label = QLabel("N/A")
        layout.addRow("Project Name:", self.project_name_label)
        
        self.upload_date_label = QLabel("N/A")
        layout.addRow("Upload Date:", self.upload_date_label)
        
        self.active_devices_label = QLabel("N/A")
        layout.addRow("Active Devices:", self.active_devices_label)
        
        # Add action buttons
        actions_layout = QHBoxLayout()
        
        self.view_devices_button = QPushButton("View Devices")
        self.view_devices_button.setEnabled(False)
        actions_layout.addWidget(self.view_devices_button)
        
        self.download_button = QPushButton("Download")
        self.download_button.setEnabled(False)
        actions_layout.addWidget(self.download_button)
        
        self.delete_button = QPushButton("Delete Model")
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("color: #e76f51;")  # Red color for delete button
        actions_layout.addWidget(self.delete_button)
        
        layout.addRow("Actions:", actions_layout)


class ModelsTab(QWidget):
    """Tab for managing models stored on the server"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        self.api_service = main_window.api_service
        
        # State variables
        self.models = []
        self.selected_model_id = None
        self.download_paths = {}
        
        # Set up UI
        self.setup_ui()
        
        # Connect signals
        self.api_service.request_finished.connect(self.on_request_finished)
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create a splitter for models list and details
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left widget - Models list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Models group
        models_group = QGroupBox("Available Models")
        models_layout = QVBoxLayout(models_group)
        
        # Models table
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(4)
        self.models_table.setHorizontalHeaderLabels([
            "Project Name", "Upload Date", "Active Devices", "Actions"
        ])
        self.models_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.models_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.models_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.models_table.customContextMenuRequested.connect(self.show_model_context_menu)
        self.models_table.clicked.connect(self.on_model_selected)
        
        models_layout.addWidget(self.models_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_models)
        buttons_layout.addWidget(self.refresh_button)
        
        models_layout.addLayout(buttons_layout)
        
        left_layout.addWidget(models_group)
        
        # Right widget - Model details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Model details group
        details_group = QGroupBox("Model Details")
        self.model_details_panel = ModelDetailsPanel()
        
        # Connect model detail button signals
        self.model_details_panel.view_devices_button.clicked.connect(
            lambda: self.view_model_devices(self.selected_model_id)
        )
        self.model_details_panel.download_button.clicked.connect(
            lambda: self.download_model(self.selected_model_id)
        )
        self.model_details_panel.delete_button.clicked.connect(
            lambda: self.delete_model(self.selected_model_id, self.get_model_name(self.selected_model_id))
        )
        
        details_layout = QVBoxLayout(details_group)
        details_layout.addWidget(self.model_details_panel)
        
        right_layout.addWidget(details_group)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Set initial splitter sizes (70% left, 30% right)
        splitter.setSizes([700, 300])
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        # Show loading indicator
        self.main_window.show_loading("Loading Models...")
        
        # Refresh models
        self.refresh_models()
    
    def refresh_models(self):
        """Refresh the list of models"""
        # Force cache clearing for models
        self.api_service.clear_cache()
        self.api_service.get_models()
    
    def get_model_name(self, model_id):
        """Get the name of a model by ID"""
        for model in self.models:
            if model['model_id'] == model_id:
                return model['project_name']
        return "Unknown Model"
    
    def view_model_devices(self, model_id):
        """View devices using this model"""
        # Get model name for better user experience
        model_name = self.get_model_name(model_id)
        
        # Show loading indicator
        self.main_window.show_loading(f"Finding devices using model '{model_name}'...")
        
        # We need to get the list of devices and filter for those using this model
        # First, clear any existing device filter in the Devices tab
        if hasattr(self.main_window.devices_tab, 'device_filter'):
            self.main_window.devices_tab.device_filter = None
        
        # Store the model_id to filter devices
        if not hasattr(self.main_window.devices_tab, 'model_filter'):
            self.main_window.devices_tab.model_filter = None
        
        self.main_window.devices_tab.model_filter = model_id
        
        # Switch to Devices tab
        self.main_window.tab_widget.setCurrentIndex(5)  # Assuming Devices is tab 5 after our changes
        
        # Force a refresh of the devices list
        QTimer.singleShot(100, lambda: self.main_window.devices_tab.refresh_devices())
    
    def download_model(self, model_id):
        """Download a model"""
        # Get model name
        model_name = self.get_model_name(model_id)
        
        # First, ask where to save the file
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Model File",
            os.path.join(os.path.expanduser("~"), f"{model_name}.tflite"),
            "TensorFlow Lite Model (*.tflite);;All Files (*)"
        )
        
        if not file_path:
            return  # User canceled
        
        # Show loading indicator
        self.main_window.show_loading(f"Downloading model '{model_name}'...")
        
        # Get download URL from the API
        self.api_service.get_model_download_url(model_id)
        
        # Store the file path for handling in the response callback
        self.download_paths[model_id] = file_path
    
    

    def handle_download_url_response(self, model_id, download_url):
        """Handle the download URL response and start the actual download"""
        if model_id not in self.download_paths:
            self.main_window.hide_loading()
            self.main_window.show_error_message("Download Error", "Download information is no longer available")
            return
        
        file_path = self.download_paths[model_id]
        
        # Create progress dialog
        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import Qt
        
        progress_dialog = QProgressDialog(f"Downloading model...", "Cancel", 0, 100, self)
        progress_dialog.setWindowTitle("Download Progress")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)  # Show immediately
        progress_dialog.setValue(0)
        
        # Create worker
        worker = DownloadWorker(download_url, file_path)
        
        # Connect signals
        worker.signals.progress.connect(progress_dialog.setValue)
        
        # Define finished handler
        def on_download_finished(success, result):
            # Hide progress dialog
            progress_dialog.close()
            
            # Hide loading indicator
            self.main_window.hide_loading()
            
            if success:
                self.main_window.show_info_message(
                    "Download Complete",
                    f"Model has been downloaded to:\n{result}"
                )
            else:
                self.main_window.show_error_message(
                    "Download Error",
                    f"Failed to download model: {result}"
                )
        
        worker.signals.finished.connect(on_download_finished)
        
        # Connect cancel button
        progress_dialog.canceled.connect(lambda: progress_dialog.close())
        
        # Start worker
        QThreadPool.globalInstance().start(worker)
        
        # Hide the main loading indicator since we have a progress dialog
        self.main_window.hide_loading()
    
    def delete_model(self, model_id, model_name):
        """Delete a model"""
        # Ask for confirmation first
        hard_delete = False
        
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Warning)
        message_box.setWindowTitle("Delete Model")
        message_box.setText(f"Are you sure you want to delete model '{model_name}'?")
        message_box.setInformativeText("This will remove the model from all devices using it.")
        
        # Add hard delete checkbox
        hard_delete_checkbox = QCheckBox("Permanently delete (including files from storage)")
        message_box.setCheckBox(hard_delete_checkbox)
        
        # Add buttons
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message_box.setDefaultButton(QMessageBox.No)
        
        # Show dialog
        if message_box.exec() != QMessageBox.Yes:
            return
        
        # Get hard delete option
        hard_delete = hard_delete_checkbox.isChecked()
        
        # Show loading indicator
        self.main_window.show_loading(f"Deleting model {model_name}...")
        
        # Make API request to delete model
        self.api_service.delete_model(model_id, hard_delete)
    
    def update_models_table(self):
        """Update the models table with current data"""
        self.models_table.setRowCount(0)
        
        for i, model in enumerate(self.models):
            self.models_table.insertRow(i)
            
            # Project Name
            self.models_table.setItem(i, 0, QTableWidgetItem(model['project_name']))
            
            # Upload Date
            upload_date = model.get('upload_date', '')
            try:
                date_obj = datetime.fromisoformat(upload_date)
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_date = upload_date
                
            self.models_table.setItem(i, 1, QTableWidgetItem(formatted_date))
            
            # Active Devices
            self.models_table.setItem(i, 2, QTableWidgetItem(str(model.get('active_devices', 0))))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            
            delete_button = QPushButton("Delete")
            delete_button.setProperty("model_id", model['model_id'])
            delete_button.setProperty("model_name", model['project_name'])
            delete_button.clicked.connect(lambda checked, btn=delete_button: 
                self.delete_model(btn.property("model_id"), btn.property("model_name")))
            
            download_button = QPushButton("Download")
            download_button.setProperty("model_id", model['model_id'])
            download_button.clicked.connect(lambda checked, btn=download_button: 
                self.download_model(btn.property("model_id")))
            
            actions_layout.addWidget(download_button)
            actions_layout.addWidget(delete_button)
            
            self.models_table.setCellWidget(i, 3, actions_widget)
        
        # If a model was selected, update its details
        if self.selected_model_id:
            self.update_model_details(self.selected_model_id)
    
    def on_model_selected(self, index):
        """Handle model selection in the table"""
        row = index.row()
        if row >= 0 and row < len(self.models):
            self.selected_model_id = self.models[row]['model_id']
            self.update_model_details(self.selected_model_id)
    
    def update_model_details(self, model_id):
        """Update the model details panel"""
        model = next((m for m in self.models if m['model_id'] == model_id), None)
        if not model:
            # Clear details if model not found
            self.model_details_panel.model_id_label.setText("N/A")
            self.model_details_panel.project_name_label.setText("N/A")
            self.model_details_panel.upload_date_label.setText("N/A")
            self.model_details_panel.active_devices_label.setText("N/A")
            self.model_details_panel.view_devices_button.setEnabled(False)
            self.model_details_panel.download_button.setEnabled(False)
            self.model_details_panel.delete_button.setEnabled(False)
            return
        
        # Update details
        self.model_details_panel.model_id_label.setText(model['model_id'])
        self.model_details_panel.project_name_label.setText(model['project_name'])
        
        # Format upload date
        upload_date = model.get('upload_date', '')
        try:
            date_obj = datetime.fromisoformat(upload_date)
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
        except:
            formatted_date = upload_date
            
        self.model_details_panel.upload_date_label.setText(formatted_date)
        
        # Active devices
        self.model_details_panel.active_devices_label.setText(str(model.get('active_devices', 0)))
        
        # Enable buttons
        self.model_details_panel.view_devices_button.setEnabled(True)
        self.model_details_panel.download_button.setEnabled(True)
        self.model_details_panel.delete_button.setEnabled(True)
    
    def show_model_context_menu(self, pos):
        """Show context menu for model table"""
        # Get the selected row
        selected_indexes = self.models_table.selectedIndexes()
        if not selected_indexes:
            return
        
        # Get the model for the selected row
        row = selected_indexes[0].row()
        if row < 0 or row >= len(self.models):
            return
            
        model_id = self.models[row]['model_id']
        model_name = self.models[row]['project_name']
        
        # Create menu
        menu = QMenu(self)
        
        # Add actions
        view_devices_action = QAction("View Devices", self)
        view_devices_action.triggered.connect(lambda: self.view_model_devices(model_id))
        menu.addAction(view_devices_action)
        
        download_action = QAction("Download Model", self)
        download_action.triggered.connect(lambda: self.download_model(model_id))
        menu.addAction(download_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add delete action
        delete_action = QAction("Delete Model", self)
        delete_action.triggered.connect(lambda: self.delete_model(model_id, model_name))
        menu.addAction(delete_action)
        
        # Show menu
        menu.exec(self.models_table.viewport().mapToGlobal(pos))
    
    # Signal handlers
    
    @Slot(str, bool, object)
    def on_request_finished(self, endpoint, success, data):
        """Handle API request finished"""
        if 'api/models' in endpoint and not 'create' in endpoint and success and 'models' in data:
            # Update models list
            self.models = data['models']
            self.update_models_table()
            self.main_window.hide_loading()
        
        elif 'api/models/' in endpoint and 'delete' in endpoint and success:
            # Show success message
            self.main_window.show_info_message(
                "Model Deleted",
                "Model deleted successfully"
            )
            
            # If this is the currently selected model, clear selection
            if self.selected_model_id in endpoint:
                self.selected_model_id = None
            
            # Refresh models
            self.refresh_models()
        
        elif 'api/models/' in endpoint and 'download' in endpoint and success:
            # Handle download URL response
            if success and data.get('success') and data.get('download_url'):
                model_id = endpoint.split('/')[2]  # Extract model_id from endpoint
                self.handle_download_url_response(model_id, data['download_url'])
            else:
                self.main_window.hide_loading()
                error_msg = data.get('error', 'Unknown error')
                self.main_window.show_error_message("Download Error", f"Failed to get download URL: {error_msg}")