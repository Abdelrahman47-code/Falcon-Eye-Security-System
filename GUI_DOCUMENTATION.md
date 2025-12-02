# 🦅 FESS GUI Dashboard Documentation

## Overview
The new `main.py` provides a **professional, modern GUI** for the Falcon Eye Security System using **customtkinter** (Dark Theme).

---

## 🎨 Interface Layout

### **Left Column (70%): Video Feed**
- **Large display** showing live camera feed with real-time object detection
- **Overlays**:
  - ROI (Region of Interest) polygon in blue
  - Detected persons with bounding boxes (color-coded by status)
  - System status indicator (ARMED/DISARMED)
  - Person names for authorized individuals
  - Alert labels for intruders

### **Right Column (30%): Control Panel**

#### **1. Status Indicators**
- **🛡️ System Status**: 
  - Green "ARMED" when active monitoring is enabled
  - Red "DISARMED" when in passive surveillance mode
  
- **📱 Telegram Status**: 
  - Green "CONNECTED" if the bot is online
  - Red "DISCONNECTED" if the bot failed to initialize

#### **2. Control Buttons**
- **🔴 ARM SYSTEM** (Red Button):
  - Activates threat detection and alert notifications
  - When armed, critical alerts will trigger Telegram notifications
  
- **🟢 DISARM** (Green Button):
  - Deactivates alerting (surveillance continues)
  - Useful during maintenance or when expecting authorized visitors

#### **3. Live Log** (Scrollable Text Box)
- Real-time event logging with timestamps
- Color-coded entries:
  - **Green**: Authorized person detected ("Welcome, [Name]")
  - **Orange**: Warnings and system status changes
  - **Red**: CRITICAL alerts ("INTRUDER detected!")
  - **Gray**: General info messages

---

## 🔧 Technical Implementation

### **Key Features**

✅ **Non-Blocking UI**:
- Uses `.after(10, self.update_frame)` to read frames every 10ms
- No `while True` loop that would freeze the GUI
- Smooth, responsive interface even during heavy processing

✅ **Proper Threading**:
- Camera runs in a separate thread (`ThreadedCamera`)
- Telegram Bot runs in its own thread with asyncio event loop
- GUI updates happen on the main thread (thread-safe)

✅ **Efficient Frame Processing**:
1. Camera thread captures frames → Queue
2. Main GUI thread retrieves frame from queue
3. Frame is processed by `ObjectDetector`
4. Results are rendered and displayed
5. OpenCV BGR → RGB → PIL Image → CTkImage conversion for display

✅ **State Management**:
- `self.armed` controls alert behavior
- `self.bot.is_armed` syncs with Telegram bot
- `self.last_alert_time` enforces cooldown (prevents spam)

---

## 🎯 Integration with Existing Modules

### **1. ObjectDetector (`src/detector.py`)**
```python
processed_frame, detections, status = self.detector.detect_frame(frame, ROI_POINTS)
```
- Returns annotated frame with bounding boxes
- Provides list of detections with `name`, `status`, `bbox`, `conf`
- Overall status: `"SAFE"`, `"WARNING"`, or `"CRITICAL"`

### **2. TelegramBot (`src/notifier.py`)**
```python
self.bot = TelegramBot()
self.bot.start()  # Starts in background thread
```
- Bot runs independently, polling for commands
- `/arm` and `/disarm` commands sync with GUI state
- `send_alert()` is thread-safe via `asyncio.run_coroutine_threadsafe()`

### **3. FaceAuthenticator (`src/face_auth.py`)**
- Automatically used by `ObjectDetector`
- Known faces from `known_faces/` directory
- Names appear in GUI log when recognized

### **4. Config (`src/config.py`)**
- Uses `CAMERA_INDEX`, `ROI_POINTS`, `ALERT_COOLDOWN`
- Loads `.env` for Telegram credentials
- Logger outputs to terminal and `logs/fess.log`

---

## 📝 Event Flow Example

### Scenario: Intruder Enters ROI

1. **Camera captures frame** → ThreadedCamera queue
2. **GUI retrieves frame** via `update_frame()`
3. **Detector processes**:
   - YOLO detects person
   - Face recognition runs → "Unknown"
   - Person is inside ROI → Status = `CRITICAL`
4. **GUI handles detection**:
   - Logs: `"⚠️ INTRUDER detected!"` (red text)
   - If armed and cooldown expired:
     - Saves screenshot to `logs/alert_YYYYMMDD_HHMMSS.jpg`
     - Sends Telegram alert with photo
     - Logs: `"🚨 CRITICAL ALERT! Sending notification..."`
