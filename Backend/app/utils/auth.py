from functools import wraps
from flask import request, jsonify, current_app

def require_api_key(f):
    """
    Decorator for requiring API key authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            current_app.logger.warning("API request missing API key")
            return jsonify({'error': 'Authentication required', 'message': 'API key is missing'}), 401
        
        if api_key != current_app.config['API_KEY']:
            current_app.logger.warning(f"Invalid API key attempted: {api_key[:5]}...")
            return jsonify({'error': 'Authentication failed', 'message': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated