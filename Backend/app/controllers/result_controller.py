from flask import Blueprint, request, jsonify
from app.services import ResultService

# Create blueprint
result_bp = Blueprint('results', __name__)

@result_bp.route('', methods=['GET'])
def list_results():
    """
    List classification results, with optional filtering
    """
    device_id = request.args.get('device_id')
    model_id = request.args.get('model_id')
    limit = int(request.args.get('limit', 50))
    
    results = ResultService.get_all_results(device_id, model_id, limit)
    return jsonify({'results': results})

@result_bp.route('/<uuid:result_id>', methods=['GET'])
def get_result(result_id):
    """
    Get a specific classification result
    """
    result = ResultService.get_result(str(result_id))
    
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    return jsonify(result)

@result_bp.route('', methods=['POST'])
def upload_result():
    """
    Upload a classification result from a device
    """
    data = request.json
    if not data or 'device_id' not in data or 'model_id' not in data or 'result' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    device_id = data['device_id']
    model_id = data['model_id']
    result_value = data['result']
    confidence = data.get('confidence', 0.0)
    additional_data = {k: v for k, v in data.items() 
                      if k not in ['device_id', 'model_id', 'result', 'confidence']}
    
    result = ResultService.create_result(
        device_id, model_id, result_value, confidence, additional_data
    )
    
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 404 if 'not found' in result.get('error', '') else 400
    
    return jsonify(result)