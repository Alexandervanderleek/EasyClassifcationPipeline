from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal

class FirstRunDialog(QDialog):
    """Dialog for first run setup to collect API credentials"""
    
    setup_complete = Signal(str, str)  
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial Setup")
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        welcome_label = QLabel(
            "Welcome to the ML Classifier Trainer!\n\n"
            "Before you get started, please configure your API connection settings. "
            "You'll need the URL of your backend server and an API key for authentication."
        )
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)
        
        form_layout = QFormLayout()
        
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("http://your-server.com:5000")
        form_layout.addRow("API Server URL:", self.api_url_input)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Your API key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API Key:", self.api_key_input)
        
        layout.addLayout(form_layout)
        
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_connection)
        layout.addWidget(test_button)
        
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save and Continue")
        self.save_button.clicked.connect(self.accept_settings)
        self.save_button.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def test_connection(self):
        """Test connection to the API server"""
        api_url = self.api_url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        if not api_url:
            QMessageBox.warning(self, "Missing Information", "Please enter the API server URL")
            return
        
        if not api_key:
            QMessageBox.warning(self, "Missing Information", "Please enter your API key")
            return
        
        import requests
        from PySide6.QtWidgets import QProgressDialog
        
        progress = QProgressDialog("Testing connection...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Connection Test")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        try:
            response = requests.get(f"{api_url}/api/health", 
                                  headers={"X-API-Key": api_key},
                                  timeout=10)
            
            progress.close()
            
            if response.status_code == 200:
                QMessageBox.information(self, "Connection Successful", 
                                      "Successfully connected to the API server!")
            else:
                QMessageBox.warning(self, "Connection Failed", 
                                  f"Connection failed with status code: {response.status_code}\n\n"
                                  f"Message: {response.text}")
        except Exception as e:
            progress.close()
            
            QMessageBox.critical(self, "Connection Error", 
                               f"Failed to connect to the API server:\n\n{str(e)}")
    
    def accept_settings(self):
        """Save settings and close dialog"""
        api_url = self.api_url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        if not api_url:
            QMessageBox.warning(self, "Missing Information", "Please enter the API server URL")
            return
        
        if not api_key:
            QMessageBox.warning(self, "Missing Information", "Please enter your API key")
            return
        
        self.setup_complete.emit(api_url, api_key)
        
        self.accept()