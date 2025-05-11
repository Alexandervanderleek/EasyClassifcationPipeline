"""
Devices Tab - Manage and monitor connected devices
"""

import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QMessageBox, QMenu, QSplitter, QCheckBox
)
from PySide6.QtCore import Qt, Slot, QTimer, Signal, QSize
from PySide6.QtGui import QAction, QColor, QFont

from app.utils import format_time_ago

class RegisterDeviceDialog(QDialog):
    """Dialog for registering a new device"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Register New Device")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.device_name = QLineEdit()
        form_layout.addRow("Device Name:", self.device_name)
        
        layout.addLayout(form_layout)
        
        layout.addWidget(QLabel("This will register a new device with the server."))
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class AssignModelDialog(QDialog):
    """Dialog for assigning a model to a device"""
    
    def __init__(self, parent, device_id, device_name, models):
        super().__init__(parent)
        self.device_id = device_id
        self.device_name = device_name
        self.models = models
        
        self.setWindowTitle("Assign Model to Device")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        device_label = QLabel(f"Device: {device_name} (ID: {device_id})")
        layout.addWidget(device_label)
        
        form_layout = QFormLayout()
        
        self.model_combo = QComboBox()
        for model in models:
            self.model_combo.addItem(model['project_name'], model['model_id'])
        
        form_layout.addRow("Select Model:", self.model_combo)
        
        layout.addLayout(form_layout)
        
        layout.addWidget(QLabel("This will assign the selected model to the device."))
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_selected_model_id(self):
        """Get the selected model ID"""
        return self.model_combo.currentData()

class DeviceDetailsPanel(QWidget):
    """Panel for showing device details"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QFormLayout(self)
        
        self.device_id_label = QLabel("N/A")
        layout.addRow("Device ID:", self.device_id_label)
        
        self.device_name_label = QLabel("N/A")
        layout.addRow("Device Name:", self.device_name_label)
        
        self.device_status_label = QLabel("N/A")
        layout.addRow("Status:", self.device_status_label)
        
        self.last_active_label = QLabel("N/A")
        layout.addRow("Last Active:", self.last_active_label)
        
        self.current_model_label = QLabel("N/A")
        layout.addRow("Current Model:", self.current_model_label)
        
        actions_layout = QHBoxLayout()
        
        self.assign_model_button = QPushButton("Assign Model")
        self.assign_model_button.setEnabled(False)
        actions_layout.addWidget(self.assign_model_button)
        
        self.view_results_button = QPushButton("View Results")
        self.view_results_button.setEnabled(False)
        actions_layout.addWidget(self.view_results_button)
        
        self.delete_device_button = QPushButton("Delete Device")
        self.delete_device_button.setEnabled(False)
        self.delete_device_button.setStyleSheet("color: #e76f51;") 
        actions_layout.addWidget(self.delete_device_button)
        
        layout.addRow("Actions:", actions_layout)

