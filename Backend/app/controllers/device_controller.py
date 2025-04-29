from flask import Blueprint, request, jsonify
from app.services import DeviceService
from app.utils.auth import require_api_key

# Create blueprint
device_bp = Blueprint('devices', __name__)

@device_bp.route('', methods=['GET'])
def list_devices():
    """
    List all registered devices
    """
    devices = DeviceService.get_all_devices()
    return jsonify({'devices': devices})

@device_bp.route('/<uuid:device_id>', methods=['GET'])
def get_device(device_id):
    """
    Get information about a specific device
    """
    device = DeviceService.get_device(str(device_id))
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify(device)

@device_bp.route('/register', methods=['POST'])
def register_device():
    """
    Register a new Raspberry Pi device
    """
    data = request.json
    if not data or 'device_name' not in data:
        return jsonify({'error': 'Missing device name'}), 400
    
    result = DeviceService.register_device(data['device_name'])
    
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 500
    
    return jsonify(result)

@device_bp.route('/<uuid:device_id>/set_model', methods=['POST'])
@require_api_key
def set_device_model(device_id):
    """
    Set the model that a device should use
    """
    data = request.json
    if not data or 'model_id' not in data:
        return jsonify({'error': 'Missing model ID'}), 400
    
    model_id = data['model_id']
    # Allow null/None to unassign model
    if model_id == 'null' or model_id == 'None' or model_id is None:
        model_id = None
    
    result = DeviceService.set_device_model(str(device_id), model_id)
    
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 404 if 'not found' in result.get('error', '') else 400
    
    return jsonify(result)

@device_bp.route('/<uuid:device_id>/heartbeat', methods=['POST'])
def device_heartbeat(device_id):
    """
    Update device status and get assigned model
    """
    data = request.json or {}
    status = data.get('status')
    
    result = DeviceService.update_heartbeat(str(device_id), status)
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 404
    
    return jsonify(result)

@device_bp.route('/<uuid:device_id>', methods=['DELETE'])
@require_api_key
def delete_device(device_id):
    """
    Delete/deregister a device (soft delete by default)
    """
    # Check for hard delete option
    hard_delete = request.args.get('hard', 'false').lower() == 'true'
    
    result = DeviceService.delete_device(str(device_id), hard_delete)
    
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 404
    
    return jsonify(result)