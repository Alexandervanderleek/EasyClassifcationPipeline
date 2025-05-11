import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app import db

class Model(db.Model):
    """Model representing a machine learning model"""
    __tablename__ = 'models'
    
    model_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    project_name = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    s3_bucket = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(1024), nullable=False)
    
    original_filename = db.Column(db.String(255), nullable=False)
    
    model_metadata = db.Column(JSONB, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    devices = db.relationship('Device', back_populates='model', lazy='dynamic')
    results = db.relationship('Result', back_populates='model', lazy='dynamic')
    
    def __repr__(self):
        return f"<Model {self.model_id} - {self.project_name}>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'model_id': str(self.model_id),
            'project_name': self.project_name,
            'upload_date': self.upload_date.isoformat(),
            's3_bucket': self.s3_bucket,
            's3_key': self.s3_key,
            'original_filename': self.original_filename,
            'metadata': self.model_metadata,
            'is_active': self.is_active,
            'active_devices': self.devices.filter_by(is_active=True).count()
        }