class DevicesTab(QWidget):
    """Tab for managing connected devices"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        self.api_service = main_window.api_service
        
        self.devices = []
        self.models = []
        self.selected_device_id = None
        self.model_filter = None
        
        self.setup_ui()
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_devices)
        self.refresh_timer.setInterval(30000)  # 30 seconds
        
        self.api_service.request_finished.connect(self.on_request_finished)
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        devices_group = QGroupBox("Connected Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(5)
        self.devices_table.setHorizontalHeaderLabels([
            "Device Name", "Status", "Last Active", "Model", "Actions"
        ])
        self.devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.devices_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.devices_table.customContextMenuRequested.connect(self.show_device_context_menu)
        self.devices_table.clicked.connect(self.on_device_selected)
        
        devices_layout.addWidget(self.devices_table)
        
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_devices_button)
        buttons_layout.addWidget(self.refresh_button)
        
        self.register_button = QPushButton("Register New Device")
        self.register_button.clicked.connect(self.register_device)
        buttons_layout.addWidget(self.register_button)
        
        devices_layout.addLayout(buttons_layout)
        
        left_layout.addWidget(devices_group)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        details_group = QGroupBox("Device Details")
        self.device_details_panel = DeviceDetailsPanel()
        
        self.device_details_panel.assign_model_button.clicked.connect(
            lambda: self.assign_model(self.selected_device_id, self.get_device_name(self.selected_device_id))
        )
        self.device_details_panel.view_results_button.clicked.connect(
            lambda: self.view_device_results(self.selected_device_id)
        )
        self.device_details_panel.delete_device_button.clicked.connect(
            lambda: self.delete_device(self.selected_device_id, self.get_device_name(self.selected_device_id))
        )
        
        details_layout = QVBoxLayout(details_group)
        details_layout.addWidget(self.device_details_panel)
        
        right_layout.addWidget(details_group)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        splitter.setSizes([700, 300])
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        self.main_window.show_loading("Loading Devices...")
        
        QTimer.singleShot(100, self.refresh_devices)
        
        self.refresh_timer.start()
    
    def on_tab_deselected(self):
        """Handle when this tab is no longer selected"""
        self.refresh_timer.stop()
    
    def on_project_changed(self, project_name, project_path):
        """Handle project change"""
        pass
    
    def refresh_devices(self):
        """Refresh the list of devices"""
        self.api_service.clear_cache()
        self.api_service.get_devices()
        self.api_service.get_models()

    def refresh_devices_button(self):
        """Handle refresh button click"""
        self.main_window.show_loading("Loading Devices...")
        self.api_service.clear_cache()
        self.api_service.get_devices()
        self.api_service.get_models()
    
    def register_device(self):
        """Show dialog to register a new device"""
        dialog = RegisterDeviceDialog(self)
        
        if dialog.exec():
            device_name = dialog.device_name.text().strip()
            
            if not device_name:
                self.main_window.show_error_message("Error", "Device name cannot be empty")
                return
            
            self.main_window.show_loading("Registering device...")
            
            self.api_service.register_device(device_name)
    
    def get_device_name(self, device_id):
        """Get the name of a device by ID"""
        for device in self.devices:
            if device['device_id'] == device_id:
                return device['device_name']
        return "Unknown Device"
    
    def assign_model(self, device_id, device_name):
        """Assign a model to a device"""
        if not self.models:
            self.main_window.show_error_message("Error", "No models available")
            return
        
        dialog = AssignModelDialog(self, device_id, device_name, self.models)
        
        if dialog.exec():
            model_id = dialog.get_selected_model_id()
            
            if not model_id:
                return
            
            self.api_service.set_device_model(device_id, model_id)
            
            self.main_window.show_status_message(f"Assigning model to device {device_name}...", 3000)
    
    def delete_device(self, device_id, device_name):
        """Delete a device"""
        hard_delete = False
        
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Warning)
        message_box.setWindowTitle("Delete Device")
        message_box.setText(f"Are you sure you want to delete device '{device_name}'?")
        message_box.setInformativeText("This will remove the device from the system. Device data will be preserved.")
        
        hard_delete_checkbox = QCheckBox("Permanently delete (cannot be undone)")
        message_box.setCheckBox(hard_delete_checkbox)
        
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message_box.setDefaultButton(QMessageBox.No)
        
        if message_box.exec() != QMessageBox.Yes:
            return
        
        hard_delete = hard_delete_checkbox.isChecked()
        
        self.main_window.show_loading(f"Deleting device {device_name}...")
        
        self.api_service.delete_device(device_id, hard_delete)
    
    def set_model_filter(self, model_id):
        """Set filter to show only devices using a specific model"""
        self.model_filter = model_id
        
        if model_id:
            model_name = "Unknown Model"
            if hasattr(self.main_window, 'models_tab') and hasattr(self.main_window.models_tab, 'models'):
                for model in self.main_window.models_tab.models:
                    if model['model_id'] == model_id:
                        model_name = model['project_name']
                        break
            
            if not hasattr(self, 'filter_banner'):
                self.filter_banner = QLabel()
                self.filter_banner.setStyleSheet("""
                    background-color: #f0f0f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 8px;
                    margin-bottom: 8px;
                """)
                self.layout().insertWidget(0, self.filter_banner)
            
            self.filter_banner.setText(f"Showing devices using model: <b>{model_name}</b> &nbsp;&nbsp; "
                                      f"<a href='#'>Clear Filter</a>")
            self.filter_banner.setVisible(True)
            self.filter_banner.linkActivated.connect(self.clear_model_filter)
        else:
            if hasattr(self, 'filter_banner'):
                self.filter_banner.setVisible(False)
    
    def clear_model_filter(self):
        """Clear the model filter"""
        self.model_filter = None
        if hasattr(self, 'filter_banner'):
            self.filter_banner.setVisible(False)
        
        self.refresh_devices()
    
    def update_devices_table(self):
        """Update the devices table with current data"""
        self.devices_table.setRowCount(0)
        
        filtered_devices = self.devices
        if hasattr(self, 'model_filter') and self.model_filter:
            filtered_devices = [d for d in self.devices if d.get('current_model_id') == self.model_filter]
        
        for i, device in enumerate(filtered_devices):
            self.devices_table.insertRow(i)
            
            self.devices_table.setItem(i, 0, QTableWidgetItem(device['device_name']))
            
            status_item = QTableWidgetItem(device['status'])
            if device['status'] == 'running':
                status_item.setBackground(QColor(200, 255, 200))  
                status_item.setForeground(QColor(0, 100, 0))      
                status_item.setFont(QFont("Arial", 9, QFont.Bold))
            elif device['status'] == 'idle':
                status_item.setBackground(QColor(255, 255, 200))  
                status_item.setForeground(QColor(150, 150, 0))      
            else:
                status_item.setBackground(QColor(255, 200, 200))  
                status_item.setForeground(QColor(150, 0, 0))      
            self.devices_table.setItem(i, 1, status_item)
            
            last_active_text = format_time_ago(device.get('last_active', ''))
            self.devices_table.setItem(i, 2, QTableWidgetItem(last_active_text))
            
            model_name = "None"
            for model in self.models:
                if model['model_id'] == device.get('current_model_id'):
                    model_name = model['project_name']
                    break
            
            self.devices_table.setItem(i, 3, QTableWidgetItem(model_name))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            
            assign_button = QPushButton("Assign Model")
            assign_button.setProperty("device_id", device['device_id'])
            assign_button.setProperty("device_name", device['device_name'])
            assign_button.clicked.connect(lambda checked, btn=assign_button: 
                self.assign_model(btn.property("device_id"), btn.property("device_name")))
            
            actions_layout.addWidget(assign_button)
            
            self.devices_table.setCellWidget(i, 4, actions_widget)
        
        if self.selected_device_id:
            self.update_device_details(self.selected_device_id)
    
    def on_device_selected(self, index):
        """Handle device selection in the table"""
        row = index.row()
        if row >= 0 and row < len(self.devices):
            if hasattr(self, 'model_filter') and self.model_filter:
                filtered_devices = [d for d in self.devices if d.get('current_model_id') == self.model_filter]
                if row < len(filtered_devices):
                    self.selected_device_id = filtered_devices[row]['device_id']
            else:
                self.selected_device_id = self.devices[row]['device_id']
            
            self.update_device_details(self.selected_device_id)
    
    def update_device_details(self, device_id):
        """Update the device details panel"""
        device = next((d for d in self.devices if d['device_id'] == device_id), None)
        if not device:
            self.device_details_panel.device_id_label.setText("N/A")
            self.device_details_panel.device_name_label.setText("N/A")
            self.device_details_panel.device_status_label.setText("N/A")
            self.device_details_panel.last_active_label.setText("N/A")
            self.device_details_panel.current_model_label.setText("N/A")
            self.device_details_panel.assign_model_button.setEnabled(False)
            self.device_details_panel.view_results_button.setEnabled(False)
            self.device_details_panel.delete_device_button.setEnabled(False)
            return
        
        self.device_details_panel.device_id_label.setText(device['device_id'])
        self.device_details_panel.device_name_label.setText(device['device_name'])
        
        status_text = device['status']
        self.device_details_panel.device_status_label.setText(status_text)
        if status_text == 'running':
            self.device_details_panel.device_status_label.setStyleSheet("color: green; font-weight: bold;")
        elif status_text == 'idle':
            self.device_details_panel.device_status_label.setStyleSheet("color: orange;")
        else:
            self.device_details_panel.device_status_label.setStyleSheet("color: red;")
        
        last_active_text = format_time_ago(device.get('last_active', ''))
        self.device_details_panel.last_active_label.setText(last_active_text)
        
        model_name = "None"
        for model in self.models:
            if model['model_id'] == device.get('current_model_id'):
                model_name = model['project_name']
                break
        
        self.device_details_panel.current_model_label.setText(model_name)
        
        self.device_details_panel.assign_model_button.setEnabled(True)
        self.device_details_panel.view_results_button.setEnabled(True)
        self.device_details_panel.delete_device_button.setEnabled(True)
    
    def show_device_context_menu(self, pos):
        """Show context menu for device table"""
        selected_indexes = self.devices_table.selectedIndexes()
        if not selected_indexes:
            return
        
        row = selected_indexes[0].row()
        
        if hasattr(self, 'model_filter') and self.model_filter:
            filtered_devices = [d for d in self.devices if d.get('current_model_id') == self.model_filter]
            if row < 0 or row >= len(filtered_devices):
                return
            device_id = filtered_devices[row]['device_id']
            device_name = filtered_devices[row]['device_name']
        else:
            if row < 0 or row >= len(self.devices):
                return
            device_id = self.devices[row]['device_id']
            device_name = self.devices[row]['device_name']
        
        menu = QMenu(self)
        
        assign_action = QAction("Assign Model", self)
        assign_action.triggered.connect(lambda: self.assign_model(device_id, device_name))
        menu.addAction(assign_action)
        
        view_results_action = QAction("View Results", self)
        view_results_action.triggered.connect(lambda: self.view_device_results(device_id))
        menu.addAction(view_results_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete Device", self)
        delete_action.triggered.connect(lambda: self.delete_device(device_id, device_name))
        menu.addAction(delete_action)
        
        menu.exec(self.devices_table.viewport().mapToGlobal(pos))
    
    def view_device_results(self, device_id):
        """View results for a specific device"""
        self.main_window.tab_widget.setCurrentIndex(6) 
        
        if hasattr(self.main_window.results_tab, 'set_device_filter'):
            self.main_window.results_tab.set_device_filter(device_id)
    
    
    @Slot(str, bool, object)
    def on_request_finished(self, endpoint, success, data):
        """Handle API request finished"""
        if 'api/devices' in endpoint and success and 'devices' in data:
            self.devices = data['devices']
            self.update_devices_table()
            
            if self.selected_device_id:
                self.update_device_details(self.selected_device_id)
                
            self.main_window.hide_loading()
        
        elif 'api/models' in endpoint and not 'create' in endpoint and success and 'models' in data:
            self.models = data['models']
            self.update_devices_table()
            self.main_window.hide_loading()
        
        elif 'api/devices/register' in endpoint and success:
            device_id = data.get('device_id', 'Unknown')
            self.main_window.show_info_message(
                "Device Registered",
                f"Device registered successfully with ID: {device_id}"
            )
            
            self.refresh_devices()
        
        elif 'api/devices/' in endpoint and 'set_model' in endpoint and success:
            self.main_window.show_info_message(
                "Model Assigned",
                "Model assigned to device successfully"
            )
            
            self.refresh_devices()
        
        elif 'api/devices/' in endpoint and 'delete' in endpoint and success:
            self.main_window.show_info_message(
                "Device Deleted",
                "Device deleted successfully"
            )
            
            if self.selected_device_id in endpoint:
                self.selected_device_id = None
            
            self.refresh_devices()