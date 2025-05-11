"""
Camera Service - Handles camera operations
"""

import os
import cv2
import time
import threading
import numpy as np
from PySide6.QtCore import QObject, Signal, QThread, QMutex, QMutexLocker

class CameraThread(QThread):
    """Thread for camera capture to avoid blocking the UI"""
    
    frame_ready = Signal(np.ndarray)
    error_occurred = Signal(str)
    
    def __init__(self, camera_index=0, frame_rate=30):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None
        self.frame_rate = frame_rate
        self.mutex = QMutex()
    
    def run(self):
        """Thread main loop"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                self.error_occurred.emit(f"Failed to open camera at index {self.camera_index}")
                return
                
            with QMutexLocker(self.mutex):
                self.running = True
            
            while self.is_running():
                ret, frame = self.cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.frame_ready.emit(frame_rgb)
                else:
                    self.error_occurred.emit("Failed to capture frame from camera")
                    break
                
                time.sleep(1.0 / self.frame_rate)
                
        except Exception as e:
            self.error_occurred.emit(f"Camera error: {str(e)}")
        finally:
            self.release_camera()
    
    def is_running(self):
        """Thread-safe check if camera is running"""
        with QMutexLocker(self.mutex):
            return self.running
    
    def stop(self):
        """Stop the camera thread"""
        with QMutexLocker(self.mutex):
            self.running = False
        
        self.wait()
        self.release_camera()
    
    def release_camera(self):
        """Release the camera resource"""
        if self.cap:
            self.cap.release()
            self.cap = None

class CameraService(QObject):
    """Service for camera operations"""
    
    camera_started = Signal(bool, str)
    camera_stopped = Signal()
    frame_captured = Signal(np.ndarray)
    image_saved = Signal(bool, str) 
    error_occurred = Signal(str) 
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.camera_thread = None
        self.current_frame = None
        self.mutex = QMutex()
    
    def start_camera(self, camera_index=None):
        """Start the camera capture thread"""
        with QMutexLocker(self.mutex):
            if self.camera_thread and self.camera_thread.is_running():
                return False, "Camera already running"
            
            if camera_index is None:
                camera_index = self.config.camera_index
            else:
                self.config.camera_index = camera_index
        
        try:
            self.camera_thread = CameraThread(camera_index)
            self.camera_thread.frame_ready.connect(self.on_frame_ready)
            self.camera_thread.error_occurred.connect(self.on_camera_error)
            self.camera_thread.start()
            
            self.camera_started.emit(True, "Camera started")
            return True, "Camera started"
            
        except Exception as e:
            self.camera_started.emit(False, str(e))
            return False, f"Failed to start camera: {str(e)}"
    
    def stop_camera(self):
        """Stop the camera capture thread"""
        with QMutexLocker(self.mutex):
            if self.camera_thread:
                self.camera_thread.stop()
                self.camera_thread = None
                self.current_frame = None
                
                self.camera_stopped.emit()
    
    def capture_image(self, class_type, project_path):
        """Capture the current frame and save it to the specified class folder"""
        with QMutexLocker(self.mutex):
            if not self.current_frame is not None:
                return False, "No camera frame available"
            
            frame_copy = self.current_frame.copy() if self.current_frame is not None else None
        
        if frame_copy is None:
            return False, "No camera frame available"
        
        try:
            class_dir = os.path.join(project_path, "dataset", class_type)
            os.makedirs(class_dir, exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            img_path = os.path.join(class_dir, f"img_{timestamp}.jpg")
            
            frame_bgr = cv2.cvtColor(frame_copy, cv2.COLOR_RGB2BGR)
            cv2.imwrite(img_path, frame_bgr)
            
            self.image_saved.emit(True, img_path)
            return True, img_path
            
        except Exception as e:
            error_msg = f"Failed to save image: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.image_saved.emit(False, error_msg)
            return False, error_msg
    
    def on_frame_ready(self, frame):
        """Handle a new frame from the camera thread"""
        with QMutexLocker(self.mutex):
            self.current_frame = frame
        
        self.frame_captured.emit(frame)
    
    def on_camera_error(self, error_message):
        """Handle camera errors"""
        self.error_occurred.emit(error_message)
        self.stop_camera()