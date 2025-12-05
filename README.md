# 🦅 Falcon Eye Security System (FESS)

**Professional AI-Powered Surveillance & Intruder Detection System**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-green)
![OpenCV](https://img.shields.io/badge/Vision-OpenCV-red)
![Telegram](https://img.shields.io/badge/Alerts-Telegram-blue)

## 📋 Overview

**Falcon Eye Security System (FESS)** is an advanced, real-time security application that transforms a standard webcam into an intelligent guardian. Unlike passive CCTV, FESS actively monitors your environment using Computer Vision to detect threats and notify you instantly.

It combines **YOLOv8** for human detection, **Face Recognition** for authentication, and **Telegram** for instant mobile alerts.

---

## ✨ Key Features

*   **👁️ Real-Time Detection**: Instantly detects humans using state-of-the-art YOLOv8 AI.
*   **🤖 Smart Authentication**: Distinguishes between "Authorized Personnel" (Green) and "Intruders" (Red) using Face Recognition.
*   **📱 Instant Alerts**: Sends a photo of the intruder to your phone via Telegram within seconds.
*   **🖥️ Professional Dashboard**: A modern, dark-themed GUI to monitor the live feed, view logs, and control the system.
*   **📸 Evidence Gallery**: Built-in gallery to view and manage snapshots of detected intruders.
*   **🎥 Video Recording**: Automatically records video clips of security breaches for evidence.
*   **🚨 Sound Alarm**: Triggers a siren sound when an intruder is detected (Toggleable).
*   **🎛️ Live Controls**: Adjust sensitivity and alert cooldowns in real-time.

---

## 🚀 Installation

### Prerequisites
*   Python 3.10 or higher
*   A webcam (or video file)
*   (Optional) C++ Build Tools (for Face Recognition support)

### Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/FESS.git
    cd FESS
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    > **Note**: If `dlib` fails to install, ensure you have Visual Studio C++ Build Tools installed, or run the app in "Object Detection Only" mode.

4.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    TELEGRAM_TOKEN=your_telegram_bot_token
    CHAT_ID=your_telegram_chat_id
    CAMERA_INDEX=0
    ```

---

## 🎮 Usage

### Running the App
Simply double-click **`run.bat`** or run:
```bash
python main.py
```

### Dashboard Controls
*   **🔴 ARM SYSTEM**: Activates threat detection and alerts.
*   **🟢 DISARM**: Pauses alerts (passive monitoring only).
*   **🚪 EXIT APP**: Safely shuts down the system and releases the camera.
*   **Gallery Tab**: View photos of past alerts.
*   **Settings Tab**: Toggle sound alarm and adjust AI sensitivity.

### Adding Known Faces
To authorize a person (so they don't trigger an alarm):
1.  Add their photo to the `known_faces/` folder.
2.  Name the file `Name.jpg` (e.g., `John.jpg`).
3.  Restart the app.

---

## 📂 Project Structure

```
FESS/
├── known_faces/       # Store photos of authorized people here
├── logs/              # Alert snapshots, videos, and log files
├── models/            # YOLOv8 model weights
├── src/
│   ├── config.py      # Configuration settings
│   ├── detector.py    # AI Object Detection & Tracking logic
│   ├── face_auth.py   # Face Recognition logic
│   └── notifier.py    # Telegram Bot integration
├── main.py            # Main GUI Application entry point
├── requirements.txt   # Python dependencies
└── README.md          # Project Documentation

---

## 🧠 Model Information

This project uses the **YOLOv8 Nano (`yolov8n.pt`)** model by default, which is optimized for speed and real-time inference on standard CPUs.

### 📥 Download Model
The model file is included in this repository. However, if you need to download it manually or want to try larger, more accurate models (at the cost of speed), you can get them here:

*   **[YOLOv8n (Nano)](https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt)** - Fastest, recommended for laptops.
*   **[YOLOv8s (Small)](https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt)** - Better accuracy, slower.
*   **[YOLOv8m (Medium)](https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt)** - High accuracy, requires GPU.

**Note**: The application will automatically download `yolov8n.pt` on the first run if it is missing.
```

---

## 🛠️ Troubleshooting

*   **"Face Recognition library not installed"**: This means `dlib` is missing. The app will still work but will treat everyone as "Unknown".
*   **Telegram Bot Offline**: Check your internet connection and ensure `TELEGRAM_TOKEN` is correct in `.env`.
*   **Camera Error**: Try changing `CAMERA_INDEX` to `1` or `2` in `.env`.

---

## 📜 License

This project is for educational purposes.
