import json
from flask import current_app
from app.repositories import ModelRepository

class ModelService:
    """Service for model business logic"""
    
    @staticmethod
    def get_all_models():
        """
        Get all active models
        
        Returns:
            List of models in dictionary format
        """
        models = ModelRepository.get_all()
        return [model.to_dict() for model in models]
    
    @staticmethod
    def get_model(model_id):
        """
        Get a model by ID
        
        Args:
            model_id: The UUID of the model
            
        Returns:
            Model as dictionary or None if not found
        """
        model = ModelRepository.get_by_id(model_id)
        return model.to_dict() if model else None
    
    @staticmethod
    def create_model(model_file, metadata_file):
        """
        Create a new model from uploaded files
        
        Args:
            model_file: The model file object
            metadata_file: The metadata file object
            
        Returns:
            Created model as dictionary or error message
        """
        try:
            metadata = json.loads(metadata_file.read().decode('utf-8'))
            
            model = ModelRepository.create(model_file, metadata)
            
            return {
                'success': True,
                'model_id': str(model.model_id),
                'message': 'Model uploaded successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Error creating model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_model(model_id, hard_delete=False):
        """
        Delete a model
        
        Args:
            model_id: The UUID of the model to delete
            hard_delete: Whether to permanently delete the model and its file
            
        Returns:
            Success message or error
        """
        try:
            if hard_delete:
                success = ModelRepository.hard_delete(model_id)
            else:
                success = ModelRepository.delete(model_id)
            
            if not success:
                return {
                    'success': False,
                    'error': 'Model not found or could not be deleted'
                }
            
            return {
                'success': True,
                'message': 'Model deleted successfully'
            }
        except Exception as e:
            current_app.logger.error(f"Error deleting model: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_download_url(model_id):
        """
        Get a pre-signed URL for downloading a model
        
        Args:
            model_id: The UUID of the model
            
        Returns:
            URL or error message
        """
        url = ModelRepository.get_download_url(model_id)
        
        if not url:
            return {
                'success': False,
                'error': 'Model not found or URL generation failed'
            }
        
        return {
            'success': True,
            'download_url': url,
            'expires_in': 3600 
        }