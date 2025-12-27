import os
import cv2
import numpy as np
from loguru import logger
import pickle

# Force Disable Face Recognition to resolve startup crash
FACE_REC_AVAILABLE = False
face_recognition = None

class FaceAuthenticator:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        logger.warning("Face Recognition is DISABLED via code.")

    def _load_library(self):
        pass

    def _load_known_faces(self):
        pass

    def refresh_faces(self):
        pass

    def identify_face(self, frame, bbox):
        return "Unknown"
        logger.info("Loading known faces from known_faces...")
        if not os.path.exists("known_faces"):
            os.makedirs("known_faces")
            return

        for filename in os.listdir("known_faces"):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join("known_faces", filename)
                try:
                    # 1. قراءة الصورة بـ OpenCV
                    img = cv2.imread(filepath)
                    
                    if img is None:
                        logger.warning(f"Could not read {filename}")
                        continue

                    # 2. المعالجة السحرية (تصحيح الألوان)
                    # لو الصورة فيها شفافية (4 قنوات)، شيل الشفافية
                    if len(img.shape) > 2 and img.shape[2] == 4:
                        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                    else:
                        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                    # 3. خطوة هامة جداً: إجبار الصورة تكون 8-bit
                    # ده بيحل مشكلة Unsupported image type
                    rgb_img = np.array(rgb_img, dtype=np.uint8)

                    # 4. استخراج البصمة
                    encodings = face_recognition.face_encodings(rgb_img)

                    if len(encodings) > 0:
                        self.known_face_encodings.append(encodings[0])
                        # تنظيف الاسم (شيل الامتداد والأرقام)
                        name = os.path.splitext(filename)[0].split('_')[0]
                        self.known_face_names.append(name)
                        logger.success(f"Loaded: {name}")
                    else:
                        logger.warning(f"No face found in {filename}")

                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
        
        
        logger.info(f"Total known faces loaded: {len(self.known_face_names)}")

    def refresh_faces(self):
        """Reloads known faces from disk (useful after adding a new face)"""
        self.known_face_encodings = []
        self.known_face_names = []
        self._load_known_faces()

    def identify_face(self, frame, bbox):
        if not FACE_REC_AVAILABLE or not self.known_face_encodings:
            return "Unknown"
            
        # Unpack bbox to match user's logic
        x1, y1, x2, y2 = bbox

        try:
            # قص الوجه
            face_img = frame[y1:y2, x1:x2]
            if face_img.size == 0: return "Unknown"

            # تحويل وتجهيز
            rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            rgb_face = np.array(rgb_face, dtype=np.uint8)
            
            # فحص سريع
            face_encodings = face_recognition.face_encodings(rgb_face)
            
            if not face_encodings:
                return "Unknown"
            
            # مقارنة
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encodings[0], tolerance=0.5)
            if True in matches:
                first_match_index = matches.index(True)
                return self.known_face_names[first_match_index]
            
            return "Unknown"

        except Exception as e:
            return "Unknown"
