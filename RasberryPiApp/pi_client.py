import os
import time
import json
import uuid
import requests
import logging
import argparse
import threading
import numpy as np
from PIL import Image
import tflite_runtime.interpreter as tflite
import cv2
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("classifier.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("PiClassifier")

class PiClassifier:
    def __init__(self, api_url, api_key, device_name=None, capture_interval=60, confidence_threshold=0.7):
        self.api_url = api_url
        self.headers = {
            'X-API-Key': api_key
        }
        
        self.device_name = device_name or f"Pi-{hex(uuid.getnode())[2:]}"
        self.device_id = self._load_or_register_device()
        self.capture_interval = capture_interval  # seconds between captures
        self.confidence_threshold = confidence_threshold
       
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(self.base_dir, "models")
        self.images_dir = os.path.join(self.base_dir, "images")
        
        # Create directories
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # State
        self.current_model_id = None
        self.current_model_path = None
        self.current_metadata = None
        self.interpreter = None
        self.is_running = False
        self.camera = None
        
        # Load current model if available
        self._load_current_model()
        
    def _load_or_register_device(self):
        """
        Load device ID from file or register with the server
        """
        device_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device.json")
        
        if os.path.exists(device_file):
            try:
                with open(device_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded device ID: {data['device_id']}")
                    return data['device_id']
            except Exception as e:
                logger.error(f"Error loading device ID: {str(e)}")
                
        # Register new device
        try:
            response = requests.post(
                f"{self.api_url}/api/devices/register",
                json={"device_name": self.device_name},
                headers=self.headers
            )
            
            if response.status_code == 200:
                device_id = response.json()['device_id']
                
                # Save device ID
                with open(device_file, 'w') as f:
                    json.dump({
                        "device_id": device_id,
                        "device_name": self.device_name,
                        "registration_date": datetime.now().isoformat()
                    }, f, indent=4)
                    
                logger.info(f"Registered new device with ID: {device_id}")
                return device_id
            else:
                logger.error(f"Error registering device: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error registering device: {str(e)}")
            return None
            
    def _load_current_model(self):
        """
        Check if there's a model already downloaded and load it
        """
        model_file = os.path.join(self.base_dir, "current_model.json")
        
        if os.path.exists(model_file):
            try:
                with open(model_file, 'r') as f:
                    data = json.load(f)
                    self.current_model_id = data['model_id']
                    self.current_model_path = data['model_path']
                    self.current_metadata = data['metadata']
                    
                    # Check if model file exists
                    if os.path.exists(self.current_model_path):
                        self._load_interpreter()
                        logger.info(f"Loaded existing model: {self.current_model_id}")
                    else:
                        logger.warning("Model file not found, will download on next heartbeat")
                        
            except Exception as e:
                logger.error(f"Error loading current model: {str(e)}")
                
    def _load_interpreter(self):
        """
        Load the TFLite interpreter with the current model
        """
        if not self.current_model_path or not os.path.exists(self.current_model_path):
            logger.error("No model available to load")
            return False
            
        try:
            self.interpreter = tflite.Interpreter(model_path=self.current_model_path)
            self.interpreter.allocate_tensors()
            logger.info("TFLite interpreter loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading interpreter: {str(e)}")
            return False
            
    def heartbeat(self):
        """
        Send heartbeat to server and check for model updates
        """
        if not self.device_id:
            logger.error("No device ID available for heartbeat")
            return
            
        try:
            response = requests.post(
                f"{self.api_url}/api/devices/{self.device_id}/heartbeat",
                json={"status": "running" if self.is_running else "idle"},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we need to download a new model
                if data['should_download'] and data['model_id'] != self.current_model_id:
                    logger.info(f"New model available: {data['model_id']}")
                    self._download_model(data['model_id'], data['metadata'])
                    
            else:
                logger.error(f"Error sending heartbeat: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {str(e)}")
            
    def _download_model(self, model_id, metadata):
        """
        Download a model from the server
        """
        try:
            # Create model directory
            model_dir = os.path.join(self.models_dir, model_id)
            os.makedirs(model_dir, exist_ok=True)
            
            # Download the model file
            response = requests.get(f"{self.api_url}/api/models/{model_id}/download", stream=True,
                headers=self.headers)
            
            if response.status_code == 200:
                model_path = os.path.join(model_dir, metadata['model_filename'])
                
                with open(model_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                # Save metadata
                metadata_path = os.path.join(model_dir, "metadata.json")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=4)
                    
                # Update current model info
                self.current_model_id = model_id
                self.current_model_path = model_path
                self.current_metadata = metadata
                
                # Save current model info
                with open(os.path.join(self.base_dir, "current_model.json"), 'w') as f:
                    json.dump({
                        "model_id": model_id,
                        "model_path": model_path,
                        "metadata": metadata
                    }, f, indent=4)
                    
                # Load interpreter
                success = self._load_interpreter()
                
                if success:
                    logger.info(f"Model {model_id} downloaded and loaded successfully")
                    return True
                else:
                    logger.error(f"Failed to load interpreter for model {model_id}")
                    return False
            else:
                logger.error(f"Error downloading model: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading model: {str(e)}")
            return False
            
    def capture_and_classify(self):
        """
        Capture an image from the camera and classify it
        """
        if not self.interpreter:
            logger.error("No model loaded for classification")
            return None
            
        try:
            # Capture image from camera
            ret, frame = self.camera.read()
            
            if not ret:
                logger.error("Failed to capture image from camera")
                return None
                
            # Save the image
            timestamp = int(time.time())
            img_path = os.path.join(self.images_dir, f"img_{timestamp}.jpg")
            cv2.imwrite(img_path, frame)
            
            # Preprocess the image
            img = Image.open(img_path).resize((224, 224))
            img_array = np.array(img, dtype=np.float32)
            img_array = img_array / 255.0  # Normalize
            img_array = np.expand_dims(img_array, axis=0)
            
            # Get interpreter details
            input_details = self.interpreter.get_input_details()
            output_details = self.interpreter.get_output_details()
            
            # Set input tensor
            self.interpreter.set_tensor(input_details[0]['index'], img_array)
            
            # Run inference
            self.interpreter.invoke()
            
            # Get output tensor
            prediction = self.interpreter.get_tensor(output_details[0]['index'])
            
            # Get class names from metadata
            if self.current_metadata and 'classes' in self.current_metadata:
                classes = self.current_metadata['classes']
            else:
                classes = ["negative", "positive"]
                
            # Interpret result
            if prediction[0][0] > 0.5:
                result = classes[1]  # Usually "positive"
                confidence = float(prediction[0][0])
            else:
                result = classes[0]  # Usually "negative"
                confidence = 1 - float(prediction[0][0])
                
            logger.info(f"Classification result: {result} (Confidence: {confidence:.2f})")
            
            # Upload result to server if confidence meets threshold
            if confidence >= self.confidence_threshold:
                self._upload_result(result, confidence, img_path)
                
            return {
                "result": result,
                "confidence": confidence,
                "image_path": img_path,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error in capture and classify: {str(e)}")
            return None
            
    def _upload_result(self, result, confidence, img_path):
        """
        Upload classification result to the server
        """
        if not self.device_id or not self.current_model_id:
            logger.error("Missing device ID or model ID for result upload")
            return False
            
        try:
            data = {
                "device_id": self.device_id,
                "model_id": self.current_model_id,
                "result": result,
                "confidence": float(confidence)
            }
            
            response = requests.post(f"{self.api_url}/api/results", json=data,
                headers=self.headers)
            
            if response.status_code == 200:
                logger.info("Result uploaded successfully")
                return True
            else:
                logger.error(f"Error uploading result: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading result: {str(e)}")
            return False
            
    def start(self):
        """
        Start the classification loop
        """
        if self.is_running:
            logger.warning("Classification loop already running")
            return
            
        # Initialize camera
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.error("Could not open camera")
                return
        except Exception as e:
            logger.error(f"Error initializing camera: {str(e)}")
            return
            
        # Start classification loop in a separate thread
        self.is_running = True
        threading.Thread(target=self._classification_loop, daemon=True).start()
        logger.info("Classification loop started")
        
    def stop(self):
        """
        Stop the classification loop
        """
        self.is_running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        logger.info("Classification loop stopped")
        
    def _classification_loop(self):
        """
        Main classification loop
        """
        while self.is_running:
            # Send heartbeat
            self.heartbeat()
            
            # Check if we have a model
            if self.interpreter:
                # Capture and classify
                self.capture_and_classify()
                
            # Wait for the next interval
            time.sleep(self.capture_interval)
            
def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='Raspberry Pi Image Classifier')
    parser.add_argument('--api', type=str, default='http://localhost:5000', help='API server URL')
    parser.add_argument('--apikey', type=str, help='Api key for your backend server')
    parser.add_argument('--name', type=str, help='Device name (default: Pi-<mac>)')
    parser.add_argument('--interval', type=int, default=60, help='Capture interval in seconds')
    parser.add_argument('--threshold', type=float, default=0.5, help='Confidence threshold for reporting')

    args = parser.parse_args()
    
    # Create and start the classifier
    classifier = PiClassifier(
        api_url=args.api,
        api_key=args.apikey,
        device_name=args.name,
        capture_interval=args.interval,
        confidence_threshold=args.threshold
    )
    
    try:
        classifier.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        classifier.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        classifier.stop()
        
if __name__ == "__main__":
    main()