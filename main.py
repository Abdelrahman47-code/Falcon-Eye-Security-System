"""
Falcon Eye Security System (FESS) - Professional GUI Dashboard
Premium customtkinter-based interface for advanced security monitoring
"""

import cv2
import time
import threading
import queue
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from src.config import CAMERA_INDEX, ALERT_COOLDOWN, LOGS_DIR, ROI_POINTS, logger
from src.detector import ObjectDetector
from src.notifier import TelegramBot


# Professional Color Palette
class Colors:
    # Primary Colors
    BG_DARK = "#0a0e27"
    BG_CARD = "#141b2d"
    BG_CARD_LIGHT = "#1f2940"
    
    # Accent Colors
    ACCENT_BLUE = "#2196F3"
    ACCENT_CYAN = "#00E5FF"
    ACCENT_GREEN = "#00E676"
    ACCENT_RED = "#FF1744"
    ACCENT_ORANGE = "#FF9800"
    ACCENT_PURPLE = "#9C27B0"
    
    # Status Colors
    SUCCESS = "#00E676"
    WARNING = "#FFC107"
    CRITICAL = "#FF1744"
    INFO = "#64B5F6"
    
    # Text Colors
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B0BEC5"
    TEXT_MUTED = "#78909C"


class ThreadedCamera:
    """
    Reads frames in a separate thread to prevent I/O blocking.
    """
    def __init__(self, src=0):
        self.src = src
        self.capture = cv2.VideoCapture(src)
        self.q = queue.Queue(maxsize=2)
        self.running = True
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                logger.warning("Camera read failed")
                time.sleep(0.1)
                continue
            
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        try:
            return self.q.get_nowait() if not self.q.empty() else None
        except queue.Empty:
            return None

    def release(self):
        self.running = False
        if self.capture.isOpened():
            self.capture.release()


class StatusBadge(ctk.CTkFrame):
    """Custom status badge widget with icon and text"""
    def __init__(self, master, icon, label, status_text="", **kwargs):
        super().__init__(master, fg_color=Colors.BG_CARD_LIGHT, corner_radius=12, **kwargs)
        
        self.grid_columnconfigure(1, weight=1)
        
        # Icon
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=28),
            width=50
        )
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=(15, 10), pady=15)
        
        # Label
        self.label = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_MUTED,
            anchor="w"
        )
        self.label.grid(row=0, column=1, sticky="w", padx=(0, 15), pady=(15, 0))
        
        # Status Text
        self.status_label = ctk.CTkLabel(
            self,
            text=status_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        self.status_label.grid(row=1, column=1, sticky="w", padx=(0, 15), pady=(0, 15))
    
    def update_status(self, text, color=Colors.TEXT_PRIMARY):
        """Update status text and color"""
        self.status_label.configure(text=text, text_color=color)


class StatCard(ctk.CTkFrame):
    """Statistics card widget"""
    def __init__(self, master, label, value="0", icon="", color=Colors.ACCENT_BLUE, **kwargs):
        super().__init__(master, fg_color=Colors.BG_CARD_LIGHT, corner_radius=10, **kwargs)
        
        # Icon and Value
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 5))
        
        ctk.CTkLabel(
            header_frame,
            text=icon,
            font=ctk.CTkFont(size=20),
            text_color=color
        ).pack(side="left")
        
        self.value_label = ctk.CTkLabel(
            header_frame,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        )
        self.value_label.pack(side="right")
        
        # Label
        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(0, 12))
    
    def update_value(self, value):
        """Update the displayed value"""
        self.value_label.configure(text=str(value))


