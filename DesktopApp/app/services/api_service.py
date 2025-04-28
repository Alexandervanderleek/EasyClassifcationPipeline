#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Service - Handles communication with the backend API
"""

import os
import json
import requests
from PySide6.QtCore import QObject, Signal

class ApiService(QObject):
    """Service for interacting with the backend API"""
    
    # Define signals for API responses
    request_started = Signal(str)
    request_finished = Signal(str, bool, object)  # endpoint, success, data
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        
        # Error handling flags
        self.connection_error = False
        self.last_error_time = None
        self.retry_delay = 60  # seconds before allowing another retry after error
    
    def close(self):
        """Close the API service"""
        if self.session:
            self.session.close()
    
    def get_api_url(self):
        """Get the configured API endpoint URL"""
        return self.config.api_endpoint
    
    def set_api_url(self, url):
        """Set the API endpoint URL"""
        self.config.api_endpoint = url
        self.config.save_config()
    
    def _handle_request(self, endpoint, method, data=None, files=None, json_data=None, params=None):
        """Handle API requests with error handling and signals"""
        import time
        from datetime import datetime, timedelta
        
        # Check if we're in an error state and should delay retries
        current_time = datetime.now()
        if self.connection_error and self.last_error_time:
            time_since_error = (current_time - self.last_error_time).total_seconds()
            if time_since_error < self.retry_delay:
                # Return cached error without making a new request
                error_info = {
                    'error_type': 'ConnectionBlocked',
                    'error_message': f'API connection failed. Retry in {int(self.retry_delay - time_since_error)} seconds.',
                    'is_retry_blocked': True,
                    'retry_after': int(self.retry_delay - time_since_error)
                }
                return error_info
        
        full_url = f"{self.get_api_url()}/{endpoint.lstrip('/')}"
        
        self.request_started.emit(endpoint)
        
        try:
            if method.lower() == 'get':
                response = self.session.get(full_url, params=params, timeout=10)  # Add timeout
            elif method.lower() == 'post':
                response = self.session.post(full_url, data=data, files=files, json=json_data, timeout=10)
            elif method.lower() == 'put':
                response = self.session.put(full_url, data=data, json=json_data, timeout=10)
            elif method.lower() == 'delete':
                response = self.session.delete(full_url, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Reset error state on successful connection
            self.connection_error = False
            self.last_error_time = None
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse JSON response
            response_data = response.json() if response.content else None
            
            self.request_finished.emit(endpoint, True, response_data)
            return response_data
            
        except requests.exceptions.RequestException as e:
            # Set error state
            self.connection_error = True
            self.last_error_time = current_time
            
            error_info = {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            
            # Handle connection errors specifically
            if isinstance(e, (requests.exceptions.ConnectionError, 
                              requests.exceptions.Timeout,
                              requests.exceptions.ConnectTimeout)):
                error_info['error_message'] = f"Could not connect to API server at {self.get_api_url()}. Please check your connection and API endpoint settings."
            
            # Try to get response data if available
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_info['status_code'] = e.response.status_code
                    error_info['response'] = e.response.json()
            except:
                pass
                
            self.request_finished.emit(endpoint, False, error_info)
            return error_info
    
    # Model API methods
    def get_models(self):
        """Get list of all models from the API"""
        return self._handle_request('api/models', 'GET')
    
    def get_model(self, model_id):
        """Get specific model details"""
        return self._handle_request(f'api/models/{model_id}', 'GET')
    
    def upload_model(self, model_path, metadata_path):
        """Upload a model to the API"""
        files = {
            'model': open(model_path, 'rb'),
            'metadata': open(metadata_path, 'rb')
        }
        
        try:
            return self._handle_request('api/models', 'POST', files=files)
        finally:
            # Close file handles
            for f in files.values():
                f.close()
    
    # Device API methods
    def get_devices(self):
        """Get list of all registered devices"""
        return self._handle_request('api/devices', 'GET')
    
    def get_device(self, device_id):
        """Get specific device details"""
        return self._handle_request(f'api/devices/{device_id}', 'GET')
    
    def register_device(self, device_name):
        """Register a new device"""
        return self._handle_request('api/devices/register', 'POST', json_data={'device_name': device_name})
    
    def set_device_model(self, device_id, model_id):
        """Assign a model to a device"""
        return self._handle_request(
            f'api/devices/{device_id}/set_model', 
            'POST', 
            json_data={'model_id': model_id}
        )
    
    # Results API methods
    def get_results(self, device_id=None, model_id=None, limit=50):
        """Get classification results with optional filtering"""
        params = {'limit': limit}
        
        if device_id:
            params['device_id'] = device_id
        
        if model_id:
            params['model_id'] = model_id
        
        return self._handle_request('api/results', 'GET', params=params)
    
    def get_result(self, result_id):
        """Get specific result details"""
        return self._handle_request(f'api/results/{result_id}', 'GET')