5. **Video displays**:
   - Red bounding box around person
   - "CRITICAL" label
   - System status overlay

---

## 🚀 How to Run

### **Prerequisites**
```bash
pip install -r requirements.txt
```

### **Ensure .env is configured**
```env
TELEGRAM_TOKEN=your_bot_token
CHAT_ID=your_chat_id
CAMERA_INDEX=0  # Or path to video file
```

### **Add Known Faces** (Optional)
- Place photos in `known_faces/` folder
- Format: `Name.jpg` (e.g., `John.jpg`, `Alice.png`)

### **Launch the GUI**
```bash
python main.py
```

---

## 🎨 GUI Customization

### **Change Theme Colors**
Edit the button colors in `build_ui()`:

```python
# ARM Button (currently red)
fg_color="#cc0000",  # Change to desired hex color
hover_color="#990000"

# DISARM Button (currently green)
fg_color="#00aa00",
hover_color="#008800"
```

### **Adjust Layout Proportions**
Modify the grid column weights in `build_ui()`:

```python
self.grid_columnconfigure(0, weight=7)  # Video (70%)
self.grid_columnconfigure(1, weight=3)  # Controls (30%)

# For 60/40 split:
# self.grid_columnconfigure(0, weight=6)
# self.grid_columnconfigure(1, weight=4)
```

### **Change Update Rate**
Adjust the frame update interval in `update_frame()`:

```python
self.after(10, self.update_frame)  # 10ms (~100 FPS max)
# For slower updates:
# self.after(33, self.update_frame)  # ~30 FPS
```

---

## 🐛 Troubleshooting

### **Camera Not Found**
- Check `CAMERA_INDEX` in `.env`
- Try different indices: `0`, `1`, `2`
- Or use video file path: `CAMERA_INDEX=videos/test.mp4`

### **Telegram Bot Not Connecting**
- Verify `TELEGRAM_TOKEN` is correct
- Check internet connection
- Look for errors in `logs/fess.log`

### **Face Recognition Not Working**
- Ensure `dlib` and `face_recognition` are installed
- Check `known_faces/` directory contains images
- Verify images are `.jpg`, `.jpeg`, or `.png` format

### **Video Display Issues**
- If video appears stretched, the auto-scaling will adjust after first render
- For manual control, edit the `scale` calculation in `display_frame()`

### **High CPU Usage**
- Reduce frame rate by increasing `self.after()` delay
- Decrease YOLO input size in `detector.py`
- Use a smaller YOLO model (e.g., `yolov8n.pt` instead of `yolov8m.pt`)

---

## 🔐 Security Best Practices

1. **Never commit `.env`** to version control
2. **Restrict Telegram bot** to specific chat IDs only
3. **Secure the `known_faces/`** directory (contains biometric data)
4. **Review logs regularly** in `logs/` folder
5. **Test the system** thoroughly before deploying to production

---

## 📚 Code Structure

```
main.py
├── Imports (cv2, customtkinter, PIL, etc.)
├── ThreadedCamera (Background frame capture)
└── FESSApp (Main GUI Application)
    ├── __init__() - Initialize components
    ├── build_ui() - Construct interface
    ├── add_log() - Append to live log
    ├── arm_system() - Enable alerts
    ├── disarm_system() - Disable alerts
    ├── update_frame() - Main video loop (non-blocking)
    ├── handle_detections() - Process alerts
    ├── display_frame() - Render video to GUI
    └── on_closing() - Clean shutdown
```

---

## 🎓 Advanced Features

### **Add Custom Buttons**
In `build_ui()`, after the DISARM button:

```python
custom_button = ctk.CTkButton(
    buttons_section,
    text="Custom Action",
    command=self.custom_action
)
custom_button.pack(fill="x", pady=5)
```

Then define the handler:
```python
def custom_action(self):
    self.add_log("Custom action triggered", "info")
    # Your logic here
```

### **Add Statistics Display**
Create a label to show detection count:

```python
# In build_ui()
self.detection_count = 0
self.stats_label = ctk.CTkLabel(
    status_section,
    text="Detections: 0",
    font=ctk.CTkFont(size=12)
)
self.stats_label.pack()

# In handle_detections()
self.detection_count += len(detections)
self.stats_label.configure(text=f"Detections: {self.detection_count}")
```

---

## 📞 Support

For issues or questions:
1. Check `logs/fess.log` for detailed error messages
2. Review the PROJECT_PROPOSAL.md for system architecture
3. Ensure all dependencies match `requirements.txt`

---

**Created by:** Senior Python Frontend Engineer  
**Framework:** customtkinter 5.2.2  
**Python:** 3.10+  
**License:** As per project requirements