class FESSApp(ctk.CTk):
    """
    Professional GUI Application for Falcon Eye Security System
    """
    def __init__(self):
        super().__init__()
        
        # Window Configuration
        self.title("🦅 Falcon Eye Security System - Professional Dashboard")
        
        # Laptop-friendly size (fits 1366x768 screens)
        window_width = 1100
        window_height = 650
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate center position
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        
        # Set geometry with centered position
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        
        # Set Dark Theme with custom colors
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure window background
        self.configure(fg_color=Colors.BG_DARK)
        
        # System State - AUTO-ARMED on startup
        self.armed = True
        self.last_alert_time = 0
        self.running = True
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'authorized_count': 0,
            'intruder_count': 0,
            'alerts_sent': 0
        }
        
        # Initialize Components
        logger.info("Initializing Professional GUI Dashboard...")
        
        try:
            self.detector = ObjectDetector()
        except Exception as e:
            logger.critical(f"Failed to initialize Detector: {e}")
            self.show_error_and_exit("Detector initialization failed")
            return
        
        self.bot = TelegramBot()
        self.bot.start()
        
        # Auto-arm the bot as well
        self.bot.is_armed = True
        
        # Camera
        logger.info(f"Connecting to camera: {CAMERA_INDEX}")
        self.camera = ThreadedCamera(CAMERA_INDEX)
        time.sleep(1.5)
        
        # Build UI
        self.build_ui()
        
        # Start Video Loop
        self.update_frame()
        
        # Handle Window Close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("✅ Professional FESS Dashboard Ready")
    
    def show_error_and_exit(self, message):
        """Show error dialog and exit"""
        import tkinter.messagebox as mb
        mb.showerror("Fatal Error", message)
        self.quit()
    
    def build_ui(self):
        """Construct the Professional GUI Layout"""
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=7)  # Video section
        self.grid_columnconfigure(1, weight=3)  # Control panel
        
        # ========== HEADER BAR ==========
        header = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, height=70, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        # Logo and Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=25, pady=15)
        
        ctk.CTkLabel(
            title_frame,
            text="🦅",
            font=ctk.CTkFont(size=32)
        ).pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(
            title_frame,
            text="FALCON EYE",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=Colors.ACCENT_CYAN
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="Security System",
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT_MUTED
        ).pack(side="left", padx=(10, 0))
        
        # System Time
        self.time_label = ctk.CTkLabel(
            header,
            text=datetime.now().strftime("%H:%M:%S"),
            font=ctk.CTkFont(size=18, family="Consolas"),
            text_color=Colors.TEXT_SECONDARY
        )
        self.time_label.pack(side="right", padx=25)
        
        # ========== LEFT PANEL: VIDEO FEED ==========
        video_container = ctk.CTkFrame(self, fg_color="transparent")
        video_container.grid(row=1, column=0, padx=(15, 8), pady=(15, 15), sticky="nsew")
        video_container.grid_rowconfigure(1, weight=1)
        video_container.grid_columnconfigure(0, weight=1)
        
        # Video Header
        video_header = ctk.CTkFrame(video_container, fg_color=Colors.BG_CARD, height=50, corner_radius=10)
        video_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        video_header.grid_propagate(False)
        
        ctk.CTkLabel(
            video_header,
            text="📹 LIVE FEED",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left", padx=20, pady=10)
        
        # Recording indicator
        self.recording_indicator = ctk.CTkLabel(
            video_header,
            text="● REC",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Colors.CRITICAL
        )
        self.recording_indicator.pack(side="right", padx=20)
        
        # Video Display
        self.video_frame = ctk.CTkFrame(video_container, fg_color=Colors.BG_CARD, corner_radius=10)
        self.video_frame.grid(row=1, column=0, sticky="nsew")
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        self.video_label.pack(expand=True, fill="both", padx=2, pady=2)
        
        # ========== RIGHT PANEL: CONTROL CENTER ==========
        control_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_CARD_LIGHT,
            scrollbar_button_hover_color=Colors.ACCENT_BLUE
        )
        control_container.grid(row=1, column=1, padx=(8, 15), pady=(15, 15), sticky="nsew")
        
        # === SYSTEM STATUS SECTION ===
        self.create_section_header(control_container, "⚡ SYSTEM STATUS")
        
        status_grid = ctk.CTkFrame(control_container, fg_color="transparent")
        status_grid.pack(fill="x", pady=(0, 20))
        status_grid.grid_columnconfigure((0, 1), weight=1)
        
        # Armed Status Badge (Auto-Armed)
        self.armed_badge = StatusBadge(
            status_grid,
            icon="🛡️",
            label="System Mode",
            status_text="ARMED",
            height=90
        )
        self.armed_badge.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.armed_badge.update_status("ARMED", Colors.CRITICAL)
        
        # Telegram Status Badge
        self.telegram_badge = StatusBadge(
            status_grid,
            icon="📡",
            label="Telegram Bot",
            status_text="OFFLINE",
            height=90
        )
        self.telegram_badge.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # Update Telegram status
        telegram_connected = self.bot.loop and self.bot.loop.is_running()
        self.telegram_badge.update_status(
            "ONLINE" if telegram_connected else "OFFLINE",
            Colors.SUCCESS if telegram_connected else Colors.CRITICAL
        )
        
        # === STATISTICS SECTION ===
        self.create_section_header(control_container, "📊 STATISTICS")
        
        stats_container = ctk.CTkFrame(control_container, fg_color="transparent")
        stats_container.pack(fill="x", pady=(0, 20))
        stats_container.grid_columnconfigure((0, 1), weight=1)
        
        # Stat Cards
        self.stat_detections = StatCard(
            stats_container,
            label="Total Detections",
            value="0",
            icon="👁️",
            color=Colors.ACCENT_BLUE
        )
        self.stat_detections.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))
        
        self.stat_authorized = StatCard(
            stats_container,
            label="Authorized",
            value="0",
            icon="✅",
            color=Colors.SUCCESS
        )
        self.stat_authorized.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))
        
        self.stat_intruders = StatCard(
            stats_container,
            label="Intruders",
            value="0",
            icon="⚠️",
            color=Colors.CRITICAL
        )
        self.stat_intruders.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=0)
        
        self.stat_alerts = StatCard(
            stats_container,
            label="Alerts Sent",
            value="0",
            icon="📤",
            color=Colors.ACCENT_PURPLE
        )
        self.stat_alerts.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=0)
        
        # === CONTROL SECTION ===
        self.create_section_header(control_container, "🎮 CONTROLS")
        
        controls_frame = ctk.CTkFrame(control_container, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 20))
        
        # ARM Button
        self.arm_button = ctk.CTkButton(
            controls_frame,
            text="🔴  ARM SYSTEM",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=55,
            fg_color=Colors.ACCENT_RED,
            hover_color="#D50000",
            border_width=0,
            corner_radius=12,
            command=self.arm_system
        )
        self.arm_button.pack(fill="x", pady=(0, 12))
        
        # DISARM Button
        self.disarm_button = ctk.CTkButton(
            controls_frame,
            text="🟢  DISARM",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=55,
            fg_color=Colors.BG_CARD_LIGHT,
            hover_color=Colors.BG_CARD,
            border_width=2,
            border_color=Colors.SUCCESS,
            text_color=Colors.SUCCESS,
            corner_radius=12,
            command=self.disarm_system
        )
        self.disarm_button.pack(fill="x")
        
        # === ACTIVITY LOG SECTION ===
        self.create_section_header(control_container, "📋 ACTIVITY LOG")
        
        log_frame = ctk.CTkFrame(control_container, fg_color=Colors.BG_CARD, corner_radius=10)
        log_frame.pack(fill="both", expand=True)
        
        # Log Box
        self.log_box = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=11, family="Consolas"),
            wrap="word",
            fg_color=Colors.BG_CARD_LIGHT,
            border_width=0,
            corner_radius=8
        )
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Initial Logs
        self.add_log("System initialized successfully", "info")
        self.add_log("Camera connected and streaming", "success")
        self.add_log("Face recognition module loaded", "success")
        if self.bot.loop and self.bot.loop.is_running():
            self.add_log("Telegram bot connected", "success")
        else:
            self.add_log("Telegram bot offline", "warning")
        
        # Auto-armed notification
        self.add_log("🚀 System Auto-Started & Armed - Active monitoring enabled", "warning")
    
    def create_section_header(self, parent, text):
        """Create a styled section header"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        header_frame.pack(fill="x", pady=(10, 15))
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w"
        ).pack(side="left", fill="x")
        
        # Separator line
        separator = ctk.CTkFrame(header_frame, fg_color=Colors.BG_CARD_LIGHT, height=2)
        separator.pack(side="bottom", fill="x", pady=(8, 0))
    
    def add_log(self, message, level="info"):
        """Add an entry to the activity log with enhanced formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "info": Colors.INFO,
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "critical": Colors.CRITICAL
        }
        
        icon_map = {
            "info": "ℹ️",
            "success": "✓",
            "warning": "⚠",
            "critical": "✖"
        }
        
        color = color_map.get(level, Colors.TEXT_SECONDARY)
        icon = icon_map.get(level, "•")
        
        self.log_box.configure(state="normal")
        
        # Timestamp
        self.log_box.insert("end", f"[{timestamp}] ", "timestamp")
        
        # Icon
        self.log_box.insert("end", f"{icon} ", level + "_icon")
        
        # Message
        self.log_box.insert("end", f"{message}\n", level)
        
        # Apply tags
        self.log_box.tag_config("timestamp", foreground=Colors.TEXT_MUTED)
        self.log_box.tag_config(level + "_icon", foreground=color)
        self.log_box.tag_config(level, foreground=color)
        
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
    
    def arm_system(self):
        """ARM the security system"""
        self.armed = True
        self.bot.is_armed = True
        self.armed_badge.update_status("ARMED", Colors.CRITICAL)
        self.add_log("System ARMED - Active threat monitoring enabled", "warning")
        logger.info("System Armed via GUI")
    
    def disarm_system(self):
        """DISARM the security system"""
        self.armed = False
        self.bot.is_armed = False
        self.armed_badge.update_status("STANDBY", Colors.TEXT_MUTED)
        self.add_log("System DISARMED - Passive surveillance mode", "info")
        logger.info("System Disarmed via GUI")
    
    def update_frame(self):
        """Main video update loop"""
        if not self.running:
            return
        
        # Update time
        self.time_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        
        frame = self.camera.read()
        
        if frame is not None:
            # Process frame
            processed_frame, detections, status = self.detector.detect_frame(frame, ROI_POINTS)
            
            # Handle detections
            self.handle_detections(detections, status, processed_frame)
            
            # Enhanced status overlay
            self.draw_enhanced_overlay(processed_frame)
            
            # Display frame
            self.display_frame(processed_frame)
        
        # Schedule next update
        self.after(10, self.update_frame)
    
    def draw_enhanced_overlay(self, frame):
        """Draw professional status overlay on video"""
        h, w = frame.shape[:2]
        
        # Semi-transparent status bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 60), (10, 14, 39), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # System status text
        status_text = "● ARMED" if self.armed else "○ STANDBY"
        status_color = (0, 230, 118) if self.armed else (144, 164, 174)
        
        cv2.putText(
            frame,
            status_text,
            (20, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            status_color,
            2,
            cv2.LINE_AA
        )
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            timestamp,
            (w - 250, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (176, 190, 197),
            1,
            cv2.LINE_AA
        )
    
    def handle_detections(self, detections, status, frame):
        """Process detections and update UI"""
        current_time = time.time()
        
        if len(detections) > 0:
            self.stats['total_detections'] += len(detections)
            self.stat_detections.update_value(self.stats['total_detections'])
        
        for det in detections:
            name = det.get("name", "Unknown")
            det_status = det.get("status", "")
            
            if name != "Unknown" and det_status == "AUTHORIZED":
                self.stats['authorized_count'] += 1
                self.stat_authorized.update_value(self.stats['authorized_count'])
                self.add_log(f"Authorized person detected: {name}", "success")
            elif det_status == "CRITICAL":
                self.stats['intruder_count'] += 1
                self.stat_intruders.update_value(self.stats['intruder_count'])
                self.add_log(f"INTRUDER ALERT - Unidentified person in restricted zone!", "critical")
        
        # Send Alert - Enhanced with Debug Logging
        if status == "CRITICAL":
            logger.debug(f"CRITICAL status detected! Armed={self.armed}")
            
            if self.armed:
                time_since_last = current_time - self.last_alert_time
                logger.debug(f"Time since last alert: {time_since_last:.1f}s (Cooldown: {ALERT_COOLDOWN}s)")
                
                if time_since_last > ALERT_COOLDOWN:
                    self.add_log("🚨 Sending Telegram alert with evidence photo...", "critical")
                    logger.warning("CRITICAL SECURITY BREACH DETECTED!")
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"alert_{timestamp}.jpg"
                    filepath = LOGS_DIR / filename
                    cv2.imwrite(str(filepath), frame)
                    logger.info(f"Evidence saved: {filepath}")
                    
                    msg = f"🚨 SECURITY BREACH 🚨\nTime: {timestamp}\nThreat Level: CRITICAL"
                    self.bot.send_alert(str(filepath), msg)
                    logger.info("Telegram alert sent successfully")
                    
                    self.stats['alerts_sent'] += 1
                    self.stat_alerts.update_value(self.stats['alerts_sent'])
                    
                    self.last_alert_time = current_time
                else:
                    remaining = ALERT_COOLDOWN - time_since_last
                    logger.debug(f"Alert on cooldown. Wait {remaining:.1f}s more")
            else:
                logger.debug("Alert NOT sent: System is DISARMED")
    
    def display_frame(self, frame):
        """Convert and display frame with professional styling"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        label_width = self.video_label.winfo_width()
        label_height = self.video_label.winfo_height()
        
        if label_width > 1 and label_height > 1:
            img_width, img_height = pil_image.size
            scale_w = label_width / img_width
            scale_h = label_height / img_height
            scale = min(scale_w, scale_h) * 0.98
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=(new_width, new_height)
            )
            
            self.video_label.configure(image=ctk_image)
            self.video_label.image = ctk_image
    
    def on_closing(self):
        """Clean shutdown"""
        logger.info("Shutting down FESS Professional Dashboard...")
        self.add_log("Initiating system shutdown...", "warning")
        
        self.running = False
        self.bot.running = False
        time.sleep(0.5)
        
        self.camera.release()
        logger.info("✅ Shutdown complete")
        self.destroy()


def main():
    """Entry point for FESS Professional Dashboard"""
    logger.info("=" * 70)
    logger.info("Starting Falcon Eye Security System - Professional Dashboard")
    logger.info("=" * 70)
    
    try:
        app = FESSApp()
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("User interrupted system")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        logger.info("FESS Terminated")


if __name__ == "__main__":
    main()
