import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app import db

class Result(db.Model):
    """Model representing a classification result"""
    __tablename__ = 'results'
    
    result_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    device_id = db.Column(UUID(as_uuid=True), db.ForeignKey('devices.device_id'), nullable=False)
    model_id = db.Column(UUID(as_uuid=True), db.ForeignKey('models.model_id'), nullable=False)
    
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    result = db.Column(db.String(255), nullable=False)
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    
    result_metadata = db.Column(JSONB, nullable=True)
    
    device = db.relationship('Device', back_populates='results')
    model = db.relationship('Model', back_populates='results')
    
    def __repr__(self):
        return f"<Result {self.result_id} - {self.result}>"
    
    def to_dict(self):
        """Convert result to dictionary"""
        return {
            'result_id': str(self.result_id),
            'device_id': str(self.device_id),
            'model_id': str(self.model_id),
            'device_name': self.device.device_name,
            'project_name': self.model.project_name,
            'timestamp': self.timestamp.isoformat(),
            'result': self.result,
            'confidence': self.confidence,
            'metadata': self.result_metadata
        }