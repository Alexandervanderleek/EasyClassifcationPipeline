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
from PySide6.QtGui import QFont, QColor, QPainter
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

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
        
        # Set up UI
        self.setup_ui()
        
        # Set up refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_results)
        self.refresh_timer.setInterval(10000)  # 10 seconds
        
        # Connect signals
        self.refresh_triggered.connect(self.refresh_results)
        self.api_service.request_finished.connect(self.on_request_finished)
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create splitter for top and bottom sections
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Top widget - Filters and results table
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
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
        self.refresh_button.clicked.connect(self.refresh_triggered)
        filters_layout.addWidget(self.refresh_button)
        
        top_layout.addWidget(filters_group)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Date/Time", "Device", "Model", "Result", "Confidence", "Details"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        
        top_layout.addWidget(self.results_table)
        
        # Add top widget to splitter
        splitter.addWidget(top_widget)
        
        # Bottom widget - Charts and statistics
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        # Stats group
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        # Results count
        count_layout = QFormLayout()
        self.result_count_label = QLabel("0")
        count_layout.addRow("Total Results:", self.result_count_label)
        
        self.positive_count_label = QLabel("0")
        count_layout.addRow("Positive Results:", self.positive_count_label)
        
        self.negative_count_label = QLabel("0")
        count_layout.addRow("Negative Results:", self.negative_count_label)
        
        stats_layout.addLayout(count_layout)
        
        # Chart
        self.chart_view = self._create_chart()
        stats_layout.addWidget(self.chart_view, 1)
        
        bottom_layout.addWidget(stats_group)
        
        # Add bottom widget to splitter
        splitter.addWidget(bottom_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 200])
    
    def _create_chart(self):
        """Create the chart for visualization"""
        # Create chart
        self.chart = QChart()
        self.chart.setTitle("Classification Results")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create bar series
        self.bar_series = QBarSeries()
        
        # Create chart view
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
    
    def _update_chart(self):
        """Update the chart with current data"""
        # Clear previous series
        self.chart.removeAllSeries()
        
        # Count results by class
        results_by_class = {}
        for result in self.results:
            result_class = result['result']
            if result_class not in results_by_class:
                results_by_class[result_class] = 0
            results_by_class[result_class] += 1
        
        if not results_by_class:
            # No data to display
            return
        
        # Create bar set
        bar_set = QBarSet("Results")
        
        # Add data and categories
        categories = []
        for result_class, count in results_by_class.items():
            bar_set.append(count)
            categories.append(result_class)
        
        # Create series and add to chart
        self.bar_series = QBarSeries()
        self.bar_series.append(bar_set)
        self.chart.addSeries(self.bar_series)
        
        # Create axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(results_by_class.values()) * 1.1)  # Add 10% margin
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        self.bar_series.attachAxis(axis_y)
        
        # Set title
        self.chart.setTitle(f"Classification Results ({len(self.results)} total)")
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        # Refresh devices and models for filters
        self.api_service.get_devices()
        self.api_service.get_models()
        
        # Refresh results
        self.refresh_results()
        
        # Start refresh timer
        self.refresh_timer.start()
    
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
        # Get filter values
        self.device_filter = self.device_combo.currentData()
        self.model_filter = self.model_combo.currentData()
        self.limit = self.limit_spin.value()
        
        # Get results
        self.api_service.get_results(self.device_filter, self.model_filter, self.limit)
    
    def update_device_combo(self):
        """Update device filter combo with current devices"""
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
    
    def update_model_combo(self):
        """Update model filter combo with current models"""
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
    
    def update_results_table(self):
        """Update the results table with current data"""
        self.results_table.setRowCount(0)
        
        for i, result in enumerate(self.results):
            self.results_table.insertRow(i)
            
            # Date/Time
            try:
                timestamp = datetime.fromisoformat(result['timestamp'])
                timestamp_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp_text = result['timestamp']
            
            self.results_table.setItem(i, 0, QTableWidgetItem(timestamp_text))
            
            # Device
            self.results_table.setItem(i, 1, QTableWidgetItem(result['device_name']))
            
            # Model
            self.results_table.setItem(i, 2, QTableWidgetItem(result['project_name']))
            
            # Result
            result_item = QTableWidgetItem(result['result'])
            if result['result'] == 'positive':
                result_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                result_item.setBackground(QColor(255, 200, 200))  # Light red
            
            self.results_table.setItem(i, 3, result_item)
            
            # Confidence
            confidence_text = f"{result['confidence'] * 100:.1f}%"
            self.results_table.setItem(i, 4, QTableWidgetItem(confidence_text))
            
            # Details button
            details_item = QTableWidgetItem("View")
            details_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(i, 5, details_item)
        
        # Update statistics
        self.result_count_label.setText(str(len(self.results)))
        
        positive_count = sum(1 for r in self.results if r['result'] == 'positive')
        self.positive_count_label.setText(str(positive_count))
        
        negative_count = sum(1 for r in self.results if r['result'] == 'negative')
        self.negative_count_label.setText(str(negative_count))
        
        # Update chart
        self._update_chart()
    
    @Slot()
    def on_filter_changed(self):
        """Handle when a filter is changed"""
        self.refresh_results()
    
    # Signal handlers
    
    @Slot(str, bool, object)
    def on_request_finished(self, endpoint, success, data):
        """Handle API request finished"""
        if 'api/results' in endpoint and success and 'results' in data:
            # Update results
            self.results = data['results']
            self.update_results_table()
        
        elif 'api/devices' in endpoint and success and 'devices' in data:
            # Update devices list for filter
            self.devices = data['devices']
            self.update_device_combo()
        
        elif 'api/models' in endpoint and not 'create' in endpoint and success and 'models' in data:
            # Update models list for filter
            self.models = data['models']
            self.update_model_combo()