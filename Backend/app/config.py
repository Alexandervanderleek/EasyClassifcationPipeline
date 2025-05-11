import os
from datetime import timedelta

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change-in-production')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/classifier_api')
    
    API_KEY = os.getenv('API_KEY', 'dev-api-key-please-change-in-production')
    
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'eu-west-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'classifier-models')
    
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 16 MB max upload size
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/classifier_api_test'
    

class ProductionConfig(Config):
    """Production configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'production-key-please-change')
    API_KEY = os.getenv('API_KEY', 'production-api-key-please-change')
    
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'classifier-models-prod')