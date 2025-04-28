#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deploy Tab - Deploy models to the cloud API
"""

import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QGroupBox, QProgressDialog,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QCoreApplication

class DeployTab(QWidget):
    """Tab for deploying models to the cloud API"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        self.api_service = main_window.api_service
        
        # Connect signals
        self.api_service.request_started.connect(self.on_request_started)
        self.api_service.request_finished.connect(self.on_request_finished)
        
        # Set up UI
        self.setup_ui()
        
        # State variables
        self.project_path = None
        self.deployed_model_id = None
        self.progress_dialog = None
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Model info group
        info_group = QGroupBox("Model Information")
        info_layout = QFormLayout(info_group)
        
        self.model_status_label = QLabel("No model available")
        info_layout.addRow("Model Status:", self.model_status_label)
        
        self.tflite_status_label = QLabel("Not converted")
        info_layout.addRow("TFLite Status:", self.tflite_status_label)
        
        self.api_endpoint_label = QLabel(self.config.api_endpoint)
        info_layout.addRow("API Endpoint:", self.api_endpoint_label)
        
        layout.addWidget(info_group)
        
        # Deploy group
        deploy_group = QGroupBox("Deploy Model")
        deploy_layout = QVBoxLayout(deploy_group)
        
        deploy_button_layout = QHBoxLayout()
        
        self.deploy_button = QPushButton("Deploy to Cloud")
        self.deploy_button.clicked.connect(self.deploy_model)
        self.deploy_button.setEnabled(False)
        deploy_button_layout.addWidget(self.deploy_button)
        
        self.test_button = QPushButton("Test Model")
        self.test_button.clicked.connect(self.test_model)
        self.test_button.setEnabled(False)
        deploy_button_layout.addWidget(self.test_button)
        
        deploy_layout.addLayout(deploy_button_layout)
        
        # Deployment status
        deployment_layout = QFormLayout()
        
        self.deploy_status_label = QLabel("Not deployed")
        deployment_layout.addRow("Deployment Status:", self.deploy_status_label)
        
        self.model_id_label = QLabel("N/A")
        deployment_layout.addRow("Model ID:", self.model_id_label)
        
        deploy_layout.addLayout(deployment_layout)
        
        layout.addWidget(deploy_group)
        
        # Test results group
        test_group = QGroupBox("Test Results")
        test_layout = QVBoxLayout(test_group)
        
        self.test_result_label = QLabel("No test results")
        test_layout.addWidget(self.test_result_label)
        
        layout.addWidget(test_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def on_project_changed(self, project_name, project_path):
        """Handle project change"""
        self.project_path = project_path
        self.update_model_status()
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        # Update API endpoint label
        self.api_endpoint_label.setText(self.config.api_endpoint)
        
        if self.project_path:
            self.update_model_status()
    
    def update_model_status(self):
        """Update the model status labels"""
        if not self.project_path:
            return
        
        model_path = os.path.join(self.project_path, "models", "model.h5")
        tflite_path = os.path.join(self.project_path, "models", "model.tflite")
        
        has_model = os.path.exists(model_path)
        has_tflite = os.path.exists(tflite_path)
        
        if has_model:
            self.model_status_label.setText("Trained")
        else:
            self.model_status_label.setText("Not trained")
        
        if has_tflite:
            self.tflite_status_label.setText("Converted")
            self.deploy_button.setEnabled(True)
            self.test_button.setEnabled(True)
        else:
            self.tflite_status_label.setText("Not converted")
            self.deploy_button.setEnabled(False)
            self.test_button.setEnabled(False)
    
    def deploy_model(self):
        """Deploy the model to the cloud API"""
        if not self.project_path:
            self.main_window.show_error_message("Error", "No project selected")
            return
        
        # Check if TFLite model exists
        tflite_path = os.path.join(self.project_path, "models", "model.tflite")
        metadata_path = os.path.join(self.project_path, "models", "metadata.json")
        
        if not os.path.exists(tflite_path):
            self.main_window.show_error_message("Error", "TFLite model not found")
            return
        
        if not os.path.exists(metadata_path):
            self.main_window.show_error_message("Error", "Model metadata not found")
            return
        
        # Confirm upload
        confirm = self.main_window.confirm_action(
            "Deploy Model",
            "This will upload the model to the API server. Continue?"
        )
        
        if not confirm:
            return
        
        # Upload the model
        self.api_service.upload_model(tflite_path, metadata_path)
    
    def test_model(self):
        """Test the model with an image"""
        if not self.project_path:
            self.main_window.show_error_message("Error", "No project selected")
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Test Image",
            os.path.expanduser("~"),
            "Images (*.jpg *.jpeg *.png);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Test model
        success, message, result = self.main_window.model_service.test_model(
            self.project_path,
            file_path
        )
        
        if success:
            result_text = f"Result: {result['result']}\n"
            result_text += f"Confidence: {result['confidence']:.2f}"
            self.test_result_label.setText(result_text)
        else:
            self.main_window.show_error_message("Test Error", message)
        
    @Slot(str)
    def on_request_started(self, endpoint):
        """Handle API request started signal"""
        print(endpoint)
    
    @Slot(str, bool, object)
    def on_request_finished(self, endpoint, success, data):
        """Handle API request finished signal"""
        if 'api/models/create' in endpoint:            
            if success:
                # Update deployment status
                self.deploy_status_label.setText("Deployed")
                self.model_id_label.setText(data.get('model_id', 'Unknown'))
                self.deployed_model_id = data.get('model_id')
                
                # Save model ID to project
                try:
                    deploy_info = {
                        'model_id': data.get('model_id'),
                        'deploy_date': data.get('message', 'Unknown'),
                        'api_endpoint': self.config.api_endpoint
                    }
                    
                    with open(os.path.join(self.project_path, "models", "deploy_info.json"), 'w') as f:
                        json.dump(deploy_info, f, indent=4)
                except Exception as e:
                    print(f"Error saving deploy info: {str(e)}")
                
                self.main_window.show_info_message(
                    "Deployment Successful",
                    f"Model deployed with ID: {data.get('model_id', 'Unknown')}"
                )
            else:
                error_message = data.get('error_message', str(data))
                self.main_window.show_error_message("Deployment Error", error_message)