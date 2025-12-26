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
        Detects persons, tracks them, and verifies identity via face recognition.
        """
        if frame is None:
            return None, [], "SAFE"

        self.frame_count += 1
        
        # Use YOLOv8 Tracking (persist=True is crucial for ID consistency)
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
            # Check if we have detections
            if result.boxes is None:
                continue
                
            for box in result.boxes:
                # Get Box Coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Get Track ID (if available)
                track_id = int(box.id[0].cpu().numpy()) if box.id is not None else -1
                
                conf = float(box.conf[0].cpu().numpy())
                
                # ROI Check
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                is_inside = cv2.pointPolygonTest(roi_pixel_cnt, (center_x, center_y), False) >= 0
                
                # --- FACE RECOGNITION LOGIC ---
                name = "Unknown"
                
                # PROACTIVE DETECTION: Check faces EVERYWHERE, not just inside ROI.
                # This ensures we know who they are before they enter the restricted zone.
                
                # Check if we need to run recognition
                should_check = False
                if track_id != -1:
                    if track_id not in self.identity_map:
                        should_check = True
                    elif (self.frame_count - self.identity_map[track_id]['last_checked']) > self.face_check_interval:
                        should_check = True
                        
                    # If we already know them, retrieve name
                    if not should_check:
                        name = self.identity_map[track_id]['name']
                else:
                    # No track ID (rare with persist=True), always check
                    should_check = True
                
                if should_check:
                    # Run Face Auth
                    name = self.face_auth.identify_face(frame, (x1, y1, x2, y2))
                    
                    # Update Cache
                    if track_id != -1:
                        self.identity_map[track_id] = {
                            'name': name,
                            'last_checked': self.frame_count
                        }
                
                # --- STATUS DETERMINATION ---
                status = "WARNING"
                color = (0, 255, 255) # Yellow
                
                if is_inside:
                    if name == "Unknown":
                        status = "CRITICAL"
                        color = (0, 0, 255) # Red
                        overall_status = "CRITICAL"
                    else:
                        status = "AUTHORIZED"
                        color = (0, 255, 0) # Green
                        # If authorized, we don't escalate overall_status to CRITICAL
                else:
                    # Outside ROI
                    if overall_status != "CRITICAL":
                        overall_status = "WARNING"

                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "conf": conf,
                    "status": status,
                    "name": name
                })
                
                # Visualization
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Label: Status + Name (if known) + Conf
                label_text = f"{status}"
                if name != "Unknown":
                    label_text += f" ({name})"
                
                cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.circle(frame, (center_x, center_y), 5, color, -1)

        return frame, detections, overall_status
