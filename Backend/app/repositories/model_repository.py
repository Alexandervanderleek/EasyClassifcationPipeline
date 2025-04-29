import os
import boto3
import botocore
from flask import current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Model, Device

class ModelRepository:
    """Repository for model data access and S3 operations"""
    
    @staticmethod
    def get_s3_client():
        """Get an S3 client configured with application settings"""
        return boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_DEFAULT_REGION']
        )
    
    @staticmethod
    def get_all(include_inactive=False):
        """
        Get all models
        
        Args:
            include_inactive: Whether to include inactive/deleted models
            
        Returns:
            List of Model objects
        """
        query = Model.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_by_id(model_id, include_inactive=False):
        """
        Get a model by ID
        
        Args:
            model_id: The UUID of the model
            include_inactive: Whether to include inactive/deleted models
            
        Returns:
            Model object or None if not found
        """
        query = Model.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.filter_by(model_id=model_id).first()
    
    @staticmethod
    def create(model_file, metadata):
        """
        Create a new model entry and upload the model file to S3
        
        Args:
            model_file: The model file object
            metadata: JSON metadata for the model
            
        Returns:
            Created Model object
        """
        # Secure the filename
        filename = secure_filename(model_file.filename)
        
        # Generate a unique S3 key
        s3_key = f"models/{metadata.get('project_name', 'unknown')}/{filename}"
        
        # Upload file to S3
        s3_client = ModelRepository.get_s3_client()
        s3_bucket = current_app.config['S3_BUCKET_NAME']
        
        try:
            s3_client.upload_fileobj(
                model_file,
                s3_bucket,
                s3_key
            )
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"S3 upload error: {str(e)}")
            raise Exception(f"Failed to upload model to S3: {str(e)}")
        
        # Create model record in database
        model = Model(
            project_name=metadata.get('project_name', 'Unknown'),
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            original_filename=filename,
            model_metadata=metadata
        )
        
        db.session.add(model)
        db.session.commit()
        
        return model
    
    @staticmethod
    def delete(model_id):
        """
        Delete a model (soft delete)
        
        Args:
            model_id: The UUID of the model to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        model = Model.query.get(model_id)
        if not model:
            return False
        
        # Handle device assignments first
        devices = Device.query.filter_by(current_model_id=model_id).all()
        for device in devices:
            device.current_model_id = None
            device.status = 'idle'
        
        # Soft delete the model
        model.is_active = False
        
        db.session.commit()
        return True
    
    @staticmethod
    def hard_delete(model_id):
        """
        Permanently delete a model and its file from S3
        
        Args:
            model_id: The UUID of the model to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        model = Model.query.get(model_id)
        if not model:
            return False
        
        # Handle device assignments first
        devices = Device.query.filter_by(current_model_id=model_id).all()
        for device in devices:
            device.current_model_id = None
            device.status = 'idle'
        
        # Delete the file from S3
        try:
            s3_client = ModelRepository.get_s3_client()
            s3_client.delete_object(
                Bucket=model.s3_bucket,
                Key=model.s3_key
            )
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"S3 deletion error: {str(e)}")
            # Continue with DB deletion even if S3 deletion fails
        
        # Delete the model from the database
        db.session.delete(model)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_download_url(model_id, expiration=3600):
        """
        Generate a pre-signed URL for downloading a model
        
        Args:
            model_id: The UUID of the model
            expiration: URL expiration time in seconds
            
        Returns:
            Pre-signed URL or None if model not found
        """
        model = Model.query.filter_by(model_id=model_id, is_active=True).first()
        if not model:
            return None
        
        s3_client = ModelRepository.get_s3_client()
        
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': model.s3_bucket,
                    'Key': model.s3_key,
                    'ResponseContentDisposition': f'attachment; filename="{model.original_filename}"'
                },
                ExpiresIn=expiration
            )
            return url
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"S3 presigned URL error: {str(e)}")
            return None