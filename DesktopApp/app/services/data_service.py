"""
Data Service - Handles data import and management
"""

import os
import cv2
import shutil
import time
import threading
from PySide6.QtCore import QObject, Signal

class DataService(QObject):
    """Service for importing and managing image data"""
    
    import_started = Signal(str, int)
    import_progress = Signal(int, int)
    import_finished = Signal(bool, str, int)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.import_thread = None
    
    def import_images_from_folder(self, folder_path, class_type, project_path):
        """Import all images from a selected folder"""
        if self.import_thread and self.import_thread.is_alive():
            return False, "Import already in progress"
        
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        image_files = []
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(image_extensions) and os.path.isfile(os.path.join(folder_path, file)):
                image_files.append(os.path.join(folder_path, file))
        
        if not image_files:
            return False, "No image files found in the selected folder"
        
        self.import_thread = threading.Thread(
            target=self._import_images_thread,
            args=(image_files, class_type, project_path),
            daemon=True
        )
        self.import_thread.start()
        
        self.import_started.emit(class_type, len(image_files))
        
        return True, f"Started importing {len(image_files)} images"
    
    def import_image_files(self, file_paths, class_type, project_path):
        """Import selected image files"""
        if self.import_thread and self.import_thread.is_alive():
            return False, "Import already in progress"
        
        if not file_paths:
            return False, "No files selected"
        
        self.import_thread = threading.Thread(
            target=self._import_images_thread,
            args=(file_paths, class_type, project_path),
            daemon=True
        )
        self.import_thread.start()
        
        self.import_started.emit(class_type, len(file_paths))
        
        return True, f"Started importing {len(file_paths)} images"
    
    def _import_images_thread(self, file_paths, class_type, project_path):
        """Thread to import images"""
        total = len(file_paths)
        imported = 0
        errors = 0
        
        target_dir = os.path.join(project_path, "dataset", class_type)
        
        for i, file_path in enumerate(file_paths):
            try:
                self.import_progress.emit(i + 1, total)
                
                img = cv2.imread(file_path)
                if img is None:
                    errors += 1
                    continue
                
                timestamp = int(time.time() * 1000) + i
                filename = f"img_{timestamp}.jpg"
                output_path = os.path.join(target_dir, filename)
                
                cv2.imwrite(output_path, img)
                
                imported += 1
                
            except Exception as e:
                errors += 1
                print(f"Error importing {file_path}: {str(e)}")
            
            time.sleep(0.01)
        
        message = f"Import complete: {imported} images imported, {errors} errors"
        self.import_finished.emit(imported > 0, message, imported)