import cv2
import numpy as np
from ultralytics import YOLO
from src.config import CONFIDENCE_THRESHOLD, MODEL_PATH, logger
from src.face_auth import FaceAuthenticator

class ObjectDetector:
    def __init__(self, model_path=MODEL_PATH):
        logger.info(f"Loading YOLO model: {model_path}")
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e
            
        self.classes = [0]  # Class 0 is 'person'
        
        # Initialize Face Authenticator
        self.face_auth = FaceAuthenticator()
        
        # Optimization: Cache identities for Track IDs
        self.identity_map = {} # {track_id: {'name': str, 'last_checked': int}}
        self.frame_count = 0
        self.face_check_interval = 5 # Faster check (every 5 frames) for better responsiveness

    def detect_frame(self, frame, roi_points):
        """
        Detects persons using Pose Estimation.
        Triggers CRITICAL only if Hands (Wrists) or Face (Nose) enter the ROI.
        """
        if frame is None:
            return None, [], "SAFE"

        self.frame_count += 1
        
        # Use YOLOv8 Pose Tracking
        # persist=True keeps Track IDs (consistent colors/IDs)
        results = self.model.track(frame, classes=self.classes, conf=CONFIDENCE_THRESHOLD, persist=True, verbose=False)
        
        height, width = frame.shape[:2]
        detections = []
        overall_status = "SAFE"
        
        # Prepare ROI polygon
        roi_pixel_cnt = np.array([
            (int(x * width), int(y * height)) 
            for x, y in roi_points
        ], dtype=np.int32)
        
        # Draw ROI
        cv2.polylines(frame, [roi_pixel_cnt], isClosed=True, color=(255, 0, 0), thickness=2)
        cv2.putText(frame, "Restricted Area", (roi_pixel_cnt[0][0], roi_pixel_cnt[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        for result in results:
            if result.boxes is None:
                continue
                
            # Iterate through detected persons
            for i, box in enumerate(result.boxes):
                # --- Basic Info ---
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                track_id = int(box.id[0].cpu().numpy()) if box.id is not None else -1
                conf = float(box.conf[0].cpu().numpy())
                
                # --- Pose / Keypoints ---
                # Keypoints format: [N, 17, 3] -> (x, y, conf)
                # We need the keypoints for this specific person (index i)
                kpts = result.keypoints.data[i].cpu().numpy() # Shape (17, 3)
                
                # COCO Keypoint Indices:
                # 0: Nose
                # 9: Left Wrist
                # 10: Right Wrist
                
                # Check critical points
                nose = kpts[0]
                l_wrist = kpts[9]
                r_wrist = kpts[10]
                
                critical_points = [
                    ('Nose', nose),
                    ('L-Wrist', l_wrist),
                    ('R-Wrist', r_wrist)
                ]
                
                # Logic: Check if ANY critical point is inside ROI
                is_breach = False
                breach_points = []
                
                for pt_name, pt_data in critical_points:
                    pixel_x, pixel_y, pt_conf = pt_data
                    if pt_conf < 0.5: # Skip low confidence points
                        continue
                        
                    pixel_x, pixel_y = int(pixel_x), int(pixel_y)
                    
                    # Point Check
                    if cv2.pointPolygonTest(roi_pixel_cnt, (pixel_x, pixel_y), False) >= 0:
                        is_breach = True
                        breach_points.append((pixel_x, pixel_y))
                
                
                # --- FACE RECOGNITION (Detected in Authorization Step) ---
                name = "Unknown"
                
                # --- STATUS DECISION ---
                status = "SAFE"
                color = (0, 255, 0) # Green
                
                # --- VISUALIZATION ---
                
                # --- VISUALIZATION ---
                
                # 1. Calculate Face Bounding Box from Keypoints (Nose, Eyes, Ears)
                face_kpts = kpts[0:5] # First 5 points are face
                valid_face_pts = face_kpts[face_kpts[:, 2] > 0.5] # Filter low conf
                
                face_bbox = None
                if len(valid_face_pts) >= 2:
                    # Get bounds of keypoints
                    bg_x1 = int(np.min(valid_face_pts[:, 0]))
                    bg_y1 = int(np.min(valid_face_pts[:, 1]))
                    bg_x2 = int(np.max(valid_face_pts[:, 0]))
                    bg_y2 = int(np.max(valid_face_pts[:, 1]))
                    
                    # Calculate center and dimensions
                    cx, cy = (bg_x1 + bg_x2) // 2, (bg_y1 + bg_y2) // 2
                    w = bg_x2 - bg_x1
                    h = bg_y2 - bg_y1
                    
                    # Enforce Square Shape (use max dimension)
                    sq_size = max(w, h)
                    
                    # Add meaningful padding (e.g., 60% extra) to cover whole head
                    padding = int(sq_size * 0.8) 
                    size = sq_size + padding
                    
                    half_size = size // 2
                    
                    fx1 = max(0, cx - half_size)
                    fy1 = max(0, cy - half_size)
                    fx2 = min(width, cx + half_size)
                    fy2 = min(height, cy + half_size)
                    
                    # Name Label (Above Face)
                    label_text = f"{name}"
                    
                    # --- FACE RECOGNITION DISABLED ---
                    # We are forcing status to CRITICAL if breach, ignoring identity for now.
                    if is_breach:
                         status = "CRITICAL"
                         color = (0, 0, 255) # Red
                         overall_status = "CRITICAL"
                         label_text = f"INTRUDER [BREACH]"
                    
                    cv2.putText(frame, label_text, (fx1, fy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), color, 2)

                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "conf": conf,
                    "status": status,
                    "name": name
                })

        return frame, detections, overall_status

    def draw_skeleton(self, frame, kpts, color):
        """Draws simple skeleton lines"""
        # Pairs of indices to connect
        skeleton = [
            (5, 7), (7, 9), # Left Arm
            (6, 8), (8, 10), # Right Arm
            (5, 6), # Shoulders
            (5, 11), (6, 12), # Body
            (11, 12), # Hips
            (0, 5), (0, 6) # Head to shoulders
        ]
        
        for p1, p2 in skeleton:
            pt1 = kpts[p1]
            pt2 = kpts[p2]
            if pt1[2] > 0.5 and pt2[2] > 0.5:
                cv2.line(frame, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), color, 2)

