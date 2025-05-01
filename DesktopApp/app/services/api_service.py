#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Service - Handles communication with the backend API
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker

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

        # Error handling flags
        self.connection_error = False
        self.last_error_time = None
        self.retry_delay = 60  # seconds before allowing another retry after error
        
        # Thread safety
        self.api_mutex = QMutex()
        
        # Cache for API responses
        self.cache = {}
        self.cache_lifetime = {
            'api/models': 300,  # 5 minutes
            'api/devices': 30,   # 30 seconds
            'api/results': 30    # 30 seconds
        }
    
    def close(self):
        """Close the API service"""
        if self.session:
            self.session.close()
        self.thread_manager.clear()
    
    def _execute_in_thread(self, endpoint, method_name, *args, **kwargs):
        """Execute an API method in a separate thread"""
        # Extract cache control from kwargs if present
        skip_cache = kwargs.pop('skip_cache', False)
        
        # Check if we can use cached data
        cache_key = endpoint
        if kwargs.get('params'):
            # Add params to cache key
            cache_key += str(kwargs['params'])
        
        if not skip_cache and self._check_cache(cache_key):
            return
            
        # Signal that request is starting
        self.request_started.emit(endpoint)
            
        worker = ApiWorker(self, endpoint, method_name, *args, **kwargs)
        
        # Connect signals
        worker.signals.started.connect(self.request_started)
        worker.signals.finished.connect(self._handle_request_finished)
        worker.signals.error.connect(self.request_error)
        
        # Start the worker in the thread pool
        self.thread_manager.start_worker(worker)
    
    def _handle_request_finished(self, endpoint, success, data):
        """Internal handler for finished requests to manage caching"""
        # Cache successful responses
        if success:
            cache_key = endpoint
            if isinstance(data, dict) and not any(x in endpoint for x in ['create', 'upload', 'delete']):
                with QMutexLocker(self.api_mutex):
                    self.cache[cache_key] = {
                        'data': data,
                        'timestamp': datetime.now()
                    }
        
        # Forward the signal
        self.request_finished.emit(endpoint, success, data)
    
    def _check_cache(self, cache_key):
        """Check if we have a valid cached response"""
        base_endpoint = cache_key.split('?')[0]
        lifetime = next((v for k, v in self.cache_lifetime.items() if k in base_endpoint), 0)
        
        if lifetime == 0:
            return False
            
        with QMutexLocker(self.api_mutex):
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                age = (datetime.now() - cache_entry['timestamp']).total_seconds()
                
                if age < lifetime:
                    # Use cached data
                    self.request_finished.emit(cache_key, True, cache_entry['data'])
                    return True
        
        return False
    
    def clear_cache(self, endpoint_pattern=None):
        """
        Clear the response cache
        
        Args:
            endpoint_pattern: Optional string to match specific endpoints to clear
                            If None, clears all cache
        """
        with QMutexLocker(self.api_mutex):
            if endpoint_pattern:
                # Clear only matching endpoints
                keys_to_remove = [key for key in self.cache.keys() if endpoint_pattern in key]
                for key in keys_to_remove:
                    del self.cache[key]
            else:
                # Clear all cache
                self.cache.clear()
    
    def reset_connection(self):
        """Reset connection error state"""
        with QMutexLocker(self.api_mutex):
            self.connection_error = False
            self.last_error_time = None

    def get_api_url(self):
        """Get the configured API endpoint URL"""
        return self.config.api_endpoint
    
    def set_api_url(self, url):
        """Set the API endpoint URL"""
        self.config.api_endpoint = url
        self.config.save_config()
        
        # Clear cache when API URL changes
        with QMutexLocker(self.api_mutex):
            self.cache.clear()
    
    def clear_cache(self):
        """Clear the response cache"""
        with QMutexLocker(self.api_mutex):
            self.cache.clear()
    
    def delete_device(self, device_id, hard_delete=False):
        params = {'hard': 'true'} if hard_delete else None
        self._execute_in_thread(f'api/devices/{device_id}', '_handle_request', 
                            f'api/devices/{device_id}', 'DELETE', params=params)
        
        # Clear cache for devices
        with QMutexLocker(self.api_mutex):
            for key in list(self.cache.keys()):
                if 'api/devices' in key:
                    del self.cache[key]

    def delete_model(self, model_id, hard_delete=False):
        params = {'hard': 'true'} if hard_delete else None
        self._execute_in_thread(f'api/models/{model_id}', '_handle_request', 
                            f'api/models/{model_id}', 'DELETE', params=params)
        
        # Clear cache for models and devices (since they might reference this model)
        with QMutexLocker(self.api_mutex):
            for key in list(self.cache.keys()):
                if 'api/models' in key or 'api/devices' in key:
                    del self.cache[key]

    def get_model_download_url(self, model_id):
        """Get a pre-signed URL for downloading a model
        
        Args:
            model_id: UUID of the model
        """
        self._execute_in_thread(f'api/models/{model_id}/download', '_handle_request', 
                            f'api/models/{model_id}/download', 'GET')
        
    def _handle_request(self, endpoint, method, data=None, files=None, json_data=None, params=None):
        """Handle API requests with error handling - NO signal emissions"""
        with QMutexLocker(self.api_mutex):
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
        
        headers = {
            'X-API-Key': self.config.api_key
        }

        print(headers)

        try:
            if method.lower() == 'get':
                response = self.session.get(full_url, params=params, headers=headers, timeout=10)
            elif method.lower() == 'post':
                response = self.session.post(full_url, data=data, files=files, json=json_data, headers=headers, timeout=10)
            elif method.lower() == 'put':
                response = self.session.put(full_url, data=data, json=json_data, headers=headers, timeout=10)
            elif method.lower() == 'delete':
                response = self.session.delete(full_url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            with QMutexLocker(self.api_mutex):
                # Reset error state on successful connection
                self.connection_error = False
                self.last_error_time = None
            
            # Check if request was successful
            response.raise_for_status()
            # Parse JSON response
            response_data = response.json() if response.content else None
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            with QMutexLocker(self.api_mutex):
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
                    with open(model_path, 'rb') as model_file, open(metadata_path, 'rb') as metadata_file:
                        files = {
                            'model': model_file,
                            'metadata': metadata_file
                        }
                        
                        try:
                            # Get the API URL
                            full_url = f"{self.api_service.get_api_url()}/api/models/create"
                            
                            headers = {
                                'X-API-Key': self.api_service.config.api_key
                            }

                            # Make the request directly instead of using _handle_request
                            response = self.api_service.session.post(
                                full_url, 
                                files=files, 
                                headers=headers,
                                timeout=30  # Longer timeout for uploads
                            )
                            
                            # Check if request was successful
                            response.raise_for_status()
                            
                            # Parse JSON response
                            result = response.json() if response.content else None
                            
                            # Clear cache after upload
                            self.api_service.clear_cache()
                            
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
        self._execute_in_thread('api/devices', '_handle_request', 'api/devices', 'GET')
    
    def get_device(self, device_id):
        """Get specific device details"""
        self._execute_in_thread(f'api/devices/{device_id}', '_handle_request', f'api/devices/{device_id}', 'GET')
    
    def register_device(self, device_name):
        """Register a new device"""
        self._execute_in_thread('api/devices/register', '_handle_request', 'api/devices/register', 'POST', 
                               json_data={'device_name': device_name})
        
        with QMutexLocker(self.api_mutex):
            for key in list(self.cache.keys()):
                if 'api/devices' in key:
                    del self.cache[key]
    
    def set_device_model(self, device_id, model_id):
        """Assign a model to a device"""
        self._execute_in_thread(f'api/devices/{device_id}/set_model', '_handle_request', 
                               f'api/devices/{device_id}/set_model', 'POST', 
                               json_data={'model_id': model_id})
        
        # Clear cache for devices and results
        with QMutexLocker(self.api_mutex):
            for key in list(self.cache.keys()):
                if 'api/devices' in key or 'api/results' in key:
                    del self.cache[key]
    
    # Results API methods
    def get_results(self, device_id=None, model_id=None, limit=50):
        """Get classification results with optional filtering"""
        params = {'limit': limit}
        
        if device_id:
            params['device_id'] = device_id
        
        if model_id:
            params['model_id'] = model_id
        
        cache_key = f"api/results?{json.dumps(params)}"
        self._execute_in_thread(cache_key, '_handle_request', 'api/results', 'GET', params=params)

    def get_result(self, result_id):
        """Get specific result details"""
        self._execute_in_thread(f'api/results/{result_id}', '_handle_request', f'api/results/{result_id}', 'GET')