#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Results Tab - View and analyze classification results
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QSpinBox, QFormLayout, QSplitter,
    QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Slot, QTimer, Signal
from PySide6.QtGui import QFont, QColor

class ResultsTab(QWidget):
    """Tab for viewing and analyzing classification results"""
    
    refresh_triggered = Signal()
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        self.api_service = main_window.api_service
        
        # State variables
        self.results = []
        self.devices = []
        self.models = []
        self.device_filter = None
        self.model_filter = None
        self.limit = 50

        self.is_updating_ui = False
        self.is_loading_results = False
        
        # Set up UI
        self.setup_ui()
        
        # Set up refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_results)
        self.refresh_timer.setInterval(30000)  # 30 seconds
        
        # Connect signals
        self.refresh_triggered.connect(self.refresh_results)
        self.api_service.request_finished.connect(self.on_request_finished)
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Filters group
        filters_group = QGroupBox("Filters")
        filters_layout = QHBoxLayout(filters_group)
        
        # Device filter
        device_layout = QFormLayout()
        self.device_combo = QComboBox()
        self.device_combo.addItem("All Devices", None)
        self.device_combo.currentIndexChanged.connect(self.on_filter_changed)
        device_layout.addRow("Device:", self.device_combo)
        filters_layout.addLayout(device_layout)
        
        # Model filter
        model_layout = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItem("All Models", None)
        self.model_combo.currentIndexChanged.connect(self.on_filter_changed)
        model_layout.addRow("Model:", self.model_combo)
        filters_layout.addLayout(model_layout)
        
        # Limit filter
        limit_layout = QFormLayout()
        self.limit_spin = QSpinBox()
        self.limit_spin.setMinimum(10)
        self.limit_spin.setMaximum(1000)
        self.limit_spin.setValue(self.limit)
        self.limit_spin.setSingleStep(10)
        self.limit_spin.valueChanged.connect(self.on_filter_changed)
        limit_layout.addRow("Limit:", self.limit_spin)
        filters_layout.addLayout(limit_layout)
        
        # Add refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_results_button)
        filters_layout.addWidget(self.refresh_button)
        
        layout.addWidget(filters_group)
        
        # Stats group
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        # Results count
        count_layout = QFormLayout()
        self.result_count_label = QLabel("0")
        self.result_count_label.setFont(QFont("Arial", 10, QFont.Bold))
        count_layout.addRow("Total Results:", self.result_count_label)
        
        self.positive_count_label = QLabel("0")
        self.positive_count_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.positive_count_label.setStyleSheet("color: #2a9d8f;")
        count_layout.addRow("Positive Results:", self.positive_count_label)
        
        self.negative_count_label = QLabel("0")
        self.negative_count_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.negative_count_label.setStyleSheet("color: #e76f51;")
        count_layout.addRow("Negative Results:", self.negative_count_label)
        
        stats_layout.addLayout(count_layout)
        
        # Add spacer to push stats to the left
        stats_layout.addStretch(1)
        
        layout.addWidget(stats_group)
        
        # Results table
        results_group = QGroupBox("Classification Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Date/Time", "Device", "Model", "Result", "Confidence", "Details"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSortingEnabled(True)
        
        # Set table styles
        self.results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: #ffffff;
                alternate-background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group, 1)  # Stretch factor 1 to make it take up available space
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        # Refresh devices and models for filters
        self.main_window.show_loading("Loading Results...")
        
        QTimer.singleShot(100, self.get_initial)
        
        self.refresh_timer.start()
    
    def get_initial(self):
        """Get initial data for the tab"""
        self.api_service.get_devices()
        self.api_service.get_models()
        QTimer.singleShot(500, self.refresh_results)

    def set_device_filter(self, device_id):
        """Set the device filter (called from Devices tab)"""
        for i in range(self.device_combo.count()):
            if self.device_combo.itemData(i) == device_id:
                self.device_combo.setCurrentIndex(i)
                return
        
        # If device not found in combo, add it
        for device in self.devices:
            if device['device_id'] == device_id:
                self.device_combo.addItem(device['device_name'], device_id)
                self.device_combo.setCurrentIndex(self.device_combo.count() - 1)
                return
    
    def refresh_results(self):
        """Refresh results based on current filters"""
        if self.is_loading_results:
            return
        
        self.is_loading_results = True
        # Get filter values
        self.device_filter = self.device_combo.currentData()
        self.model_filter = self.model_combo.currentData()
        self.limit = self.limit_spin.value()
        
        # Get results
        self.api_service.get_results(self.device_filter, self.model_filter, self.limit)
    
    def refresh_results_button(self):
        """Refresh results when button is clicked"""
        self.main_window.show_loading("Loading Results...")
        if self.is_loading_results:
            return
        
        self.is_loading_results = True
        # Get filter values
        self.device_filter = self.device_combo.currentData()
        self.model_filter = self.model_combo.currentData()
        self.limit = self.limit_spin.value()
        
        # Get results
        self.api_service.get_results(self.device_filter, self.model_filter, self.limit)
    
    def update_device_combo(self):
        """Update device filter combo with current devices"""
        self.is_updating_ui = True

        current_device = self.device_combo.currentData()
        
        # Clear and add "All Devices" option
        self.device_combo.clear()
        self.device_combo.addItem("All Devices", None)

        # Add devices
        for device in self.devices:
            self.device_combo.addItem(device['device_name'], device['device_id'])
        
        # Restore previous selection if possible
        if current_device:
            for i in range(self.device_combo.count()):
                if self.device_combo.itemData(i) == current_device:
                    self.device_combo.setCurrentIndex(i)
                    break
        self.is_updating_ui = False
    
    def update_model_combo(self):
        """Update model filter combo with current models"""
        self.is_updating_ui = True
        current_model = self.model_combo.currentData()
        
        # Clear and add "All Models" option
        self.model_combo.clear()
        self.model_combo.addItem("All Models", None)
        
        # Add models
        for model in self.models:
            self.model_combo.addItem(model['project_name'], model['model_id'])
        
        # Restore previous selection if possible
        if current_model:
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_model:
                    self.model_combo.setCurrentIndex(i)
                    break
        
        self.is_updating_ui = False

    def update_results_table(self):
        """Update the results table with current data"""
        self.results_table.setRowCount(0)
        
        # Sort results by timestamp (newest first)
        sorted_results = sorted(
            self.results, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )
        
        for i, result in enumerate(sorted_results):
            self.results_table.insertRow(i)
            
            # Date/Time
            try:
                timestamp = datetime.fromisoformat(result['timestamp'])
                timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp_text = result['timestamp']
            
            date_item = QTableWidgetItem(timestamp_text)
            date_item.setData(Qt.UserRole, result['timestamp'])  # Store original for sorting
            self.results_table.setItem(i, 0, date_item)
            
            # Device
            self.results_table.setItem(i, 1, QTableWidgetItem(result['device_name']))
            
            # Model
            self.results_table.setItem(i, 2, QTableWidgetItem(result['project_name']))
            
            # Result
            result_item = QTableWidgetItem(result['result'])
            
            # Style by result type
            if result['result'].lower() == 'positive':
                result_item.setForeground(QColor("#2a9d8f"))  # Green for positive
                result_item.setFont(QFont("Arial", 9, QFont.Bold))
            else:
                result_item.setForeground(QColor("#e76f51"))  # Red/orange for negative
                result_item.setFont(QFont("Arial", 9, QFont.Bold))
            
            self.results_table.setItem(i, 3, result_item)
            
            # Confidence
            confidence_value = result.get('confidence', 0)
            confidence_text = f"{confidence_value * 100:.1f}%"
            confidence_item = QTableWidgetItem(confidence_text)
            confidence_item.setData(Qt.UserRole, confidence_value)  # Store original for sorting
            
            # Style confidence based on value
            if confidence_value >= 0.9:
                confidence_item.setForeground(QColor("#1b4332"))  # Dark green for high confidence
                confidence_item.setFont(QFont("Arial", 9, QFont.Bold))
            elif confidence_value >= 0.7:
                confidence_item.setForeground(QColor("#2a9d8f"))  # Medium green
            elif confidence_value >= 0.5:
                confidence_item.setForeground(QColor("#e9c46a"))  # Yellow
            else:
                confidence_item.setForeground(QColor("#e76f51"))  # Red/orange for low confidence
            
            self.results_table.setItem(i, 4, confidence_item)
            
            # Details button
            details_item = QTableWidgetItem("View Details")
            details_item.setTextAlignment(Qt.AlignCenter)
            details_item.setForeground(QColor("#457b9d"))  # Blue for clickable items
            self.results_table.setItem(i, 5, details_item)
        
        # Update statistics
        self.result_count_label.setText(str(len(self.results)))
        
        positive_count = sum(1 for r in self.results if r['result'].lower() == 'positive')
        self.positive_count_label.setText(str(positive_count))
        
        negative_count = sum(1 for r in self.results if r['result'].lower() == 'negative')
        self.negative_count_label.setText(str(negative_count))
    
    @Slot()
    def on_filter_changed(self):
        """Handle when a filter is changed"""
        if self.is_updating_ui:
            return
        
        if hasattr(self, '_filter_timer') and self._filter_timer.isActive():
            self._filter_timer.stop()
    
        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self.refresh_results)
        self._filter_timer.start(300)  # 300ms delay
    
    # Signal handlers
    @Slot(str, bool, object)
    def on_request_finished(self, endpoint, success, data):
        """Handle API request finished"""
        if 'api/results' in endpoint and success and 'results' in data:
            # Update results
            self.is_loading_results = False
        
            if success and 'results' in data:
                # Update results
                self.results = data['results']
                self.update_results_table()
            self.main_window.hide_loading()
        
        elif 'api/devices' in endpoint and success and 'devices' in data:
            # Update devices list for filter
            self.devices = data['devices']
            self.update_device_combo()
        
        elif 'api/models' in endpoint and not 'create' in endpoint and success and 'models' in data:
            # Update models list for filter
            self.models = data['models']
            self.update_model_combo()