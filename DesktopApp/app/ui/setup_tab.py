
"""
Setup Tab - Project setup and configuration
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, 
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QProgressDialog,
    QGroupBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Slot, QTimer

class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.api_endpoint = QLineEdit(self.config.api_endpoint)
        form_layout.addRow("API Endpoint:", self.api_endpoint)
        
        self.camera_index = QSpinBox()
        self.camera_index.setMinimum(0)
        self.camera_index.setMaximum(10)
        self.camera_index.setValue(self.config.camera_index)
        form_layout.addRow("Camera Index:", self.camera_index)
        
        self.default_project_name = QLineEdit(self.config.default_project_name)
        form_layout.addRow("Default Project Name:", self.default_project_name)
        
        self.default_epochs = QSpinBox()
        self.default_epochs.setMinimum(1)
        self.default_epochs.setMaximum(100)
        self.default_epochs.setValue(self.config.default_epochs)
        form_layout.addRow("Default Epochs:", self.default_epochs)
        
        self.default_batch_size = QSpinBox()
        self.default_batch_size.setMinimum(1)
        self.default_batch_size.setMaximum(128)
        self.default_batch_size.setValue(self.config.default_batch_size)
        form_layout.addRow("Default Batch Size:", self.default_batch_size)
        
        self.default_learning_rate = QDoubleSpinBox()
        self.default_learning_rate.setDecimals(6)
        self.default_learning_rate.setMinimum(0.000001)
        self.default_learning_rate.setMaximum(0.1)
        self.default_learning_rate.setSingleStep(0.0001)
        self.default_learning_rate.setValue(self.config.default_learning_rate)
        form_layout.addRow("Default Learning Rate:", self.default_learning_rate)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        """Save settings when OK is clicked"""
        self.config.api_endpoint = self.api_endpoint.text()
        self.config.camera_index = self.camera_index.value()
        self.config.default_project_name = self.default_project_name.text()
        self.config.default_epochs = self.default_epochs.value()
        self.config.default_batch_size = self.default_batch_size.value()
        self.config.default_learning_rate = self.default_learning_rate.value()
        
        self.config.save_config()
        
        super().accept()

class ProjectDialog(QDialog):
    """Dialog for creating a new project"""
    
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Create New Project")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.project_name = QLineEdit(self.config.default_project_name)
        form_layout.addRow("Project Name:", self.project_name)
        
        layout.addLayout(form_layout)
        
        layout.addWidget(QLabel("This will create a new project with the necessary folders."))
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class SetupTab(QWidget):
    """Setup tab for project creation and management"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        self.model_service = main_window.model_service
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        projects_group = QGroupBox("Projects")
        projects_layout = QVBoxLayout(projects_group)
        
        self.project_list = QListWidget()
        self.project_list.itemDoubleClicked.connect(self.on_project_selected)
        projects_layout.addWidget(self.project_list)
        
        project_buttons_layout = QHBoxLayout()
        
        self.new_project_button = QPushButton("New Project")
        self.new_project_button.clicked.connect(self.create_project)
        project_buttons_layout.addWidget(self.new_project_button)
        
        self.open_project_button = QPushButton("Open Project")
        self.open_project_button.clicked.connect(self.open_project)
        project_buttons_layout.addWidget(self.open_project_button)
        
        self.delete_project_button = QPushButton("Delete Project")
        self.delete_project_button.clicked.connect(self.delete_project)
        project_buttons_layout.addWidget(self.delete_project_button)
        
        self.refresh_projects_button = QPushButton("Refresh")
        self.refresh_projects_button.clicked.connect(self.refresh_projects)
        project_buttons_layout.addWidget(self.refresh_projects_button)
        
        projects_layout.addLayout(project_buttons_layout)
        
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        api_layout = QFormLayout()
        self.api_endpoint_label = QLabel(self.config.api_endpoint)
        api_layout.addRow("API Endpoint:", self.api_endpoint_label)
        
        api_buttons_layout = QHBoxLayout()
        
        self.settings_button = QPushButton("Edit Settings")
        self.settings_button.clicked.connect(self.show_settings)
        api_buttons_layout.addWidget(self.settings_button)
        
        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_api_connection)
        api_buttons_layout.addWidget(self.test_connection_button)
        
        settings_layout.addLayout(api_layout)
        settings_layout.addLayout(api_buttons_layout)
        
        layout.addWidget(projects_group, 2)
        layout.addWidget(settings_group, 1)
        
        layout.addStretch()
        
        self.refresh_projects()
    
    def refresh_projects(self):
        """Refresh the list of projects"""
        self.project_list.clear()
        
        projects = self.model_service.list_projects()
        
        for project in projects:
            item = QListWidgetItem(project['name'])
            item.setData(Qt.UserRole, project)
            self.project_list.addItem(item)
    
    def create_project(self):
        """Show dialog to create a new project"""
        dialog = ProjectDialog(self, self.config)
        
        if dialog.exec():
            project_name = dialog.project_name.text().strip()
            
            if not project_name:
                self.main_window.show_error_message("Error", "Project name cannot be empty")
                return
            
            project_path = self.config.get_project_path(project_name)
            if os.path.exists(project_path):
                self.main_window.show_error_message(
                    "Error", 
                    f"Project '{project_name}' already exists"
                )
                return
            
            try:
                self.main_window.show_status_message(f"Creating project '{project_name}'...")
                project_path = self.model_service.create_project_structure(project_name)
                
                self.main_window.show_status_message(f"Project '{project_name}' created", 5000)
                self.refresh_projects()
                
                self.main_window.set_current_project(project_name, project_path)
                
                self.main_window.tab_widget.setCurrentIndex(1)
                
            except Exception as e:
                self.main_window.show_error_message("Error", f"Failed to create project: {str(e)}")
    
    def open_project(self):
        """Open a selected project"""
        selected_items = self.project_list.selectedItems()
        
        if not selected_items:
            self.main_window.show_warning_message(
                "Warning", 
                "Please select a project to open"
            )
            return
        
        self.on_project_selected(selected_items[0])
    
    def delete_project(self):
        """Delete a selected project"""
        selected_items = self.project_list.selectedItems()
        
        if not selected_items:
            self.main_window.show_warning_message(
                "Warning", 
                "Please select a project to delete"
            )
            return
        
        project_data = selected_items[0].data(Qt.UserRole)
        project_name = project_data['name']
        project_path = project_data['path']
        
        confirm = self.main_window.confirm_action(
            "Delete Project",
            f"Are you sure you want to delete project '{project_name}'?\n\n"
            "This will permanently delete all project files, models, and data.\n"
            "This action cannot be undone."
        )
        
        if not confirm:
            return
        
        try:
            if (self.main_window.current_project and 
                self.main_window.current_project['path'] == project_path):
                self.main_window.current_project = None
                self.main_window.project_label.setText("No project selected")
                self.main_window.update_tabs_state()
            
            import shutil
            shutil.rmtree(project_path)
            
            self.main_window.show_status_message(f"Project '{project_name}' deleted", 5000)
            
            self.refresh_projects()
            
        except Exception as e:
            self.main_window.show_error_message(
                "Error",
                f"Failed to delete project: {str(e)}"
            )
    
    def on_project_selected(self, item):
        """Handle project selection"""
        project_data = item.data(Qt.UserRole)
        
        self.main_window.set_current_project(project_data['name'], project_data['path'])
        
        self.main_window.show_status_message(f"Project '{project_data['name']}' opened", 5000)
    
    def test_api_connection(self):
        """Test connection to the API server"""
        self.main_window.api_service.connection_error = False
        self.main_window.api_service.last_error_time = None
        
        self.main_window.show_status_message("Testing API connection...", 3000)
        
        
        
        timeout_timer = QTimer(self)
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(lambda: handle_timeout())
        timeout_timer.start(10000) 
        
        def handle_response(endpoint, success, data):
            if 'api/health' not in endpoint:
                return
                
            self.main_window.api_service.request_finished.disconnect(handle_response)
            timeout_timer.stop()
            if success:
                self.main_window.show_info_message(
                    "Connection Successful",
                    f"Successfully connected to API server at: {self.config.api_endpoint}"
                )
        
        def handle_timeout():
            try:
                self.main_window.api_service.request_finished.disconnect(handle_response)
            except:
                pass 
            
            self.main_window.show_error_message(
                "Connection Failed",
                f"Connection to {self.config.api_endpoint} timed out. Please check the API endpoint and try again."
            )
        
        self.main_window.api_service.request_finished.connect(handle_response)
        
        self.main_window.api_service.health_check()
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self, self.config)
        
        if self.main_window.api_service.connection_error:
            from PySide6.QtWidgets import QMessageBox
            
            warning = QMessageBox(self)
            warning.setIcon(QMessageBox.Warning)
            warning.setWindowTitle("API Connection Issue")
            warning.setText("There is currently a connection issue with the API server.")
            warning.setInformativeText(
                "You can edit your API settings to fix the connection problem.\n"
                "After changing the settings, use the 'Test Connection' button to verify."
            )
            warning.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            
            result = warning.exec()
            if result == QMessageBox.Cancel:
                return
        
        if dialog.exec():
            self.api_endpoint_label.setText(self.config.api_endpoint)
            
            self.main_window.api_service.set_api_url(self.config.api_endpoint)
            
            self.main_window.api_service.reset_connection()
            
            self.main_window.show_status_message("Settings saved", 3000)