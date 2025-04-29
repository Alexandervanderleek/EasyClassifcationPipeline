import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app import db

class Device(db.Model):
    """Model representing a Raspberry Pi device"""
    __tablename__ = 'devices'
    
    # Primary key
    device_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Device information
    device_name = db.Column(db.String(255), nullable=False)
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign key to Model
    current_model_id = db.Column(UUID(as_uuid=True), db.ForeignKey('models.model_id'), nullable=True)
    
    # Status
    status = db.Column(db.String(50), nullable=False, default='idle')
    
    # Soft delete flag
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    model = db.relationship('Model', back_populates='devices')
    results = db.relationship('Result', back_populates='device', lazy='dynamic')
    
    def __repr__(self):
        return f"<Device {self.device_id} - {self.device_name}>"
    
    def to_dict(self):
        """Convert device to dictionary"""
        return {
            'device_id': str(self.device_id),
            'device_name': self.device_name,
            'registration_date': self.registration_date.isoformat(),
            'last_active': self.last_active.isoformat(),
            'current_model_id': str(self.current_model_id) if self.current_model_id else None,
            'status': self.status,
            'is_active': self.is_active
        }