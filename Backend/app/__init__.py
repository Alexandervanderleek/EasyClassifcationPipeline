import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """
    Create and configure the Flask application
    
    Args:
        config_name: Configuration to use (development, testing, production)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_class = f"{config_name.capitalize()}Config"
    
    from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
    
    if config_name.lower() == 'development':
        app.config.from_object('app.config.DevelopmentConfig')
    elif config_name.lower() == 'testing':
        app.config.from_object('app.config.TestingConfig')
    elif config_name.lower() == 'production':
        app.config.from_object('app.config.ProductionConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    from app.controllers.device_controller import device_bp
    from app.controllers.model_controller import model_bp
    from app.controllers.result_controller import result_bp
    
    app.register_blueprint(device_bp, url_prefix='/api/devices')
    app.register_blueprint(model_bp, url_prefix='/api/models')
    app.register_blueprint(result_bp, url_prefix='/api/results')
    
    register_error_handlers(app)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint for testing API connectivity"""
        from flask import jsonify
        return jsonify({
            'status': 'ok',
            'message': 'API server is running',
            'environment': app.config.get('ENV', 'unknown')
        })
    
    return app

def register_error_handlers(app):
    """Register error handlers for the application"""
    from flask import jsonify
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': str(error)}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Server error', 'message': str(error)}), 500