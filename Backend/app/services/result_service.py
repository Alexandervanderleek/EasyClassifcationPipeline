from flask import current_app
from app.repositories import ResultRepository, DeviceRepository

class ResultService:
    """Service for classification result business logic"""
    
    @staticmethod
    def get_all_results(device_id=None, model_id=None, limit=50):
        """
        Get all results with optional filtering
        
        Args:
            device_id: Filter by device ID (optional)
            model_id: Filter by model ID (optional)
            limit: Maximum number of results to return
            
        Returns:
            List of results in dictionary format
        """
        results = ResultRepository.get_all(device_id, model_id, limit)
        return [result.to_dict() for result in results]
    
    @staticmethod
    def get_result(result_id):
        """
        Get a result by ID
        
        Args:
            result_id: The UUID of the result
            
        Returns:
            Result as dictionary or None if not found
        """
        result = ResultRepository.get_by_id(result_id)
        return result.to_dict() if result else None
    
    @staticmethod
    def create_result(device_id, model_id, result_value, confidence, additional_data=None):
        """
        Create a new classification result
        
        Args:
            device_id: UUID of the device that generated the result
            model_id: UUID of the model used for classification
            result_value: The classification result (e.g., 'positive', 'negative')
            confidence: The confidence score (0.0 to 1.0)
            additional_data: Additional result data (optional)
            
        Returns:
            Created result as dictionary or error message
        """
        try:
            # Prepare metadata
            metadata = additional_data if additional_data else {}
            
            # Create result
            result = ResultRepository.create(
                device_id=device_id,
                model_id=model_id,
                result_value=result_value,
                confidence=confidence,
                metadata=metadata
            )
            
            if not result:
                return {
                    'success': False,
                    'error': 'Device or model not found'
                }
            
            # Update device last active timestamp
            DeviceRepository.update_heartbeat(device_id)
            
            return {
                'success': True,
                'result_id': str(result.result_id),
                'message': 'Result uploaded successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Error creating result: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }