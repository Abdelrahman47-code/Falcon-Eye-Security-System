# 🦅 FESS Quick Start Guide

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your Telegram credentials

# 3. Add known faces (optional)
# Place photos in known_faces/ folder
# Name format: John.jpg, Sarah.png, etc.

# 4. Run the GUI
python main.py
```

---

## GUI Overview

### **Layout**
```
┌─────────────────────────────────┬──────────────────┐
│                                 │  ⚙️ Control Panel │
│    📹 Live Video Feed           │                  │
│                                 │  🛡️ Status       │
│                                 │  ARMED ✓         │
│   [Camera View with ROI]        │                  │
│   [Detection Overlays]          │  📱 Telegram     │
│   [System Status]               │  CONNECTED ✓     │
│                                 │                  │
│                                 │  🔴 ARM SYSTEM   │
│                                 │  🟢 DISARM       │
│                                 │                  │
│                                 │  📋 Live Log     │
│                                 │  ┌────────────┐  │
│                                 │  │[19:30:15]  │  │
│                                 │  │System init │  │
│                                 │  │            │  │
│                                 │  └────────────┘  │
└─────────────────────────────────┴──────────────────┘
```

---

## Key Features

### ✅ **ARM System** (Red Button)
- **Action**: Enables threat detection and alert notifications
- **Result**: Status shows "ARMED" in green
- **Log**: "🛡️ System ARMED - Monitoring for threats"
- **Behavior**: Intruders in ROI trigger Telegram alerts

### ✅ **DISARM** (Green Button)
- **Action**: Disables alerting (monitoring continues)
- **Result**: Status shows "DISARMED" in red
- **Log**: "🔓 System DISARMED - Surveillance only"
- **Behavior**: No alerts sent, but detection still runs

### ✅ **Live Video Feed**
- Shows real-time camera with detection overlays:
  - **Blue polygon**: Region of Interest (ROI)
  - **Green boxes**: Authorized persons
  - **Red boxes**: Intruders
  - **Yellow boxes**: Persons outside ROI
  - **Labels**: Person names and status

### ✅ **Live Log**
- Scrollable event log with color coding:
  - **Green**: Authorized detection ("✅ Welcome, John")
  - **Red**: Intruder alerts ("⚠️ INTRUDER detected!")
  - **Orange**: System status changes
  - **Gray**: General info

---

## Detection Logic

### **When a Person is Detected:**

1. **Outside ROI**:
   - Status: WARNING (Yellow box)
   - Log: No entry
   - Alert: None

2. **Inside ROI + Known Face**:
   - Status: AUTHORIZED (Green box)
   - Log: "✅ Welcome, [Name]"
   - Alert: None

3. **Inside ROI + Unknown Face**:
   - Status: CRITICAL (Red box)
   - Log: "⚠️ INTRUDER detected!"
   - Alert: If armed, sends Telegram notification with photo

---

## Telegram Bot Commands

Send these commands to your bot via Telegram:

- `/start` - Show available commands
- `/arm` - ARM the system remotely
- `/disarm` - DISARM the system remotely

**Note**: Commands instantly sync with the GUI!

---

## Workflow Example

### Scenario: Authorized Person Arrives

```
[User walks into camera view]
  ↓
[Detector: Person detected outside ROI]
  ↓
GUI: Yellow box, no log entry
  ↓
[Person walks into ROI (blue zone)]
  ↓
[Face Recognition: Match found → "John"]
  ↓
GUI Log: "✅ Welcome, John" (green)
GUI Video: Green box with "AUTHORIZED (John)"
  ↓
No alert sent (authorized)
```

### Scenario: Intruder Detected (System Armed)

```
[Unknown person walks into ROI]
  ↓
[Face Recognition: No match → "Unknown"]
  ↓
GUI Log: "⚠️ INTRUDER detected!" (red)
GUI Video: Red box with "CRITICAL"
  ↓
System Armed? YES
  ↓
Cooldown expired? YES
  ↓
Action:
  1. Save screenshot → logs/alert_20251202_193045.jpg
  2. Send Telegram alert with photo
  3. GUI Log: "🚨 CRITICAL ALERT! Sending notification..."
  4. Update last_alert_time
```

---

## Customization

### Change ROI (Region of Interest)

Edit `src/config.py`:

```python
ROI_POINTS = [
    (0.3, 0.3),  # Top-Left (x, y as 0-1 normalized)
    (0.7, 0.3),  # Top-Right
    (0.7, 0.7),  # Bottom-Right
    (0.3, 0.7)   # Bottom-Left
]
```

### Adjust Alert Cooldown

Edit `src/config.py`:

```python
ALERT_COOLDOWN = 30  # Seconds between alerts
```

### Use Video File Instead of Camera

Edit `.env`:

```env
CAMERA_INDEX=videos/test.mp4
```

---

## Shortcuts & Tips

### **Keyboard Shortcuts**
- Currently none implemented, but you can add them!

### **Pro Tips**
1. **Test with sample video**: Use `CAMERA_INDEX=videos/test.mp4` before deploying to real camera
2. **Monitor logs**: Check `logs/fess.log` for detailed debugging
3. **Known faces**: Use clear, front-facing photos for best recognition
4. **Performance**: If laggy, reduce frame rate in `update_frame()` (change `10` to `33` for 30fps)

---

## Troubleshooting

### Problem: "Camera not found"
**Solution**: 
- Check `CAMERA_INDEX` in `.env`
- Try `0`, `1`, or `2`
- For USB cameras, unplug and replug

### Problem: "Telegram not connecting"
**Solution**:
- Verify `TELEGRAM_TOKEN` is correct
- Check internet connection
- Review `logs/fess.log` for errors

### Problem: "Face recognition always returns Unknown"
**Solution**:
- Ensure photos in `known_faces/` are clear and front-facing
- Check that `face_recognition` library is installed
- Lower the tolerance in `face_auth.py` (line 89): `tolerance=0.5` → `tolerance=0.6`

### Problem: "GUI is laggy"
**Solution**:
- Reduce frame rate: `self.after(10, ...)` → `self.after(33, ...)`
- Use smaller YOLO model
- Close other applications

---

## File Locations

| Item | Path |
|------|------|
| Main GUI | `main.py` |
| Configuration | `src/config.py` |
| Environment | `.env` |
| Known Faces | `known_faces/*.jpg` |
| Alert Screenshots | `logs/alert_*.jpg` |
| System Logs | `logs/fess.log` |

---

## Next Steps

1. ✅ **Test the System**:
   ```bash
   python main.py
   ```

2. ✅ **Add Your Face**:
   - Take a clear photo
   - Save as `known_faces/YourName.jpg`
   - Restart application

3. ✅ **Configure Alerts**:
   - Set up Telegram bot with BotFather
   - Add token and chat ID to `.env`

4. ✅ **Deploy**:
   - Connect to security camera
   - Update `CAMERA_INDEX`
   - Run in production mode

---

**Need Help?** Check `GUI_DOCUMENTATION.md` for detailed technical information.

**Enjoy your Falcon Eye Security System! 🦅**
