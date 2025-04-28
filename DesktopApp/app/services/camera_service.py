#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Camera Service - Handles camera operations
"""

import os
import cv2
import time
import threading
import numpy as np
from PySide6.QtCore import QObject, Signal, QThread

class CameraThread(QThread):
    """Thread for camera capture to avoid blocking the UI"""
    
    # Define signal for frame capture
    frame_ready = Signal(np.ndarray)
    
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None
    
    def run(self):
        """Thread main loop"""
        self.cap = cv2.VideoCapture(self.camera_index)
        self.running = True
        
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                # Convert BGR to RGB for Qt
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame_ready.emit(frame_rgb)
            
            # Sleep to control frame rate (30 FPS)
            time.sleep(0.033)
    
    def stop(self):
        """Stop the camera thread"""
        self.running = False
        self.wait()  # Wait for thread to finish
        
        if self.cap:
            self.cap.release()
            self.cap = None

class CameraService(QObject):
    """Service for camera operations"""
    
    # Define signals
    camera_started = Signal(bool, str)  # success, message
    camera_stopped = Signal()
    frame_captured = Signal(np.ndarray)  # RGB frame
    image_saved = Signal(bool, str)  # success, path
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.camera_thread = None
        self.current_frame = None
    
    def start_camera(self, camera_index=None):
        """Start the camera capture thread"""
        if self.camera_thread and self.camera_thread.running:
            return False, "Camera already running"
        
        if camera_index is None:
            camera_index = self.config.camera_index
        else:
            self.config.camera_index = camera_index
        
        try:
            # Create and start the camera thread
            self.camera_thread = CameraThread(camera_index)
            self.camera_thread.frame_ready.connect(self.on_frame_ready)
            self.camera_thread.start()
            
            # Emit signal
            self.camera_started.emit(True, "Camera started")
            return True, "Camera started"
            
        except Exception as e:
            self.camera_started.emit(False, str(e))
            return False, f"Failed to start camera: {str(e)}"
    
    def stop_camera(self):
        """Stop the camera capture thread"""
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
            self.current_frame = None
            
            # Emit signal
            self.camera_stopped.emit()
    
    def capture_image(self, class_type, project_path):
        """Capture the current frame and save it to the specified class folder"""
        if not self.current_frame is not None:
            return False, "No camera frame available"
        
        try:
            # Save the image
            timestamp = int(time.time() * 1000)
            img_path = os.path.join(project_path, "dataset", class_type, f"img_{timestamp}.jpg")
            
            # Convert RGB back to BGR for OpenCV
            frame_bgr = cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(img_path, frame_bgr)
            
            # Emit signal
            self.image_saved.emit(True, img_path)
            return True, img_path
            
        except Exception as e:
            self.image_saved.emit(False, str(e))
            return False, f"Failed to save image: {str(e)}"
    
    def on_frame_ready(self, frame):
        """Handle a new frame from the camera thread"""
        self.current_frame = frame
        self.frame_captured.emit(frame)