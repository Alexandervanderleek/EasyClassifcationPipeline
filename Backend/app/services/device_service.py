from flask import current_app
from app.repositories import DeviceRepository, ModelRepository

class DeviceService:
    """Service for device business logic"""
    
    @staticmethod
    def get_all_devices():
        """
        Get all active devices
        
        Returns:
            List of devices in dictionary format
        """
        devices = DeviceRepository.get_all()
        return [device.to_dict() for device in devices]
    
    @staticmethod
    def get_device(device_id):
        """
        Get a device by ID
        
        Args:
            device_id: The UUID of the device
            
        Returns:
            Device as dictionary or None if not found
        """
        device = DeviceRepository.get_by_id(device_id)
        return device.to_dict() if device else None
    
    @staticmethod
    def register_device(device_name):
        """
        Register a new device
        
        Args:
            device_name: Name of the device
            
        Returns:
            Created device as dictionary or error message
        """
        try:
            device = DeviceRepository.create(device_name)
            
            return {
                'success': True,
                'device_id': str(device.device_id),
                'message': 'Device registered successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Error registering device: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def set_device_model(device_id, model_id):
        """
        Set the model for a device
        
        Args:
            device_id: UUID of the device
            model_id: UUID of the model (or None to unassign)
            
        Returns:
            Success message or error
        """
        try:
            if model_id and not ModelRepository.get_by_id(model_id):
                return {
                    'success': False,
                    'error': 'Model not found'
                }
            
            device = DeviceRepository.update_model(device_id, model_id)
            
            if not device:
                return {
                    'success': False,
                    'error': 'Device not found'
                }
            
            return {
                'success': True,
                'message': 'Model set successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Error setting device model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_heartbeat(device_id, status=None):
        """
        Update device heartbeat and status
        
        Args:
            device_id: UUID of the device
            status: New status (optional)
            
        Returns:
            Updated device info with model details
        """
        try:
            device = DeviceRepository.update_heartbeat(device_id, status)
            
            if not device:
                return {
                    'error': 'Device not found'
                }
            
            model_id = device.current_model_id
            model = None
            should_download = False
            
            if model_id:
                model = ModelRepository.get_by_id(model_id)
                if model:
                    should_download = True
            
            model_data = model.to_dict() if model else None
            return {
                'model_id': str(model_id) if model_id else None,
                'should_download': should_download,
                'metadata': model_data['metadata'] if model_data else None  
            }
        except Exception as e:
            current_app.logger.error(f"Error updating heartbeat: {str(e)}")
            return {
                'error': str(e)
            }
    
    @staticmethod
    def delete_device(device_id, hard_delete=False):
        """
        Delete a device
        
        Args:
            device_id: UUID of the device to delete
            hard_delete: Whether to permanently delete the device
            
        Returns:
            Success message or error
        """
        try:
            if hard_delete:
                success = DeviceRepository.hard_delete(device_id)
            else:
                success = DeviceRepository.delete(device_id)
            
            if not success:
                return {
                    'success': False,
                    'error': 'Device not found or could not be deleted'
                }
            
            return {
                'success': True,
                'message': 'Device deleted successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Error deleting device: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }