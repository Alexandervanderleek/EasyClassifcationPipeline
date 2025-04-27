import os
import json
import uuid
import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Database (in-memory for simplicity, use a real DB in production)
models_db = {}
devices_db = {}
results_db = {}

@app.route('/api/models', methods=['POST'])
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
        
    try:
        # Generate a unique ID for the model
        model_id = str(uuid.uuid4())
        
        # Create a directory for this model
        model_dir = os.path.join(app.config['UPLOAD_FOLDER'], model_id)
        os.makedirs(model_dir, exist_ok=True)
        
        # Save model file
        model_path = os.path.join(model_dir, secure_filename(model_file.filename))
        model_file.save(model_path)
        
        # Parse and save metadata
        metadata = json.loads(metadata_file.read().decode('utf-8'))
        metadata['model_id'] = model_id
        metadata['upload_date'] = datetime.datetime.now().isoformat()
        metadata['model_filename'] = secure_filename(model_file.filename)
        
        metadata_path = os.path.join(model_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
            
        # Store in our database
        models_db[model_id] = {
            'metadata': metadata,
            'model_path': model_path,
            'metadata_path': metadata_path,
            'active_devices': []
        }
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'message': 'Model uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/models', methods=['GET'])
def list_models():
    """
    List all available models
    """
    models_list = []
    for model_id, model_data in models_db.items():
        models_list.append({
            'model_id': model_id,
            'project_name': model_data['metadata'].get('project_name', 'Unknown'),
            'upload_date': model_data['metadata'].get('upload_date', 'Unknown'),
            'active_devices': len(model_data['active_devices'])
        })
    
    return jsonify({'models': models_list})
    
@app.route('/api/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """
    Get information about a specific model
    """
    if model_id not in models_db:
        return jsonify({'error': 'Model not found'}), 404
        
    return jsonify({
        'model_id': model_id,
        'metadata': models_db[model_id]['metadata']
    })
    
@app.route('/api/models/<model_id>/download', methods=['GET'])
def download_model(model_id):
    """
    Download a specific model file
    """
    if model_id not in models_db:
        return jsonify({'error': 'Model not found'}), 404
        
    return send_file(
        models_db[model_id]['model_path'],
        as_attachment=True,
        download_name=models_db[model_id]['metadata']['model_filename']
    )
    
@app.route('/api/devices/register', methods=['POST'])
def register_device():
    """
    Register a new Raspberry Pi device
    """
    data = request.json
    if not data or 'device_name' not in data:
        return jsonify({'error': 'Missing device name'}), 400
        
    device_id = str(uuid.uuid4())
    
    devices_db[device_id] = {
        'device_id': device_id,
        'device_name': data['device_name'],
        'registration_date': datetime.datetime.now().isoformat(),
        'last_active': datetime.datetime.now().isoformat(),
        'current_model_id': None,
        'status': 'idle'
    }
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'message': 'Device registered successfully'
    })
    
@app.route('/api/devices', methods=['GET'])
def list_devices():
    """
    List all registered devices
    """
    devices_list = list(devices_db.values())
    return jsonify({'devices': devices_list})
    
@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """
    Get information about a specific device
    """
    if device_id not in devices_db:
        return jsonify({'error': 'Device not found'}), 404
        
    return jsonify(devices_db[device_id])
    
@app.route('/api/devices/<device_id>/set_model', methods=['POST'])
def set_device_model(device_id):
    """
    Set the model that a device should use
    """
    if device_id not in devices_db:
        return jsonify({'error': 'Device not found'}), 404
        
    data = request.json
    if not data or 'model_id' not in data:
        return jsonify({'error': 'Missing model ID'}), 400
        
    model_id = data['model_id']
    if model_id not in models_db:
        return jsonify({'error': 'Model not found'}), 404
        
    # Update the device's current model
    old_model_id = devices_db[device_id]['current_model_id']
    devices_db[device_id]['current_model_id'] = model_id
    devices_db[device_id]['last_active'] = datetime.datetime.now().isoformat()
    
    # Remove device from old model's active devices
    if old_model_id and old_model_id in models_db:
        if device_id in models_db[old_model_id]['active_devices']:
            models_db[old_model_id]['active_devices'].remove(device_id)
    
    # Add device to new model's active devices
    if device_id not in models_db[model_id]['active_devices']:
        models_db[model_id]['active_devices'].append(device_id)
    
    return jsonify({
        'success': True,
        'message': 'Model set successfully'
    })
    
@app.route('/api/devices/<device_id>/heartbeat', methods=['POST'])
def device_heartbeat(device_id):
    """
    Update device status and get assigned model
    """
    if device_id not in devices_db:
        return jsonify({'error': 'Device not found'}), 404
        
    data = request.json or {}
    
    # Update device status
    devices_db[device_id]['last_active'] = datetime.datetime.now().isoformat()
    if 'status' in data:
        devices_db[device_id]['status'] = data['status']
        
    # Return the current assigned model
    model_id = devices_db[device_id]['current_model_id']
    should_download = False
    
    if model_id and model_id in models_db:
        metadata = models_db[model_id]['metadata']
        should_download = True
    else:
        metadata = None
        
    return jsonify({
        'model_id': model_id,
        'should_download': should_download,
        'metadata': metadata
    })
    
@app.route('/api/results', methods=['POST'])
def upload_result():
    """
    Upload a classification result from a device
    """
    data = request.json
    if not data or 'device_id' not in data or 'model_id' not in data or 'result' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    device_id = data['device_id']
    model_id = data['model_id']
    
    if device_id not in devices_db:
        return jsonify({'error': 'Device not found'}), 404
        
    if model_id not in models_db:
        return jsonify({'error': 'Model not found'}), 404
        
    # Store the result
    result_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    result_data = {
        'result_id': result_id,
        'device_id': device_id,
        'model_id': model_id,
        'device_name': devices_db[device_id]['device_name'],
        'project_name': models_db[model_id]['metadata'].get('project_name', 'Unknown'),
        'timestamp': timestamp,
        'result': data['result'],
        'confidence': data.get('confidence', 0.0),
        'image_url': None  # We're not storing images in this version
    }
    
    # Save to database
    results_db[result_id] = result_data
    
    # Update device status
    devices_db[device_id]['last_active'] = timestamp
    
    # Save result to file
    results_dir = os.path.join(app.config['RESULTS_FOLDER'], device_id)
    os.makedirs(results_dir, exist_ok=True)
    
    result_file = os.path.join(results_dir, f"{result_id}.json")
    with open(result_file, 'w') as f:
        json.dump(result_data, f, indent=4)
        
    return jsonify({
        'success': True,
        'result_id': result_id,
        'message': 'Result uploaded successfully'
    })
    
@app.route('/api/results', methods=['GET'])
def list_results():
    """
    List classification results, with optional filtering
    """
    device_id = request.args.get('device_id')
    model_id = request.args.get('model_id')
    limit = int(request.args.get('limit', 50))
    
    results = list(results_db.values())
    
    # Apply filters
    if device_id:
        results = [r for r in results if r['device_id'] == device_id]
    if model_id:
        results = [r for r in results if r['model_id'] == model_id]
        
    # Sort by timestamp (newest first)
    results.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Apply limit
    results = results[:limit]
    
    return jsonify({'results': results})
    
@app.route('/api/results/<result_id>', methods=['GET'])
def get_result(result_id):
    """
    Get a specific classification result
    """
    if result_id not in results_db:
        return jsonify({'error': 'Result not found'}), 404
        
    return jsonify(results_db[result_id])
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)