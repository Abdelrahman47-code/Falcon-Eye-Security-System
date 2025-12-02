# 🤖 Automatic Telegram Alert Testing Guide

## 📋 Prerequisites Checklist

Before testing, verify these are all ✅:

### 1. Telegram Bot Setup
- [ ] Bot created with @BotFather
- [ ] Token in `.env` file: `TELEGRAM_TOKEN=8234281667:AAFWJ5_5bv96zOdWstUa4NrE25vy3xdrAMc`
- [ ] Chat ID in `.env` file: `CHAT_ID=869824962`
- [ ] Started conversation with your bot (send /start to it)

### 2. System Status
- [ ] Application running (`.venv\Scripts\python.exe main.py`)
- [ ] Video feed showing
- [ ] Telegram Status shows "ONLINE" (green)
- [ ] Camera working properly

---

## 🎯 **How to Get Automatic Alerts**

### **Step 1: ARM the System** 🔴

**In the GUI:**
1. Click the large red button: **🔴 ARM SYSTEM**
2. Watch the status badge change:
   - Before: "STANDBY" (gray)
   - After: **"ARMED"** (red)
3. Check the Activity Log for: "System ARMED - Active threat monitoring enabled"

**OR via Telegram:**
- Send `/arm` to your bot
- Bot replies: "✅ System ARMED. Monitoring for intruders."

---

### **Step 2: Trigger an Intruder Detection** 👤

You need to create a **CRITICAL** status:
- **Detected person** = Any human
- **Inside ROI** = Within the blue polygon zone
- **Unknown face** = Not in `known_faces/` folder

**Option A: Test with Yourself**
If your face is NOT in `known_faces/`:
1. Stand in front of camera
2. Move into the **blue ROI zone**
3. Wait 2-3 seconds
4. **BOOM!** 💥 Alert sent!

**Option B: Remove Your Face Temporarily**
If your face IS in `known_faces/`:
1. Move your photo out: `known_faces/YourName.jpg` → `YourName_backup.jpg`
2. Restart the app (so it reloads known faces)
3. Now you'll be detected as "Unknown"
4. Walk into ROI and get the alert!

**Option C: Ask Someone Else**
- Get a friend/family member whose face is NOT registered
- Have them walk into the blue zone
- Alert triggered!

---

### **Step 3: Check for the Alert** 📱

**What happens automatically:**

1. **In the GUI Activity Log:**
   ```
   [19:50:23] ⚠ INTRUDER ALERT - Unidentified person in restricted zone!
   [19:50:23] ✖ 🚨 Sending Telegram alert with evidence photo...
   ```

2. **In the Statistics Panel:**
   - "Intruders" counter increases
   - "Alerts Sent" counter increases

3. **In Telegram:**
   - You receive a message from your bot:
   ```
   🚨 SECURITY BREACH 🚨
   Time: 20251202_195023
   Threat Level: CRITICAL
   ```
   - With an attached photo showing the detection

4. **In the Terminal/Logs:**
   ```
   CRITICAL status detected! Armed=True
   Time since last alert: 45.3s (Cooldown: 30s)
   CRITICAL SECURITY BREACH DETECTED!
   Evidence saved: logs/alert_20251202_195023.jpg
   Telegram alert sent successfully
   ```

---

## 🐛 **Troubleshooting**

### **Problem: Alert Not Sending**

#### Check 1: Is System Armed?
**Look for in Terminal:**
```
CRITICAL status detected! Armed=False
Alert NOT sent: System is DISARMED
```
**Solution:** Click the ARM button!

---

#### Check 2: Is Person in ROI?
**Look for in Activity Log:**
- If you see "Total Detections" increasing but no "Intruder" count
- Person is detected but OUTSIDE the blue zone

**Solution:** Move closer to the center of the blue polygon

---

#### Check 3: Is Face Recognized?
**Look for in Activity Log:**
```
✓ Authorized person detected: YourName
```
**If you see this:** Your face is recognized, so NO alert (by design!)

**Solution:** 
- Temporarily rename your photo: `known_faces/YourName.jpg` → `YourName_backup.jpg`
- Restart app
- Test again

---

#### Check 4: Cooldown Timer
**Look for in Terminal:**
```
Alert on cooldown. Wait 15.3s more
```
**Explanation:** System waits 30 seconds between alerts (prevents spam)

**Solution:** Wait for cooldown to expire, then try again

---

#### Check 5: Telegram Bot Offline
**Look at GUI Status Badge:**
- If "Telegram Bot" shows "OFFLINE" (red)

