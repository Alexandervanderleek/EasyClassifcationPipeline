#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Service - Handles communication with the backend API
"""

import os
import json
import time
import requests
from PySide6.QtCore import QObject, Signal

from app.services.worker_service import ApiWorker, ThreadManager

class ApiService(QObject):
    """Service for interacting with the backend API"""
    
    # Define signals for API responses
    request_started = Signal(str)
    request_finished = Signal(str, bool, object)  # endpoint, success, data
    request_error = Signal(str, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        self.thread_manager = ThreadManager()

        self.cache = {}
        self.cache_expiry = 30  # seconds

        # Error handling flags
        self.connection_error = False
        self.last_error_time = None
        self.retry_delay = 60  # seconds before allowing another retry after error
    
    def close(self):
        """Close the API service"""
        if self.session:
            self.session.close()
        self.thread_manager.clear()
    
    def _execute_in_thread(self, endpoint, method_name, *args, **kwargs):
        """Execute an API method in a separate thread"""
        worker = ApiWorker(self, endpoint, method_name, *args, **kwargs)
        
        # Connect signals
        worker.signals.started.connect(self.request_started)
        worker.signals.finished.connect(self.request_finished)
        worker.signals.error.connect(self.request_error)
        
        # Start the worker in the thread pool
        self.thread_manager.start_worker(worker)
    
    def reset_connection(self):
        """Reset connection error state"""
        self.connection_error = False
        self.last_error_time = None

    def get_api_url(self):
        """Get the configured API endpoint URL"""
        return self.config.api_endpoint
    
    def set_api_url(self, url):
        """Set the API endpoint URL"""
        self.config.api_endpoint = url
        self.config.save_config()
    
    def _handle_request(self, endpoint, method, data=None, files=None, json_data=None, params=None):
        """Handle API requests with error handling - NO signal emissions"""
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
        
        try:
            if method.lower() == 'get':
                response = self.session.get(full_url, params=params, timeout=10)
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
            
            # Update cache for models (no signal emission)
            if 'models' in endpoint and not self.connection_error:
                self.cache['models'] = {
                    'data': response_data,
                    'timestamp': time.time()
                }

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
                
            return error_info
    
    # Model API methods
    def get_models(self):
        """Get list of all models from the API"""
        if 'models' in self.cache and time.time() - self.cache['models']['timestamp'] < self.cache_expiry:
            self.request_finished.emit('api/models', True, self.cache['models']['data'])
        
        # Execute the request in a separate thread
        self._execute_in_thread('api/models', '_handle_request', 'api/models', 'GET')
    
    def get_model(self, model_id):
        """Get specific model details"""
        self._execute_in_thread('api/models/' + model_id, '_handle_request', f'api/models/{model_id}', 'GET')
    
    def upload_model(self, model_path, metadata_path):
        """Upload a model to the API"""
        # Create a worker for this specific task
        class UploadModelWorker(ApiWorker):
            def run(self):
                try:
                    self.signals.started.emit('api/models/create')
                    
                    # Open files
                    files = {
                        'model': open(model_path, 'rb'),
                        'metadata': open(metadata_path, 'rb')
                    }
                    
                    try:
                        # Get the API URL
                        full_url = f"{self.api_service.get_api_url()}/api/models/create"
                        
                        # Make the request directly instead of using _handle_request
                        response = self.api_service.session.post(
                            full_url, 
                            files=files, 
                            timeout=10
                        )
                        
                        # Check if request was successful
                        response.raise_for_status()
                        
                        # Parse JSON response
                        result = response.json() if response.content else None
                        
                        # Emit success result
                        self.signals.finished.emit('api/models/create', True, result)
                        
                    except requests.exceptions.RequestException as e:
                        # Handle error
                        error_info = {
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                        
                        # Emit error result
                        self.signals.finished.emit('api/models/create', False, error_info)
                        
                    finally:
                        # Close file handles (in finally to ensure they're closed)
                        for f in files.values():
                            f.close()
                        
                except Exception as e:
                    self.signals.error.emit('api/models/create', str(e))
        
        # Create the worker
        worker = UploadModelWorker(self, 'api/models/create', '_handle_request')
        
        # Connect signals
        worker.signals.started.connect(self.request_started)
        worker.signals.finished.connect(self.request_finished)
        worker.signals.error.connect(self.request_error)
        
        # Start the worker
        self.thread_manager.start_worker(worker)

    def health_check(self):
        """Check if the API server is reachable"""
        self._execute_in_thread('api/health', '_handle_request', 'api/health', 'GET')

    def get_devices(self):
        """Get list of all registered devices"""
        # Check cache first
        if 'devices' in self.cache and time.time() - self.cache['devices']['timestamp'] < self.cache_expiry:
            self.request_finished.emit('api/devices', True, self.cache['devices']['data'])
        
        self._execute_in_thread('api/devices', '_handle_request', 'api/devices', 'GET')
    
    def get_device(self, device_id):
        """Get specific device details"""
        self._execute_in_thread(f'api/devices/{device_id}', '_handle_request', f'api/devices/{device_id}', 'GET')
    
    def register_device(self, device_name):
        """Register a new device"""
        self._execute_in_thread('api/devices/register', '_handle_request', 'api/devices/register', 'POST', 
                               json_data={'device_name': device_name})
    
    def set_device_model(self, device_id, model_id):
        """Assign a model to a device"""
        self._execute_in_thread(f'api/devices/{device_id}/set_model', '_handle_request', 
                               f'api/devices/{device_id}/set_model', 'POST', 
                               json_data={'model_id': model_id})
        
    
    # Results API methods
    def get_results(self, device_id=None, model_id=None, limit=50):
        """Get classification results with optional filtering"""
        params = {'limit': limit}
        
        if device_id:
            params['device_id'] = device_id
        
        if model_id:
            params['model_id'] = model_id
        
        self._execute_in_thread('api/results', '_handle_request', 'api/results', 'GET', params=params)

    def get_result(self, result_id):
        """Get specific result details"""
        self._execute_in_thread(f'api/results/{result_id}', '_handle_request', f'api/results/{result_id}', 'GET')