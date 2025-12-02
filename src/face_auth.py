try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    face_recognition = None
    FACE_REC_AVAILABLE = False

import cv2
import os
import numpy as np
from pathlib import Path
from src.config import logger

class FaceAuthenticator:
    def __init__(self, known_faces_dir="known_faces"):
        self.known_encodings = []
        self.known_names = []
        self.known_faces_dir = Path(known_faces_dir)
        
        if FACE_REC_AVAILABLE:
            self._load_known_faces()
        else:
            logger.warning("Face Recognition library not available. Running in detection-only mode.")

    def _load_known_faces(self):
        """
        Loads all .jpg and .png images from the known_faces directory
        and encodes them for recognition.
        """
        if not self.known_faces_dir.exists():
            logger.warning(f"Directory '{self.known_faces_dir}' not found. Creating it.")
            self.known_faces_dir.mkdir(parents=True, exist_ok=True)
            return

        logger.info(f"Loading known faces from {self.known_faces_dir}...")
        
        for file_path in self.known_faces_dir.glob("*"):
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                try:
                    # Load image using OpenCV
                    img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
                    
                    if img is None:
                        logger.warning(f"Could not read image: {file_path.name}")
                        continue
                        
                    # Handle different channel counts
                    if len(img.shape) == 2:
                        # Grayscale -> RGB
                        rgb_image = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                    elif img.shape[2] == 4:
                        # BGRA -> RGB
                        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                    elif img.shape[2] == 3:
                        # BGR -> RGB
                        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    else:
                        logger.warning(f"Unsupported image format {file_path.name} with shape {img.shape}. Skipping.")
                        continue
                        
                    # Ensure uint8 type and contiguous memory layout (Critical for dlib)
                    if rgb_image.dtype != np.uint8:
                        rgb_image = rgb_image.astype(np.uint8)
                    
                    rgb_image = np.ascontiguousarray(rgb_image)
                    
                    # Encode face (assume one face per image)
                    encodings = face_recognition.face_encodings(rgb_image)
                    
                    if encodings:
                        self.known_encodings.append(encodings[0])
                        # Use filename (without extension) as the name
                        name = file_path.stem.replace("_", " ").title()
                        self.known_names.append(name)
                        logger.info(f"Loaded face: {name}")
                    else:
                        logger.warning(f"No face found in {file_path.name}. Skipping.")
                except Exception as e:
                    logger.error(f"Error loading {file_path.name}: {e}")
        
        logger.info(f"Total known faces loaded: {len(self.known_names)}")

    def identify_face(self, frame, bbox):
        """
        Identifies a face within the given bounding box.
        
        Args:
            frame: The full video frame (BGR).
            bbox: Tuple (x1, y1, x2, y2).
            
        Returns:
            name: The name of the identified person, or "Unknown".
        """
        if not FACE_REC_AVAILABLE:
            return "Unknown"

        if not self.known_encodings:
            return "Unknown"

        x1, y1, x2, y2 = bbox
        
        # Ensure bbox is within frame boundaries
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        # Crop the face
        face_img = frame[y1:y2, x1:x2]
        
        if face_img.size == 0:
            return "Unknown"

        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        
        # Get encoding for the cropped face
        # We pass the whole image but since we cropped it, we can just say the face is the whole image
        # Or better, let face_recognition find it in the crop to be robust against loose bboxes
        # However, finding faces is slow. Since we have the bbox, let's force it.
        # face_encodings takes a list of locations [(top, right, bottom, left)]
        # Since we cropped, the location is the whole crop: (0, width, height, 0)
        face_h, face_w = face_img.shape[:2]
        
        try:
            # Attempt to encode the face directly from the crop
            current_encodings = face_recognition.face_encodings(rgb_face, known_face_locations=[(0, face_w, face_h, 0)])
            
            if not current_encodings:
                return "Unknown"
                
            current_encoding = current_encodings[0]
            
            # Compare with known faces
            matches = face_recognition.compare_faces(self.known_encodings, current_encoding, tolerance=0.6)
            name = "Unknown"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_encodings, current_encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                name = self.known_names[best_match_index]
                
            return name

        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return "Unknown"
