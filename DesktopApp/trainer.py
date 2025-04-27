import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import threading
import time
import requests
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import shutil
import json

class ModelTrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Classifier Model Trainer")
        self.root.geometry("800x600")
        
        # Variables
        self.project_name = tk.StringVar(value="my_classifier")
        self.epochs = tk.IntVar(value=10)
        self.batch_size = tk.IntVar(value=32)
        self.learning_rate = tk.DoubleVar(value=0.0001)
        self.api_endpoint = tk.StringVar(value="http://localhost:5000")
        self.camera_index = tk.IntVar(value=0)
        
        # Create project directory structure
        self.create_project_structure()
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        self.setup_tab = ttk.Frame(self.tab_control)
        self.collect_tab = ttk.Frame(self.tab_control)
        self.train_tab = ttk.Frame(self.tab_control)
        self.deploy_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.setup_tab, text="Setup")
        self.tab_control.add(self.collect_tab, text="Collect Images")
        self.tab_control.add(self.train_tab, text="Train Model")
        self.tab_control.add(self.deploy_tab, text="Deploy Model")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Setup the tabs
        self.setup_setup_tab()
        self.setup_collect_tab()
        self.setup_train_tab()
        self.setup_deploy_tab()
        
        # Camera variables
        self.cap = None
        self.is_capturing = False
        self.current_class = "positive"  # or "negative"
        
        # Model variables
        self.model = None
        self.training_thread = None
        self.is_training = False
        
    def create_project_structure(self):
        # Create base directory in user's home directory
        base_dir = os.path.join(os.path.expanduser("~"), "classifier_projects")
        os.makedirs(base_dir, exist_ok=True)
        self.base_dir = base_dir
        
    def setup_project_directories(self):
        # Create specific project directory
        project_name = self.project_name.get()
        project_dir = os.path.join(self.base_dir, project_name)
        
        # Create necessary subdirectories
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "dataset"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "dataset", "positive"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "dataset", "negative"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "models"), exist_ok=True)
        
        self.project_dir = project_dir
        messagebox.showinfo("Success", f"Project structure created at {project_dir}")
        
    def setup_setup_tab(self):
        frame = ttk.Frame(self.setup_tab, padding="10")
        frame.pack(fill="both", expand=True)
        
        # Project name
        ttk.Label(frame, text="Project Name:").grid(column=0, row=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.project_name, width=25).grid(column=1, row=0, sticky=tk.W, pady=5)
        
        # Camera selection
        ttk.Label(frame, text="Camera Index:").grid(column=0, row=1, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.camera_index, width=5).grid(column=1, row=1, sticky=tk.W, pady=5)
        
        # API endpoint
        ttk.Label(frame, text="API Endpoint:").grid(column=0, row=2, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.api_endpoint, width=25).grid(column=1, row=2, sticky=tk.W, pady=5)
        
        # Create project button
        ttk.Button(frame, text="Create Project Structure", command=self.setup_project_directories).grid(column=0, row=3, columnspan=2, pady=20)
        
        # Help text
        help_text = """
        Step 1: Enter a project name and click 'Create Project Structure'
        Step 2: Go to the 'Collect Images' tab to capture positive and negative examples
        Step 3: Train your model on the 'Train Model' tab
        Step 4: Deploy your model using the 'Deploy Model' tab
        """
        ttk.Label(frame, text=help_text, wraplength=500).grid(column=0, row=4, columnspan=2, sticky=tk.W)
        
    def setup_collect_tab(self):
        frame = ttk.Frame(self.collect_tab, padding="10")
        frame.pack(fill="both", expand=True)
        
        # Create a notebook for camera and import tabs
        collect_notebook = ttk.Notebook(frame)
        collect_notebook.grid(column=0, row=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        camera_tab = ttk.Frame(collect_notebook)
        import_tab = ttk.Frame(collect_notebook)
        
        collect_notebook.add(camera_tab, text="Camera Capture")
        collect_notebook.add(import_tab, text="Import Images")
        
        # === Camera Tab ===
        # Camera frame
        self.camera_frame = ttk.Frame(camera_tab, borderwidth=2, relief="groove", width=640, height=480)
        self.camera_frame.grid(column=0, row=0, columnspan=2, padx=5, pady=5)
        self.camera_label = ttk.Label(self.camera_frame)
        self.camera_label.pack()
        
        # Control buttons
        controls_frame = ttk.Frame(camera_tab)
        controls_frame.grid(column=0, row=1, columnspan=2, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Start Camera", command=self.start_camera).grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(controls_frame, text="Stop Camera", command=self.stop_camera).grid(column=1, row=0, padx=5, pady=5)
        
        # Capture frame
        capture_frame = ttk.Frame(camera_tab)
        capture_frame.grid(column=0, row=2, columnspan=2, padx=5, pady=5)
        
        ttk.Label(capture_frame, text="Current Class:").grid(column=0, row=0, padx=5, pady=5)
        self.class_label = ttk.Label(capture_frame, text="Positive")
        self.class_label.grid(column=1, row=0, padx=5, pady=5)
        
        ttk.Button(capture_frame, text="Capture Positive", command=lambda: self.capture_image("positive")).grid(column=0, row=1, padx=5, pady=5)
        ttk.Button(capture_frame, text="Capture Negative", command=lambda: self.capture_image("negative")).grid(column=1, row=1, padx=5, pady=5)
        
        # === Import Tab ===
        import_frame = ttk.Frame(import_tab, padding="10")
        import_frame.pack(fill="both", expand=True)
        
        # Positive images import
        pos_frame = ttk.LabelFrame(import_frame, text="Positive Images")
        pos_frame.grid(column=0, row=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(pos_frame, text="Select Folder", command=lambda: self.import_images_from_folder("positive")).grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(pos_frame, text="Select Files", command=lambda: self.import_image_files("positive")).grid(column=1, row=0, padx=5, pady=5)
        
        # Negative images import
        neg_frame = ttk.LabelFrame(import_frame, text="Negative Images")
        neg_frame.grid(column=0, row=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(neg_frame, text="Select Folder", command=lambda: self.import_images_from_folder("negative")).grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(neg_frame, text="Select Files", command=lambda: self.import_image_files("negative")).grid(column=1, row=0, padx=5, pady=5)
        
        # Import progress
        progress_frame = ttk.Frame(import_frame)
        progress_frame.grid(column=0, row=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(progress_frame, text="Import Progress:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.import_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        self.import_progress.grid(column=1, row=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.import_status = ttk.Label(progress_frame, text="")
        self.import_status.grid(column=0, row=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Stats (shared between tabs)
        self.stats_frame = ttk.Frame(frame)
        self.stats_frame.grid(column=0, row=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(self.stats_frame, text="Positive Images:").grid(column=0, row=0, padx=5, pady=2, sticky=tk.W)
        self.positive_count = ttk.Label(self.stats_frame, text="0")
        self.positive_count.grid(column=1, row=0, padx=5, pady=2, sticky=tk.W)
        
        ttk.Label(self.stats_frame, text="Negative Images:").grid(column=0, row=1, padx=5, pady=2, sticky=tk.W)
        self.negative_count = ttk.Label(self.stats_frame, text="0")
        self.negative_count.grid(column=1, row=1, padx=5, pady=2, sticky=tk.W)
        
    def setup_train_tab(self):
        frame = ttk.Frame(self.train_tab, padding="10")
        frame.pack(fill="both", expand=True)
        
        # Training parameters
        params_frame = ttk.LabelFrame(frame, text="Training Parameters")
        params_frame.grid(column=0, row=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(params_frame, text="Epochs:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(params_frame, textvariable=self.epochs, width=5).grid(column=1, row=0, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(params_frame, text="Batch Size:").grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(params_frame, textvariable=self.batch_size, width=5).grid(column=1, row=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(params_frame, text="Learning Rate:").grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(params_frame, textvariable=self.learning_rate, width=10).grid(column=1, row=2, padx=5, pady=5, sticky=tk.W)
        
        # Training control
        train_frame = ttk.Frame(frame)
        train_frame.grid(column=0, row=1, padx=5, pady=20, sticky=(tk.W, tk.E))
        
        self.train_button = ttk.Button(train_frame, text="Train Model", command=self.train_model)
        self.train_button.grid(column=0, row=0, padx=5, pady=5)
        
        self.convert_button = ttk.Button(train_frame, text="Convert to TFLite", command=self.convert_to_tflite, state="disabled")
        self.convert_button.grid(column=1, row=0, padx=5, pady=5)
        
        # Progress
        progress_frame = ttk.Frame(frame)
        progress_frame.grid(column=0, row=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(progress_frame, text="Training Progress:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(column=1, row=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Log
        log_frame = ttk.LabelFrame(frame, text="Training Log")
        log_frame.grid(column=0, row=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=10, width=70)
        self.log_text.grid(column=0, row=0, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(column=1, row=0, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = scrollbar.set
        
    def setup_deploy_tab(self):
        frame = ttk.Frame(self.deploy_tab, padding="10")
        frame.pack(fill="both", expand=True)
        
        # Model info
        info_frame = ttk.LabelFrame(frame, text="Model Information")
        info_frame.grid(column=0, row=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(info_frame, text="Model Status:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.model_status = ttk.Label(info_frame, text="Not trained")
        self.model_status.grid(column=1, row=0, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_frame, text="TFLite Status:").grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.tflite_status = ttk.Label(info_frame, text="Not converted")
        self.tflite_status.grid(column=1, row=1, padx=5, pady=5, sticky=tk.W)
        
        # Deploy
        deploy_frame = ttk.Frame(frame)
        deploy_frame.grid(column=0, row=1, padx=5, pady=20, sticky=(tk.W, tk.E))
        
        self.deploy_button = ttk.Button(deploy_frame, text="Deploy to Cloud", command=self.deploy_model, state="disabled")
        self.deploy_button.grid(column=0, row=0, padx=5, pady=5)
        
        ttk.Label(deploy_frame, text="Deployment Status:").grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.deploy_status = ttk.Label(deploy_frame, text="Not deployed")
        self.deploy_status.grid(column=1, row=1, padx=5, pady=5, sticky=tk.W)
        
        # Test
        test_frame = ttk.LabelFrame(frame, text="Test Model")
        test_frame.grid(column=0, row=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(test_frame, text="Select Test Image", command=self.select_test_image).grid(column=0, row=0, padx=5, pady=5)
        self.test_result = ttk.Label(test_frame, text="")
        self.test_result.grid(column=0, row=1, columnspan=2, padx=5, pady=5)

    def start_camera(self):
        if self.is_capturing:
            return
            
        try:
            self.cap = cv2.VideoCapture(self.camera_index.get())
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open camera")
                return
                
            self.is_capturing = True
            threading.Thread(target=self.update_camera, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Could not start camera: {str(e)}")
            
    def stop_camera(self):
        self.is_capturing = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            
    def update_camera(self):
        while self.is_capturing:
            ret, frame = self.cap.read()
            if ret:
                # Convert to RGB for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize for display
                frame_resized = cv2.resize(frame_rgb, (640, 480))
                # Convert to PhotoImage
                img = tk.PhotoImage(data=cv2.imencode('.png', frame_resized)[1].tobytes())
                # Update label
                self.camera_label.configure(image=img)
                self.camera_label.image = img
            time.sleep(0.03)  # ~30 FPS
            
    def capture_image(self, class_type):
        if not self.is_capturing or not hasattr(self, 'project_dir'):
            messagebox.showerror("Error", "Camera not started or project not set up")
            return
            
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image")
            return
            
        # Save the image
        timestamp = int(time.time() * 1000)
        img_path = os.path.join(self.project_dir, "dataset", class_type, f"img_{timestamp}.jpg")
        cv2.imwrite(img_path, frame)
        
        # Update counts
        self.update_image_counts()
        
    def import_images_from_folder(self, class_type):
        """
        Import all images from a selected folder
        """
        if not hasattr(self, 'project_dir'):
            messagebox.showerror("Error", "Project not set up")
            return
            
        # Ask for folder
        folder_path = filedialog.askdirectory(title=f"Select folder containing {class_type} images")
        if not folder_path:
            return
            
        # Get list of image files
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        image_files = []
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(image_extensions) and os.path.isfile(os.path.join(folder_path, file)):
                image_files.append(os.path.join(folder_path, file))
                
        if not image_files:
            messagebox.showinfo("Info", "No image files found in the selected folder")
            return
            
        # Confirm import
        confirm = messagebox.askyesno(
            "Confirm Import", 
            f"Found {len(image_files)} image files. Import them as {class_type} examples?"
        )
        
        if not confirm:
            return
            
        # Import images
        self._process_image_import(image_files, class_type)
        
    def import_image_files(self, class_type):
        """
        Import selected image files
        """
        if not hasattr(self, 'project_dir'):
            messagebox.showerror("Error", "Project not set up")
            return
            
        # Ask for files
        image_extensions = (
            ('Image files', '*.jpg *.jpeg *.png *.bmp *.gif'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('PNG files', '*.png'),
            ('All files', '*.*')
        )
        
        files = filedialog.askopenfilenames(
            title=f"Select {class_type} images",
            filetypes=image_extensions
        )
        
        if not files:
            return
            
        # Import images
        self._process_image_import(files, class_type)
        
    def _process_image_import(self, file_paths, class_type):
        """
        Process a list of image files to import
        """
        if not file_paths:
            return
            
        # Get target directory
        target_dir = os.path.join(self.project_dir, "dataset", class_type)
        
        # Start import in a separate thread
        threading.Thread(
            target=self._import_images_thread,
            args=(file_paths, target_dir),
            daemon=True
        ).start()
        
    def _import_images_thread(self, file_paths, target_dir):
        """
        Thread to import images
        """
        total = len(file_paths)
        imported = 0
        errors = 0
        
        # Reset progress bar
        self.root.after(0, lambda: self.import_progress.config(value=0))
        self.root.after(0, lambda: self.import_status.config(text=f"Importing 0/{total} images..."))
        
        for i, file_path in enumerate(file_paths):
            try:
                # Update progress
                progress = (i + 1) / total * 100
                self.root.after(0, lambda p=progress: self.import_progress.config(value=p))
                self.root.after(0, lambda i=i, t=total: self.import_status.config(text=f"Importing {i+1}/{t} images..."))
                
                # Read image to validate and potentially resize
                img = cv2.imread(file_path)
                if img is None:
                    errors += 1
                    continue
                    
                # Save to target directory with unique name
                timestamp = int(time.time() * 1000) + i  # Add i to avoid duplicate timestamps
                filename = f"img_{timestamp}.jpg"
                output_path = os.path.join(target_dir, filename)
                
                # Optionally resize image
                # img_resized = cv2.resize(img, (224, 224))
                # cv2.imwrite(output_path, img_resized)
                
                # Or just copy the image
                cv2.imwrite(output_path, img)
                
                imported += 1
                
            except Exception as e:
                errors += 1
                print(f"Error importing {file_path}: {str(e)}")
                
            # Small delay to avoid UI freezing
            time.sleep(0.01)
            
        # Update final status
        self.root.after(0, lambda: self.import_status.config(
            text=f"Import complete. {imported} images imported, {errors} errors."
        ))
        
        # Update image counts
        self.root.after(0, self.update_image_counts)
        
    def update_image_counts(self):
        if hasattr(self, 'project_dir'):
            pos_dir = os.path.join(self.project_dir, "dataset", "positive")
            neg_dir = os.path.join(self.project_dir, "dataset", "negative")
            
            pos_count = len([f for f in os.listdir(pos_dir) if os.path.isfile(os.path.join(pos_dir, f))])
            neg_count = len([f for f in os.listdir(neg_dir) if os.path.isfile(os.path.join(neg_dir, f))])
            
            self.positive_count.config(text=str(pos_count))
            self.negative_count.config(text=str(neg_count))
            
    def train_model(self):
        if not hasattr(self, 'project_dir'):
            messagebox.showerror("Error", "Project not set up")
            return
            
        # Check if we have enough images
        pos_dir = os.path.join(self.project_dir, "dataset", "positive")
        neg_dir = os.path.join(self.project_dir, "dataset", "negative")
        
        pos_count = len([f for f in os.listdir(pos_dir) if os.path.isfile(os.path.join(pos_dir, f))])
        neg_count = len([f for f in os.listdir(neg_dir) if os.path.isfile(os.path.join(neg_dir, f))])
        
        if pos_count < 10 or neg_count < 10:
            messagebox.showerror("Error", "Need at least 10 images of each class")
            return
            
        # Disable buttons during training
        self.train_button.config(state="disabled")
        self.convert_button.config(state="disabled")
        self.deploy_button.config(state="disabled")
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "Starting training...\n")
        
        # Start training in a separate thread
        self.is_training = True
        self.training_thread = threading.Thread(target=self.train_model_thread)
        self.training_thread.daemon = True
        self.training_thread.start()
        
    def train_model_thread(self):
        try:
            # Prepare data directory
            dataset_dir = os.path.join(self.project_dir, "dataset")
            
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
                batch_size=self.batch_size.get(),
                class_mode='binary',
                subset='training'
            )
            
            validation_generator = train_datagen.flow_from_directory(
                dataset_dir,
                target_size=(224, 224),
                batch_size=self.batch_size.get(),
                class_mode='binary',
                subset='validation'
            )
            
            # Add to log
            self.root.after(0, lambda: self.log_text.insert(tk.END, f"Classes found: {train_generator.class_indices}\n"))
            
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
            self.model = Model(inputs=base_model.input, outputs=predictions)
            
            # Compile model
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate.get()),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            # Create a callback for updating the UI
            class UICallback(tf.keras.callbacks.Callback):
                def __init__(self, app):
                    super().__init__()
                    self.app = app
                
                def on_epoch_end(self, epoch, logs=None):
                    if not logs:
                        logs = {}
                    msg = f"Epoch {epoch+1}/{self.app.epochs.get()}: "
                    msg += f"loss={logs.get('loss', 0):.4f}, "
                    msg += f"accuracy={logs.get('accuracy', 0):.4f}, "
                    msg += f"val_loss={logs.get('val_loss', 0):.4f}, "
                    msg += f"val_accuracy={logs.get('val_accuracy', 0):.4f}\n"
                    
                    self.app.root.after(0, lambda: self.app.log_text.insert(tk.END, msg))
                    self.app.root.after(0, lambda: self.app.log_text.see(tk.END))
                    
                    # Update progress bar
                    progress_val = (epoch + 1) / self.app.epochs.get() * 100
                    self.app.root.after(0, lambda: self.app.progress.config(value=progress_val))
            
            # Train the model
            self.root.after(0, lambda: self.log_text.insert(tk.END, "Training model...\n"))
            
            history = self.model.fit(
                train_generator,
                steps_per_epoch=train_generator.samples // self.batch_size.get(),
                validation_data=validation_generator,
                validation_steps=validation_generator.samples // self.batch_size.get(),
                epochs=self.epochs.get(),
                callbacks=[UICallback(self)]
            )
            
            # Save the model
            model_path = os.path.join(self.project_dir, "models", "model.h5")
            self.model.save(model_path)
            
            # Update UI
            self.root.after(0, lambda: self.log_text.insert(tk.END, f"Model saved to {model_path}\n"))
            self.root.after(0, lambda: self.model_status.config(text="Trained"))
            
            # Enable convert button
            self.root.after(0, lambda: self.train_button.config(state="normal"))
            self.root.after(0, lambda: self.convert_button.config(state="normal"))
            
            # Create model metadata
            metadata = {
                "project_name": self.project_name.get(),
                "date_created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "classes": list(train_generator.class_indices.keys()),
                "class_indices": train_generator.class_indices,
                "training_params": {
                    "epochs": self.epochs.get(),
                    "batch_size": self.batch_size.get(),
                    "learning_rate": self.learning_rate.get()
                },
                "training_results": {
                    "final_accuracy": float(history.history['accuracy'][-1]),
                    "final_val_accuracy": float(history.history['val_accuracy'][-1])
                }
            }
            
            with open(os.path.join(self.project_dir, "models", "metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=4)
                
        except Exception as e:
            self.root.after(0, lambda: self.log_text.insert(tk.END, f"Error during training: {str(e)}\n"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Training failed: {str(e)}"))
        finally:
            self.is_training = False
            self.root.after(0, lambda: self.train_button.config(state="normal"))
            
    def convert_to_tflite(self):
        if not hasattr(self, 'model') and not hasattr(self, 'project_dir'):
            # Try to load the model
            try:
                model_path = os.path.join(self.project_dir, "models", "model.h5")
                if os.path.exists(model_path):
                    self.model = tf.keras.models.load_model(model_path)
                else:
                    messagebox.showerror("Error", "Model not found")
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Could not load model: {str(e)}")
                return
        
        try:
            # Create a converter
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            
            # Convert the model
            tflite_model = converter.convert()
            
            # Save the TFLite model
            tflite_path = os.path.join(self.project_dir, "models", "model.tflite")
            with open(tflite_path, 'wb') as f:
                f.write(tflite_model)
            
            # Apply quantization for smaller size
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            tflite_quantized_model = converter.convert()
            
            # Save the quantized model
            tflite_q_path = os.path.join(self.project_dir, "models", "model_quantized.tflite")
            with open(tflite_q_path, 'wb') as f:
                f.write(tflite_quantized_model)
            
            # Update UI
            self.tflite_status.config(text="Converted")
            self.deploy_button.config(state="normal")
            
            messagebox.showinfo("Success", "Models converted to TFLite format")
            
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            
    def deploy_model(self):
        if not hasattr(self, 'project_dir'):
            messagebox.showerror("Error", "Project not set up")
            return
            
        # Check if TFLite model exists
        tflite_path = os.path.join(self.project_dir, "models", "model.tflite")
        if not os.path.exists(tflite_path):
            messagebox.showerror("Error", "TFLite model not found")
            return
            
        try:
            # Load model and metadata
            with open(tflite_path, 'rb') as f:
                model_data = f.read()
                
            metadata_path = os.path.join(self.project_dir, "models", "metadata.json")
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # Prepare data for API
            files = {
                'model': ('model.tflite', model_data, 'application/octet-stream'),
                'metadata': ('metadata.json', json.dumps(metadata), 'application/json')
            }
            
            # Make API request
            api_url = f"{self.api_endpoint.get()}/api/models"
            response = requests.post(api_url, files=files)
            
            if response.status_code == 200:
                result = response.json()
                self.deploy_status.config(text=f"Deployed (ID: {result.get('model_id', 'Unknown')})")
                messagebox.showinfo("Success", f"Model deployed successfully with ID: {result.get('model_id', 'Unknown')}")
            else:
                messagebox.showerror("Error", f"Deployment failed: {response.text}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Deployment failed: {str(e)}")
            
    def select_test_image(self):
        if not hasattr(self, 'model'):
            messagebox.showerror("Error", "Model not trained")
            return
            
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if not file_path:
            return
            
        try:
            # Load and preprocess the image
            img = tf.keras.preprocessing.image.load_img(file_path, target_size=(224, 224))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0  # Normalize
            
            # Make prediction
            prediction = self.model.predict(img_array)
            
            # Load metadata to get class names
            metadata_path = os.path.join(self.project_dir, "models", "metadata.json")
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # Get class names
            classes = metadata.get('classes', ['negative', 'positive'])
            
            # Interpret result
            if prediction[0][0] > 0.5:
                result = classes[1]  # Positive
                confidence = float(prediction[0][0])
            else:
                result = classes[0]  # Negative
                confidence = 1 - float(prediction[0][0])
                
            # Display result
            self.test_result.config(text=f"Result: {result} (Confidence: {confidence:.2f})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModelTrainerApp(root)
    root.mainloop()