**Solution:**
1. Check internet connection
2. Verify `.env` has correct `TELEGRAM_TOKEN`
3. Check `logs/fess.log` for connection errors
4. Restart the application

---

## 🧪 **Quick Test Procedure**

### **5-Minute Test:**

```bash
# 1. Start the app
.venv\Scripts\python.exe main.py

# 2. In GUI: Click ARM button
# Status should show "ARMED" in red

# 3. Remove your known face (if exists)
# Rename: known_faces/YourName.jpg → YourName_backup.jpg

# 4. Restart app to reload faces
# Close window, run again

# 5. Stand in front of camera in ROI zone
# Wait 3 seconds

# 6. Check Telegram on your phone
# Should receive alert with photo!
```

---

## 📊 **Understanding the Logic**

### **Alert Trigger Conditions (ALL must be true):**
```python
✅ status == "CRITICAL"           # Unknown person in ROI
✅ self.armed == True             # System is armed
✅ time_since_last > 30s          # Cooldown expired
✅ bot.is_running == True         # Telegram connected
```

### **Why "CRITICAL" Status:**
```python
Person detected:
  ├─ Outside ROI → "WARNING" (Yellow box, no alert)
  │
  └─ Inside ROI:
      ├─ Known face → "AUTHORIZED" (Green box, no alert)
      │
      └─ Unknown face → "CRITICAL" (Red box, ALERT!)
```

---

## 🎯 **Expected Behavior**

### **Scenario 1: Known Person (You)**
```
1. Face recognized: "John"
2. Status: AUTHORIZED
3. GUI Log: "✓ Authorized person detected: John"
4. Alert: ❌ NO ALERT (you're authorized!)
```

### **Scenario 2: Unknown Person (Intruder)**
```
1. Face NOT recognized: "Unknown"
2. Status: CRITICAL
3. GUI Log: "⚠ INTRUDER ALERT"
4. Alert: ✅ TELEGRAM MESSAGE SENT!
5. Photo saved: logs/alert_YYYYMMDD_HHMMSS.jpg
```

---

## 🔧 **Advanced Settings**

### **Change Alert Cooldown**

Edit `src/config.py`:
```python
ALERT_COOLDOWN = 30  # Default: 30 seconds

# For faster testing:
ALERT_COOLDOWN = 5   # 5 seconds (sends more frequently)

# For production:
ALERT_COOLDOWN = 60  # 1 minute (reduce spam)
```

### **Adjust ROI Size**

Edit `src/config.py`:
```python
ROI_POINTS = [
    (0.2, 0.2),  # Top-Left (x, y as 0-1 normalized)
    (0.8, 0.2),  # Top-Right
    (0.8, 0.8),  # Bottom-Right
    (0.2, 0.8)   # Bottom-Left
]

# Make ROI smaller (center only):
ROI_POINTS = [
    (0.3, 0.3),
    (0.7, 0.3),
    (0.7, 0.7),
    (0.3, 0.7)
]

# Make ROI larger (almost full screen):
ROI_POINTS = [
    (0.1, 0.1),
    (0.9, 0.1),
    (0.9, 0.9),
    (0.1, 0.9)
]
```

---

## 📱 **Telegram Bot Commands**

Your bot supports these commands:

| Command | Action |
|---------|--------|
| `/start` | Show welcome message |
| `/arm` | ARM system remotely |
| `/disarm` | DISARM system remotely |

**Note:** ARM/DISARM commands sync with the GUI!

---

## 🎓 **Pro Tips**

1. **Test First:** Always test with `ALERT_COOLDOWN = 5` to avoid waiting
2. **Check Logs:** Terminal shows WHY alerts don't send
3. **Monitor Stats:** Watch the "Alerts Sent" counter in GUI
4. **Evidence Photos:** All alerts save to `logs/alert_*.jpg`
5. **Bot Status:** If Telegram shows "OFFLINE", restart the app

---

## ✅ **Success Indicators**

You'll know it's working when:
- ✅ GUI shows "ARMED" in red
- ✅ Activity Log shows "INTRUDER ALERT"
- ✅ Activity Log shows "Sending Telegram alert..."
- ✅ Statistics "Alerts Sent" increases
- ✅ Terminal shows "Telegram alert sent successfully"
- ✅ **Your phone receives a Telegram message with photo!**

---

**Need more help?** Check `logs/fess.log` for detailed error messages.

**System working perfectly?** Restore your face: `YourName_backup.jpg` → `known_faces/YourName.jpg`
