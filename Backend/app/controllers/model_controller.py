from flask import Blueprint, request, jsonify
from app.services import ModelService
from app.utils.auth import require_api_key

model_bp = Blueprint('models', __name__)

@model_bp.route('', methods=['GET'])
def list_models():
    """
    List all available models
    """
    models = ModelService.get_all_models()
    return jsonify({'models': models})

@model_bp.route('/<uuid:model_id>', methods=['GET'])
def get_model(model_id):
    """
    Get information about a specific model
    """
    model = ModelService.get_model(str(model_id))
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    return jsonify(model)

@model_bp.route('/create', methods=['POST'])
@require_api_key
def upload_model():
    """
    Upload a new model and its metadata
    """
    if 'model' not in request.files or 'metadata' not in request.files:
        return jsonify({'error': 'Missing model or metadata'}), 400
    
    model_file = request.files['model']
    metadata_file = request.files['metadata']
    
    if model_file.filename == '' or metadata_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    result = ModelService.create_model(model_file, metadata_file)
    
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 500
    
    return jsonify(result)

@model_bp.route('/<uuid:model_id>/download', methods=['GET'])
def download_model(model_id):
    """
    Get a download URL for a specific model file
    """
    result = ModelService.get_download_url(str(model_id))
    
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 404
    
    return jsonify(result)

@model_bp.route('/<uuid:model_id>', methods=['DELETE'])
@require_api_key
def delete_model(model_id):
    """
    Delete a model (soft delete by default)
    """
    hard_delete = request.args.get('hard', 'false').lower() == 'true'
    
    result = ModelService.delete_model(str(model_id), hard_delete)
    
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 404
    
    return jsonify(result)