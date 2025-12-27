import os
import cv2
import numpy as np
from loguru import logger

# Flag to control face recognition availability
FACE_REC_AVAILABLE = False
face_recognition = None


class FaceAuthenticator:
    """
    Handles face recognition:
    - Loads known faces from disk
    - Encodes faces
    - Identifies detected faces
    """

    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []

        # Try to safely load face_recognition
        self._load_library()

        if FACE_REC_AVAILABLE:
            self._load_known_faces()
        else:
            logger.warning("Face Recognition is DISABLED (library not available).")

    def _load_library(self):
        """
        Safely loads face_recognition library to avoid startup crashes.
        """
        global FACE_REC_AVAILABLE, face_recognition

        try:
            import face_recognition as fr
            face_recognition = fr
            FACE_REC_AVAILABLE = True
            logger.success("face_recognition library loaded successfully.")
        except Exception as e:
            FACE_REC_AVAILABLE = False
            face_recognition = None
            logger.error(f"Failed to load face_recognition: {e}")

    def _load_known_faces(self):
        """
        Loads face images from 'known_faces/' directory
        and extracts their face encodings.
        """
        if not FACE_REC_AVAILABLE:
            return

        faces_dir = "known_faces"
        os.makedirs(faces_dir, exist_ok=True)

        logger.info("Loading known faces...")

        for filename in os.listdir(faces_dir):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            filepath = os.path.join(faces_dir, filename)

            try:
                # Read image using OpenCV
                img = cv2.imread(filepath)
                if img is None:
                    logger.warning(f"Could not read image: {filename}")
                    continue

                # Convert image to RGB
                if img.shape[2] == 4:
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                else:
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Force uint8 format (fixes unsupported image type errors)
                rgb_img = np.array(rgb_img, dtype=np.uint8)

                # Extract face encodings
                encodings = face_recognition.face_encodings(rgb_img)

                if not encodings:
                    logger.warning(f"No face detected in {filename}")
                    continue

                # Save encoding and extracted name
                self.known_face_encodings.append(encodings[0])

                name = os.path.splitext(filename)[0].split("_")[0]
                self.known_face_names.append(name)

                logger.success(f"Loaded face: {name}")

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

        logger.info(f"Total known faces loaded: {len(self.known_face_names)}")

    def refresh_faces(self):
        """
        Reloads known faces from disk.
        Useful after adding new face images.
        """
        self.known_face_encodings.clear()
        self.known_face_names.clear()
        self._load_known_faces()

    def identify_face(self, frame, bbox):
        """
        Identifies a face inside a given bounding box.

        Args:
            frame (ndarray): Full camera frame (BGR)
            bbox (tuple): (x1, y1, x2, y2)

        Returns:
            str: Person name or 'Unknown'
        """
        if not FACE_REC_AVAILABLE or not self.known_face_encodings:
            return "Unknown"

        x1, y1, x2, y2 = bbox

        try:
            # Crop face from frame
            face_img = frame[y1:y2, x1:x2]
            if face_img.size == 0:
                return "Unknown"

            # Convert to RGB
            rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            rgb_face = np.array(rgb_face, dtype=np.uint8)

            # Encode detected face
            encodings = face_recognition.face_encodings(rgb_face)
            if not encodings:
                return "Unknown"

            # Compare against known faces
            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                encodings[0],
                tolerance=0.5
            )

            if True in matches:
                idx = matches.index(True)
                return self.known_face_names[idx]

            return "Unknown"

        except Exception as e:
            logger.error(f"Face identification error: {e}")
            return "Unknown"
