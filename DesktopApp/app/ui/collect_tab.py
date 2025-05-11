"""
Collect Tab - Collect training images using camera or file import
"""

import os
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, 
    QLabel, QPushButton, QGroupBox, QTabWidget, QProgressBar,
    QFileDialog, QCheckBox
)
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QImage, QPixmap

from app.services.camera_service import CameraService
from app.services.data_service import DataService

class CollectTab(QWidget):
    """Tab for collecting training images"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        
        self.camera_service = CameraService(self.config)
        self.data_service = DataService(self.config)
        
        self.camera_service.camera_started.connect(self.on_camera_started)
        self.camera_service.camera_stopped.connect(self.on_camera_stopped)
        self.camera_service.frame_captured.connect(self.on_frame_captured)
        self.camera_service.image_saved.connect(self.on_image_saved)
        
        self.data_service.import_started.connect(self.on_import_started)
        self.data_service.import_progress.connect(self.on_import_progress)
        self.data_service.import_finished.connect(self.on_import_finished)
        
        self.setup_ui()
        
        self.project_path = None
        self.camera_running = False
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        camera_widget = QWidget()
        self.tab_widget.addTab(camera_widget, "Camera Capture")
        
        import_widget = QWidget()
        self.tab_widget.addTab(import_widget, "Import Images")
        
        self.setup_camera_tab(camera_widget)
        
        self.setup_import_tab(import_widget)
        
        self.stats_group = QGroupBox("Dataset Statistics")
        stats_layout = QFormLayout(self.stats_group)
        
        self.positive_count_label = QLabel("0")
        stats_layout.addRow("Positive Images:", self.positive_count_label)
        
        self.negative_count_label = QLabel("0")
        stats_layout.addRow("Negative Images:", self.negative_count_label)
        
        layout.addWidget(self.stats_group)
    
    def setup_camera_tab(self, widget):
        """Set up the camera capture tab"""
        layout = QVBoxLayout(widget)
        
        self.camera_preview = QLabel("Camera not started")
        self.camera_preview.setAlignment(Qt.AlignCenter)
        self.camera_preview.setMinimumSize(640, 480)
        self.camera_preview.setStyleSheet("background-color: #222; color: #ddd;")
        layout.addWidget(self.camera_preview)
        
        camera_controls = QHBoxLayout()
        
        self.start_camera_button = QPushButton("Start Camera")
        self.start_camera_button.clicked.connect(self.start_camera)
        camera_controls.addWidget(self.start_camera_button)
        
        self.stop_camera_button = QPushButton("Stop Camera")
        self.stop_camera_button.clicked.connect(self.stop_camera)
        self.stop_camera_button.setEnabled(False)
        camera_controls.addWidget(self.stop_camera_button)
        
        layout.addLayout(camera_controls)
        
        capture_controls = QHBoxLayout()
        
        self.capture_positive_button = QPushButton("Capture Positive")
        self.capture_positive_button.clicked.connect(lambda: self.capture_image("positive"))
        self.capture_positive_button.setEnabled(False)
        capture_controls.addWidget(self.capture_positive_button)
        
        self.capture_negative_button = QPushButton("Capture Negative")
        self.capture_negative_button.clicked.connect(lambda: self.capture_image("negative"))
        self.capture_negative_button.setEnabled(False)
        capture_controls.addWidget(self.capture_negative_button)
        
        layout.addLayout(capture_controls)
    
    def setup_import_tab(self, widget):
        """Set up the image import tab"""
        layout = QVBoxLayout(widget)
        
        positive_group = QGroupBox("Positive Images")
        positive_layout = QHBoxLayout(positive_group)
        
        self.import_positive_folder_button = QPushButton("Import Folder")
        self.import_positive_folder_button.clicked.connect(lambda: self.import_folder("positive"))
        positive_layout.addWidget(self.import_positive_folder_button)
        
        self.import_positive_files_button = QPushButton("Import Files")
        self.import_positive_files_button.clicked.connect(lambda: self.import_files("positive"))
        positive_layout.addWidget(self.import_positive_files_button)
        
        layout.addWidget(positive_group)
        
        negative_group = QGroupBox("Negative Images")
        negative_layout = QHBoxLayout(negative_group)
        
        self.import_negative_folder_button = QPushButton("Import Folder")
        self.import_negative_folder_button.clicked.connect(lambda: self.import_folder("negative"))
        negative_layout.addWidget(self.import_negative_folder_button)
        
        self.import_negative_files_button = QPushButton("Import Files")
        self.import_negative_files_button.clicked.connect(lambda: self.import_files("negative"))
        negative_layout.addWidget(self.import_negative_files_button)
        
        layout.addWidget(negative_group)
        
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.import_progress_bar = QProgressBar()
        self.import_progress_bar.setRange(0, 100)
        self.import_progress_bar.setValue(0)
        progress_layout.addWidget(self.import_progress_bar)
        
        self.import_status_label = QLabel("Ready to import images")
        progress_layout.addWidget(self.import_status_label)
        
        layout.addWidget(progress_group)
    
    def on_project_changed(self, project_name, project_path):
        """Handle project change"""
        self.project_path = project_path
        self.update_image_counts()
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        if self.project_path:
            self.update_image_counts()
    
    def update_image_counts(self):
        """Update the image count labels"""
        if not self.project_path:
            return
        
        pos_count, neg_count = self.main_window.model_service.get_image_counts(self.project_path)
        
        self.positive_count_label.setText(str(pos_count))
        self.negative_count_label.setText(str(neg_count))
    
    def start_camera(self):
        """Start the camera"""
        if not self.project_path:
            self.main_window.show_error_message("Error", "No project selected")
            return
        
        success, message = self.camera_service.start_camera()
        
        if not success:
            self.main_window.show_error_message("Camera Error", message)
    
    def stop_camera(self):
        """Stop the camera"""
        self.camera_service.stop_camera()
    
    def capture_image(self, class_type):
        """Capture image from camera"""
        if not self.camera_running:
            return
        
        success, result = self.camera_service.capture_image(class_type, self.project_path)
        
        if success:
            self.main_window.show_status_message(f"Captured {class_type} image", 3000)
            self.update_image_counts()
        else:
            self.main_window.show_error_message("Error", f"Failed to capture image: {result}")
    
    def import_folder(self, class_type):
        """Import images from a folder"""
        if not self.project_path:
            self.main_window.show_error_message("Error", "No project selected")
            return
        
        folder_path = QFileDialog.getExistingDirectory(
            self,
            f"Select folder with {class_type} images",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        if not folder_path:
            return
        
        success, message = self.data_service.import_images_from_folder(
            folder_path, 
            class_type, 
            self.project_path
        )
        
        if not success:
            self.main_window.show_error_message("Import Error", message)
    
    def import_files(self, class_type):
        """Import individual image files"""
        if not self.project_path:
            self.main_window.show_error_message("Error", "No project selected")
            return
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            f"Select {class_type} images",
            os.path.expanduser("~"),
            "Images (*.jpg *.jpeg *.png *.bmp *.gif);;All Files (*)"
        )
        
        if not file_paths:
            return
        
        success, message = self.data_service.import_image_files(
            file_paths, 
            class_type, 
            self.project_path
        )
        
        if not success:
            self.main_window.show_error_message("Import Error", message)
    
    
    @Slot(bool, str)
    def on_camera_started(self, success, message):
        """Handle camera started signal"""
        if success:
            self.camera_running = True
            self.start_camera_button.setEnabled(False)
            self.stop_camera_button.setEnabled(True)
            self.capture_positive_button.setEnabled(True)
            self.capture_negative_button.setEnabled(True)
            self.main_window.show_status_message("Camera started", 3000)
        else:
            self.main_window.show_error_message("Camera Error", message)
    
    @Slot()
    def on_camera_stopped(self):
        """Handle camera stopped signal"""
        self.camera_running = False
        self.start_camera_button.setEnabled(True)
        self.stop_camera_button.setEnabled(False)
        self.capture_positive_button.setEnabled(False)
        self.capture_negative_button.setEnabled(False)
        self.camera_preview.setText("Camera not started")
        self.camera_preview.setPixmap(QPixmap())
        self.main_window.show_status_message("Camera stopped", 3000)
    
    @Slot(np.ndarray)
    def on_frame_captured(self, frame):
        """Handle new frame from camera"""
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        label_size = self.camera_preview.size()
        scaled_pixmap = QPixmap.fromImage(q_image).scaled(
            label_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.camera_preview.setPixmap(scaled_pixmap)
    
    @Slot(bool, str)
    def on_image_saved(self, success, path):
        """Handle image saved signal"""
        if success:
            self.update_image_counts()
        else:
            self.main_window.show_error_message("Error", f"Failed to save image: {path}")
    
    @Slot(str, int)
    def on_import_started(self, class_type, total_files):
        """Handle import started signal"""
        self.import_progress_bar.setRange(0, total_files)
        self.import_progress_bar.setValue(0)
        self.import_status_label.setText(f"Importing {total_files} {class_type} images...")
        
        self.import_positive_folder_button.setEnabled(False)
        self.import_positive_files_button.setEnabled(False)
        self.import_negative_folder_button.setEnabled(False)
        self.import_negative_files_button.setEnabled(False)
    
    @Slot(int, int)
    def on_import_progress(self, current, total):
        """Handle import progress signal"""
        self.import_progress_bar.setValue(current)
        self.import_status_label.setText(f"Importing {current}/{total} images...")
    
    @Slot(bool, str, int)
    def on_import_finished(self, success, message, total_imported):
        """Handle import finished signal"""
        self.import_positive_folder_button.setEnabled(True)
        self.import_positive_files_button.setEnabled(True)
        self.import_negative_folder_button.setEnabled(True)
        self.import_negative_files_button.setEnabled(True)
        
        self.import_status_label.setText(message)
        self.update_image_counts()
        
        if success:
            self.main_window.show_status_message(f"Imported {total_imported} images", 3000)