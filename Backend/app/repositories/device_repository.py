from datetime import datetime
from app import db
from app.models import Device

class DeviceRepository:
    """Repository for device data access"""
    
    @staticmethod
    def get_all(include_inactive=False):
        """
        Get all devices
        
        Args:
            include_inactive: Whether to include inactive/deleted devices
            
        Returns:
            List of Device objects
        """
        query = Device.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_by_id(device_id, include_inactive=False):
        """
        Get a device by ID
        
        Args:
            device_id: The UUID of the device
            include_inactive: Whether to include inactive/deleted devices
            
        Returns:
            Device object or None if not found
        """
        query = Device.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.filter_by(device_id=device_id).first()
    
    @staticmethod
    def create(device_name):
        """
        Create a new device
        
        Args:
            device_name: Name of the device
            
        Returns:
            Created Device object
        """
        device = Device(
            device_name=device_name,
            status='idle'
        )
        
        db.session.add(device)
        db.session.commit()
        
        return device
    
    @staticmethod
    def update_model(device_id, model_id):
        """
        Set the model for a device
        
        Args:
            device_id: UUID of the device
            model_id: UUID of the model (or None to unassign)
            
        Returns:
            Updated Device object or None if device not found
        """
        device = Device.query.filter_by(device_id=device_id, is_active=True).first()
        if not device:
            return None
        
        device.current_model_id = model_id
        device.last_active = datetime.utcnow()
        
        db.session.commit()
        return device
    
    @staticmethod
    def update_heartbeat(device_id, status=None):
        """
        Update device heartbeat and optionally status
        
        Args:
            device_id: UUID of the device
            status: New status (optional)
            
        Returns:
            Updated Device object or None if device not found
        """
        device = Device.query.filter_by(device_id=device_id, is_active=True).first()
        if not device:
            return None
        
        device.last_active = datetime.utcnow()
        if status:
            device.status = status
        
        db.session.commit()
        return device
    
    @staticmethod
    def delete(device_id):
        """
        Delete a device (soft delete)
        
        Args:
            device_id: UUID of the device to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        device = Device.query.get(device_id)
        if not device:
            return False
        
        device.is_active = False
        device.status = 'inactive'
        
        db.session.commit()
        return True
    
    @staticmethod
    def hard_delete(device_id):
        """
        Permanently delete a device
        
        Args:
            device_id: UUID of the device to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        device = Device.query.get(device_id)
        if not device:
            return False
        
        db.session.delete(device)
        db.session.commit()
        
        return True