"""
Train Tab - Train and convert models
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QGroupBox, QSpinBox, QDoubleSpinBox,
    QProgressBar, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Slot

class TrainTab(QWidget):
    """Tab for training and converting models"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = main_window.config
        self.model_service = main_window.model_service
        
        self.model_service.training_started.connect(self.on_training_started)
        self.model_service.training_progress.connect(self.on_training_progress)
        self.model_service.training_finished.connect(self.on_training_finished)
        
        self.model_service.conversion_started.connect(self.on_conversion_started)
        self.model_service.conversion_progress.connect(self.on_conversion_progress)
        self.model_service.conversion_finished.connect(self.on_conversion_finished)
        
        self.setup_ui()
        
        self.project_path = None
        self.is_training = False
        self.is_converting = False
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        params_group = QGroupBox("Training Parameters")
        params_layout = QFormLayout(params_group)
        
        self.epochs_spinbox = QSpinBox()
        self.epochs_spinbox.setMinimum(1)
        self.epochs_spinbox.setMaximum(100)
        self.epochs_spinbox.setValue(self.config.default_epochs)
        params_layout.addRow("Epochs:", self.epochs_spinbox)
        
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setMinimum(1)
        self.batch_size_spinbox.setMaximum(128)
        self.batch_size_spinbox.setValue(self.config.default_batch_size)
        params_layout.addRow("Batch Size:", self.batch_size_spinbox)
        
        self.learning_rate_spinbox = QDoubleSpinBox()
        self.learning_rate_spinbox.setDecimals(6)
        self.learning_rate_spinbox.setMinimum(0.000001)
        self.learning_rate_spinbox.setMaximum(0.1)
        self.learning_rate_spinbox.setSingleStep(0.0001)
        self.learning_rate_spinbox.setValue(self.config.default_learning_rate)
        params_layout.addRow("Learning Rate:", self.learning_rate_spinbox)
        
        top_layout.addWidget(params_group)
        
        buttons_group = QGroupBox("Actions")
        buttons_layout = QHBoxLayout(buttons_group)
        
        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        buttons_layout.addWidget(self.train_button)
        
        self.convert_button = QPushButton("Convert to TFLite")
        self.convert_button.clicked.connect(self.convert_model)
        self.convert_button.setEnabled(False)
        buttons_layout.addWidget(self.convert_button)
        
        top_layout.addWidget(buttons_group)
        
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        
        top_layout.addWidget(progress_group)
        
        status_group = QGroupBox("Model Status")
        status_layout = QFormLayout(status_group)
        
        self.model_status_label = QLabel("Not trained")
        status_layout.addRow("Model:", self.model_status_label)
        
        self.tflite_status_label = QLabel("Not converted")
        status_layout.addRow("TFLite:", self.tflite_status_label)
        
        top_layout.addWidget(status_group)
        
        splitter.addWidget(top_widget)
        
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        log_group = QGroupBox("Training Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        bottom_layout.addWidget(log_group)
        
        splitter.addWidget(bottom_widget)
        
        splitter.setSizes([300, 200])
    
    def on_project_changed(self, project_name, project_path):
        """Handle project change"""
        self.project_path = project_path
        self.update_model_status()
        
        self.log_text.clear()
    
    def on_tab_selected(self):
        """Handle when this tab is selected"""
        if self.project_path:
            self.update_model_status()
    
    def update_model_status(self):
        """Update the model status labels"""
        if not self.project_path:
            return
        
        model_path = os.path.join(self.project_path, "models", "model.h5")
        tflite_path = os.path.join(self.project_path, "models", "model.tflite")
        
        if os.path.exists(model_path):
            self.model_status_label.setText("Trained")
            self.convert_button.setEnabled(True)
        else:
            self.model_status_label.setText("Not trained")
            self.convert_button.setEnabled(False)
        
        if os.path.exists(tflite_path):
            self.tflite_status_label.setText("Converted")
        else:
            self.tflite_status_label.setText("Not converted")
    
    def train_model(self):
        """Start model training"""
        if not self.project_path:
            self.main_window.show_error_message("Error", "No project selected")
            return
        
        if self.is_training:
            return
        
        epochs = self.epochs_spinbox.value()
        batch_size = self.batch_size_spinbox.value()
        learning_rate = self.learning_rate_spinbox.value()
        
        success, message = self.model_service.train_model(
            self.project_path,
            epochs,
            batch_size,
            learning_rate
        )
        
        if not success:
            self.main_window.show_error_message("Training Error", message)
    
    def convert_model(self):
        """Convert model to TFLite format"""
        if not self.project_path:
            self.main_window.show_error_message("Error", "No project selected")
            return
        
        if self.is_converting:
            return
        
        success, message = self.model_service.convert_to_tflite(self.project_path)
        
        if not success:
            self.main_window.show_error_message("Conversion Error", message)
    
    
    @Slot()
    def on_training_started(self):
        """Handle training started signal"""
        self.is_training = True
        
        self.train_button.setEnabled(False)
        self.convert_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Training in progress...")
        
        self.log_text.clear()
        self.log_text.append("Training started...\n")
        
        self.main_window.show_status_message("Training started", 3000)
    
    @Slot(int, dict)
    def on_training_progress(self, epoch, logs):
        """Handle training progress signal"""
        progress = int(epoch / self.epochs_spinbox.value() * 100)
        self.progress_bar.setValue(progress)
        
        self.progress_label.setText(f"Training epoch {epoch}/{self.epochs_spinbox.value()}")
        
        log_text = f"Epoch {epoch}/{self.epochs_spinbox.value()}: "
        log_text += f"loss={logs.get('loss', 0):.4f}, "
        log_text += f"accuracy={logs.get('accuracy', 0):.4f}, "
        log_text += f"val_loss={logs.get('val_loss', 0):.4f}, "
        log_text += f"val_accuracy={logs.get('val_accuracy', 0):.4f}"
        
        self.log_text.append(log_text)
        
        self.log_text.ensureCursorVisible()
    
    @Slot(bool, str)
    def on_training_finished(self, success, message):
        """Handle training finished signal"""
        self.is_training = False
        
        self.train_button.setEnabled(True)
        self.progress_label.setText(message)
        
        if success:
            self.log_text.append("\nTraining completed successfully!")
            self.main_window.show_status_message("Training completed", 3000)
            
            self.update_model_status()
        else:
            self.log_text.append(f"\nTraining failed: {message}")
            self.main_window.show_error_message("Training Error", message)
    
    @Slot()
    def on_conversion_started(self):
        """Handle conversion started signal"""
        self.is_converting = True
        
        self.train_button.setEnabled(False)
        self.convert_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Converting to TFLite...")
        
        self.log_text.append("\nConverting model to TFLite format...")
        
        self.main_window.show_status_message("Converting model", 3000)
    
    @Slot(int)
    def on_conversion_progress(self, progress):
        """Handle conversion progress signal"""
        self.progress_bar.setValue(progress)
    
    @Slot(bool, str)
    def on_conversion_finished(self, success, message):
        """Handle conversion finished signal"""
        self.is_converting = False
        
        self.train_button.setEnabled(True)
        self.convert_button.setEnabled(True)
        self.progress_label.setText(message)
        
        if success:
            self.log_text.append("Conversion completed successfully!")
            self.main_window.show_status_message("Conversion completed", 3000)
            
            self.update_model_status()
        else:
            self.log_text.append(f"Conversion failed: {message}")
            self.main_window.show_error_message("Conversion Error", message)