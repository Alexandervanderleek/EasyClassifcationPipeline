#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model Service - Handles model training, conversion, and management
"""

import os
import json
import time
import datetime
from pathlib import Path
import threading
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from PySide6.QtCore import QObject, Signal, Slot

class ModelService(QObject):
    """Service for training, converting, and managing models"""
    
    # Define signals for training and conversion
    training_started = Signal()
    training_progress = Signal(int, dict)  # epoch, logs
    training_finished = Signal(bool, str)  # success, message
    
    conversion_started = Signal()
    conversion_progress = Signal(int)  # progress percentage
    conversion_finished = Signal(bool, str)  # success, message
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_model = None
        self.current_metadata = None
        self.training_thread = None
        self.conversion_thread = None
    
    def create_project_structure(self, project_name):
        """Create directory structure for a new project"""
        project_dir = os.path.join(self.config.base_dir, project_name)
        
        # Create necessary subdirectories
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "dataset"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "dataset", "positive"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "dataset", "negative"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "models"), exist_ok=True)
        
        return project_dir
    
    def get_image_counts(self, project_path):
        """Get the number of positive and negative images in the project"""
        pos_dir = os.path.join(project_path, "dataset", "positive")
        neg_dir = os.path.join(project_path, "dataset", "negative")
        
        pos_count = len([f for f in os.listdir(pos_dir) 
                      if os.path.isfile(os.path.join(pos_dir, f))])
        neg_count = len([f for f in os.listdir(neg_dir) 
                      if os.path.isfile(os.path.join(neg_dir, f))])
        
        return pos_count, neg_count
    
    def list_projects(self):
        """List all available projects"""
        try:
            projects = []
            for item in os.listdir(self.config.base_dir):
                project_path = os.path.join(self.config.base_dir, item)
                if os.path.isdir(project_path):
                    # Check if it has the expected structure
                    if os.path.exists(os.path.join(project_path, "dataset")):
                        pos_count, neg_count = self.get_image_counts(project_path)
                        
                        # Check for trained model
                        model_path = os.path.join(project_path, "models", "model.h5")
                        tflite_path = os.path.join(project_path, "models", "model.tflite")
                        has_model = os.path.exists(model_path)
                        has_tflite = os.path.exists(tflite_path)
                        
                        projects.append({
                            'name': item,
                            'path': project_path,
                            'positive_count': pos_count,
                            'negative_count': neg_count,
                            'has_model': has_model,
                            'has_tflite': has_tflite
                        })
            
            return projects
        except Exception as e:
            print(f"Error listing projects: {str(e)}")
            return []
    
    def train_model(self, project_path, epochs=10, batch_size=32, learning_rate=0.0001):
        """Train a model for the given project"""
        if self.training_thread and self.training_thread.is_alive():
            return False, "Training already in progress"
        
        # Check if we have enough images
        pos_count, neg_count = self.get_image_counts(project_path)
        if pos_count < 10 or neg_count < 10:
            return False, "Need at least 10 images of each class"
        
        # Start training in a separate thread
        self.training_thread = threading.Thread(
            target=self._train_model_thread,
            args=(project_path, epochs, batch_size, learning_rate),
            daemon=True
        )
        self.training_thread.start()
        
        # Emit signal
        self.training_started.emit()
        
        return True, "Training started"
    
    def _train_model_thread(self, project_path, epochs, batch_size, learning_rate):
        """Training thread to run in background"""
        try:
            # Prepare data directory
            dataset_dir = os.path.join(project_path, "dataset")
            
            # Create data generator with augmentation
            train_datagen = ImageDataGenerator(
                rescale=1./255,
                rotation_range=20,
                width_shift_range=0.2,
                height_shift_range=0.2,
                shear_range=0.2,
                zoom_range=0.2,
                horizontal_flip=True,
                validation_split=0.2
            )
            
            # Create data generators
            train_generator = train_datagen.flow_from_directory(
                dataset_dir,
                target_size=(224, 224),
                batch_size=batch_size,
                class_mode='binary',
                subset='training'
            )
            
            validation_generator = train_datagen.flow_from_directory(
                dataset_dir,
                target_size=(224, 224),
                batch_size=batch_size,
                class_mode='binary',
                subset='validation'
            )
            
            # Create the model
            base_model = MobileNetV2(
                input_shape=(224, 224, 3),
                include_top=False,
                weights='imagenet'
            )
            
            # Freeze the base model layers
            base_model.trainable = False
            
            # Add custom classification head
            x = base_model.output
            x = GlobalAveragePooling2D()(x)
            x = Dense(128, activation='relu')(x)
            predictions = Dense(1, activation='sigmoid')(x)  # Binary classification
            
            # Create the final model
            model = Model(inputs=base_model.input, outputs=predictions)
            
            # Compile model
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            # Create a callback for updating the UI
            class UICallback(tf.keras.callbacks.Callback):
                def __init__(self, service):
                    super().__init__()
                    self.service = service
                
                def on_epoch_end(self, epoch, logs=None):
                    if not logs:
                        logs = {}
                        
                    from PySide6.QtCore import QCoreApplication
                    QCoreApplication.processEvents()
                    self.service.training_progress.emit(epoch + 1, logs)
            
            # Train the model
            history = model.fit(
                train_generator,
                steps_per_epoch=train_generator.samples // batch_size,
                validation_data=validation_generator,
                validation_steps=validation_generator.samples // batch_size,
                epochs=epochs,
                callbacks=[UICallback(self)]
            )
            
            # Save the model
            model_path = os.path.join(project_path, "models", "model.h5")
            model.save(model_path)
            
            # Store the current model
            self.current_model = model
            
            # Create model metadata
            metadata = {
                "project_name": os.path.basename(project_path),
                "date_created": datetime.datetime.now().isoformat(),
                "classes": list(train_generator.class_indices.keys()),
                "class_indices": train_generator.class_indices,
                "training_params": {
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate
                },
                "training_results": {
                    "final_accuracy": float(history.history['accuracy'][-1]),
                    "final_val_accuracy": float(history.history['val_accuracy'][-1])
                }
            }
            
            # Save metadata
            metadata_path = os.path.join(project_path, "models", "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            self.current_metadata = metadata
            
            # Signal successful completion
            self.training_finished.emit(True, "Model trained successfully")
            
        except Exception as e:
            # Signal error
            self.training_finished.emit(False, str(e))
    
    def convert_to_tflite(self, project_path):
        """Convert the trained model to TFLite format"""
        if self.conversion_thread and self.conversion_thread.is_alive():
            return False, "Conversion already in progress"
        
        # Start conversion in a separate thread
        self.conversion_thread = threading.Thread(
            target=self._convert_to_tflite_thread,
            args=(project_path,),
            daemon=True
        )
        self.conversion_thread.start()
        
        # Emit signal
        self.conversion_started.emit()
        
        return True, "Conversion started"
    
    def _convert_to_tflite_thread(self, project_path):
        """Conversion thread to run in background"""
        try:
            # Check if we have a model in memory
            if self.current_model is None:
                # Try to load the model from file
                model_path = os.path.join(project_path, "models", "model.h5")
                if not os.path.exists(model_path):
                    raise FileNotFoundError("Model file not found")
                
                self.current_model = load_model(model_path)
            
            # Signal progress
            self.conversion_progress.emit(10)
            
            # Create a converter
            converter = tf.lite.TFLiteConverter.from_keras_model(self.current_model)
            
            # Signal progress
            self.conversion_progress.emit(30)
            
            # Convert the model
            tflite_model = converter.convert()
            
            # Signal progress
            self.conversion_progress.emit(60)
            
            # Save the TFLite model
            tflite_path = os.path.join(project_path, "models", "model.tflite")
            with open(tflite_path, 'wb') as f:
                f.write(tflite_model)
            
            # Signal progress
            self.conversion_progress.emit(80)
            
            # Apply quantization for smaller size
            converter = tf.lite.TFLiteConverter.from_keras_model(self.current_model)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            tflite_quantized_model = converter.convert()
            
            # Save the quantized model
            tflite_q_path = os.path.join(project_path, "models", "model_quantized.tflite")
            with open(tflite_q_path, 'wb') as f:
                f.write(tflite_quantized_model)
            
            # Signal progress
            self.conversion_progress.emit(100)
            
            # Signal successful completion
            self.conversion_finished.emit(True, "Model converted successfully")
            
        except Exception as e:
            # Signal error
            self.conversion_finished.emit(False, str(e))
    
    def load_model_metadata(self, project_path):
        """Load model metadata from a project"""
        metadata_path = os.path.join(project_path, "models", "metadata.json")
        
        if not os.path.exists(metadata_path):
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.current_metadata = metadata
            return metadata
        except Exception as e:
            print(f"Error loading model metadata: {str(e)}")
            return None
    
    def test_model(self, project_path, image_path):
        """Test a model with an image and return the classification result"""
        try:
            # Check if we have a model in memory
            if self.current_model is None:
                # Try to load the model from file
                model_path = os.path.join(project_path, "models", "model.h5")
                if not os.path.exists(model_path):
                    return False, "Model not found", None
                
                self.current_model = load_model(model_path)
            
            # Load and preprocess the image
            img = tf.keras.preprocessing.image.load_img(image_path, target_size=(224, 224))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = tf.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0  # Normalize
            
            # Make prediction
            prediction = self.current_model.predict(img_array)
            
            # Load metadata to get class names if we don't have it
            if not self.current_metadata:
                self.load_model_metadata(project_path)
            
            # Get class names from metadata
            if self.current_metadata and 'classes' in self.current_metadata:
                classes = self.current_metadata['classes']
            else:
                classes = ['negative', 'positive']
            
            # Interpret result
            if prediction[0][0] > 0.5:
                result = classes[1]  # Positive class
                confidence = float(prediction[0][0])
            else:
                result = classes[0]  # Negative class
                confidence = 1 - float(prediction[0][0])
                
            return True, "Prediction successful", {
                'result': result,
                'confidence': confidence,
                'raw_prediction': float(prediction[0][0])
            }
            
        except Exception as e:
            return False, str(e), None