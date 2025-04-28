#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Devices Tab - Manage and monitor connected devices
"""

import os
import json
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Slot, QTimer, Signal, QPoint
from PySide6.QtGui import QAction

class RegisterDeviceDialog(QDialog):
    """Dialog for registering a new device"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Register New Device")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Device Name
        self.device_name = QLineEdit()
        form_layout.addRow("Device Name:", self.device_name)
        
        layout.addLayout(form_layout)
        
        # Add message
        layout.addWidget(QLabel("This will register a new device with the server."))
        
        # Add buttons
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
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Device info
        device_label = QLabel(f"Device: {device_name} (ID: {device_id})")
        layout.addWidget(device_label)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Model selection
        self.model_combo = QComboBox()
        for model in models:
            self.model_combo.addItem(model['project_name'], model['model_id'])
        
        form_layout.addRow("Select Model:", self.model_combo)
        
        layout.addLayout(form_layout)
        
        # Add message
        layout.addWidget(QLabel("This will assign the selected model to the device."))
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_selected_model_id(self):
        """Get the selected model ID"""
        return self.model_combo.currentData()

class DevicesTab(QWidget):
    """Tab for managing connected devices"""
    
    
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        self.api_service = main_window.api_service
        
        # State variables
        self.devices = []
        self.models = []
        self.selected_device_id = None
        
        # Set up UI
        self.setup_ui()
        
        # Set up refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_devices)
        self.refresh_timer.setInterval(30000)  # 30 seconds
        
        # Connect signals
        self.api_service.request_finished.connect(self.on_request_finished)
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Devices group
        devices_group = QGroupBox("Connected Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        # Devices table
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
        
        devices_layout.addWidget(self.devices_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_devices_button)
        buttons_layout.addWidget(self.refresh_button)
        
        devices_layout.addLayout(buttons_layout)
        
        layout.addWidget(devices_group)
        
        # Add stretch at the end to push widgets to the top
        layout.addStretch()
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        # Show loading indicator
        self.main_window.show_loading("Loading Devices...")
        
        # Refresh devices in a non-blocking way
        QTimer.singleShot(100, self.refresh_devices)
        
            # Start refresh timer
        self.refresh_timer.start()
    
    def on_project_changed(self, project_name, project_path):
        """Handle project change"""
        # We don't need to do anything specific here
        pass
    
    def refresh_devices(self):
        """Refresh the list of devices"""
        self.api_service.get_devices()
        self.api_service.get_models()
    
    def refresh_devices_button(self):
        self.main_window.show_loading("Loading Devices...")
        self.api_service.get_devices()
        self.api_service.get_models()
    
    
    def assign_model(self, device_id, device_name):
        """Assign a model to a device"""
        # Check if we have models
        if not self.models:
            self.main_window.show_error_message("Error", "No models available")
            return
        
        # Create dialog
        dialog = AssignModelDialog(self, device_id, device_name, self.models)
        
        if dialog.exec():
            model_id = dialog.get_selected_model_id()
            
            if not model_id:
                return
            
            # Assign model
            self.api_service.set_device_model(device_id, model_id)
            
            # Show status message
            self.main_window.show_status_message(f"Assigning model to device {device_name}...", 3000)
    
    def update_devices_table(self):
        """Update the devices table with current data"""
        self.devices_table.setRowCount(0)
        
        for i, device in enumerate(self.devices):
            self.devices_table.insertRow(i)
            
            # Device Name
            self.devices_table.setItem(i, 0, QTableWidgetItem(device['device_name']))
            
            # Status
            status_item = QTableWidgetItem(device['status'])
            if device['status'] == 'running':
                status_item.setBackground(Qt.green)
            elif device['status'] == 'idle':
                status_item.setBackground(Qt.yellow)
            else:
                status_item.setBackground(Qt.red)
            self.devices_table.setItem(i, 1, status_item)
            
            # Last Active
            try:
                last_active = datetime.fromisoformat(device['last_active'])
                now = datetime.now()
                
                if (now - last_active) < timedelta(minutes=5):
                    last_active_text = "Just now"
                elif (now - last_active) < timedelta(hours=1):
                    minutes = (now - last_active).seconds // 60
                    last_active_text = f"{minutes} min ago"
                elif (now - last_active) < timedelta(days=1):
                    hours = (now - last_active).seconds // 3600
                    last_active_text = f"{hours} hours ago"
                else:
                    days = (now - last_active).days
                    last_active_text = f"{days} days ago"
            except:
                last_active_text = "Unknown"
                
            self.devices_table.setItem(i, 2, QTableWidgetItem(last_active_text))
            
            # Model
            model_name = "None"
            for model in self.models:
                if model['model_id'] == device.get('current_model_id'):
                    model_name = model['project_name']
                    break
            
            self.devices_table.setItem(i, 3, QTableWidgetItem(model_name))
            
            # Actions
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
    
    def update_device_details(self, device_id):
        """Update the device details panel"""
        for device in self.devices:
            if device['device_id'] == device_id:
                self.device_id_label.setText(device['device_id'])
                self.device_name_label.setText(device['device_name'])
                self.device_status_label.setText(device['status'])
                self.last_active_label.setText(device['last_active'])
                
                # Find model name
                model_name = "None"
                for model in self.models:
                    if model['model_id'] == device.get('current_model_id'):
                        model_name = model['project_name']
                        break
                
                self.current_model_label.setText(model_name)
                return
        
        # Clear details if device not found
        self.device_id_label.setText("N/A")
        self.device_name_label.setText("N/A")
        self.device_status_label.setText("N/A")
        self.last_active_label.setText("N/A")
        self.current_model_label.setText("N/A")
    
    def show_device_context_menu(self, pos):
        """Show context menu for device table"""
        # Get the selected row
        selected_indexes = self.devices_table.selectedIndexes()
        if not selected_indexes:
            return
        
        # Get the device for the selected row
        row = selected_indexes[0].row()
        device_id = self.devices[row]['device_id']
        device_name = self.devices[row]['device_name']
        
        # Create menu
        menu = QMenu(self)
        
        # Add actions
        assign_action = QAction("Assign Model", self)
        assign_action.triggered.connect(lambda: self.assign_model(device_id, device_name))
        menu.addAction(assign_action)
        
        view_results_action = QAction("View Results", self)
        view_results_action.triggered.connect(lambda: self.view_device_results(device_id))
        menu.addAction(view_results_action)
        
        # Show menu
        menu.exec(self.devices_table.viewport().mapToGlobal(pos))
    
    def view_device_results(self, device_id):
        """View results for a specific device"""
        # Switch to Results tab
        self.main_window.tab_widget.setCurrentIndex(5)  # Assuming Results is tab 5
        
        # Set device filter in Results tab
        if hasattr(self.main_window.results_tab, 'set_device_filter'):
            self.main_window.results_tab.set_device_filter(device_id)
    
    # Signal handlers
    
    @Slot(str, bool, object)
    def on_request_finished(self, endpoint, success, data):
        """Handle API request finished"""
        if 'api/devices' in endpoint and success and 'devices' in data:
            # Update devices list
            self.devices = data['devices']
            self.update_devices_table()
            
            # Update details if a device is selected
            if self.selected_device_id:
                self.update_device_details(self.selected_device_id)
        
        elif 'api/models' in endpoint and not 'create' in endpoint and success and 'models' in data:
            # Update models list
            self.models = data['models']
            self.update_devices_table()
            self.main_window.hide_loading()
        
        elif 'api/devices/register' in endpoint and success:
            # Show success message
            model_id = data.get('device_id', 'Unknown')
            self.main_window.show_info_message(
                "Device Registered",
                f"Device registered successfully with ID: {model_id}"
            )
            
            # Refresh devices
            self.refresh_devices()
        
        elif 'api/devices/' in endpoint and 'set_model' in endpoint and success:
            # Show success message
            self.main_window.show_info_message(
                "Model Assigned",
                "Model assigned to device successfully"
            )
            
            # Refresh devices
            self.refresh_devices()