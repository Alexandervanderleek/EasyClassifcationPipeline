from datetime import datetime
from app import db
from app.models import Result, Device, Model

class ResultRepository:
    """Repository for classification result data access"""
    
    @staticmethod
    def get_all(device_id=None, model_id=None, limit=50):
        """
        Get all results with optional filtering
        
        Args:
            device_id: Filter by device ID (optional)
            model_id: Filter by model ID (optional)
            limit: Maximum number of results to return
            
        Returns:
            List of Result objects
        """
        query = Result.query.join(Device).join(Model).filter(
            Device.is_active == True,
            Model.is_active == True
        )
        
        if device_id:
            query = query.filter(Result.device_id == device_id)
        
        if model_id:
            query = query.filter(Result.model_id == model_id)
        
        # Order by timestamp (newest first)
        query = query.order_by(Result.timestamp.desc())
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_by_id(result_id):
        """
        Get a result by ID
        
        Args:
            result_id: The UUID of the result
            
        Returns:
            Result object or None if not found
        """
        return Result.query.filter_by(result_id=result_id).first()
    
    @staticmethod
    def create(device_id, model_id, result_value, confidence, metadata=None):
        """
        Create a new classification result
        
        Args:
            device_id: UUID of the device that generated the result
            model_id: UUID of the model used for classification
            result_value: The classification result (e.g., 'positive', 'negative')
            confidence: The confidence score (0.0 to 1.0)
            metadata: Additional result metadata (optional)
            
        Returns:
            Created Result object
        """
        # Verify that device and model exist and are active
        device = Device.query.filter_by(device_id=device_id, is_active=True).first()
        model = Model.query.filter_by(model_id=model_id, is_active=True).first()
        
        if not device or not model:
            return None
        
        # Create result
        result = Result(
            device_id=device_id,
            model_id=model_id,
            result=result_value,
            confidence=confidence,
            result_metadata=metadata
        )
        
        # Update device last_active time
        device.last_active = datetime.utcnow()
        
        db.session.add(result)
        db.session.commit()
        
        return result
    
    @staticmethod
    def delete_by_device(device_id):
        """
        Delete all results for a given device (should rarely be used)
        
        Args:
            device_id: UUID of the device
            
        Returns:
            Number of results deleted
        """
        results = Result.query.filter_by(device_id=device_id).all()
        count = len(results)
        
        for result in results:
            db.session.delete(result)
        
        db.session.commit()
        return count
    
    @staticmethod
    def delete_by_model(model_id):
        """
        Delete all results for a given model (should rarely be used)
        
        Args:
            model_id: UUID of the model
            
        Returns:
            Number of results deleted
        """
        results = Result.query.filter_by(model_id=model_id).all()
        count = len(results)
        
        for result in results:
            db.session.delete(result)
        
        db.session.commit()
        return count