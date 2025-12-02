# Project Proposal: Falcon Eye Security System (FESS)

## 1. Project Overview
**Falcon Eye Security System (FESS)** is an intelligent, automated surveillance solution designed to enhance premise security through real-time computer vision. Unlike traditional passive CCTV systems, FESS actively monitors a video feed to detect human presence, verifies identity using Face Recognition, and instantly notifies the owner via a Telegram Bot if an unauthorized intruder enters a restricted area.

The system is built to be modular, lightweight, and capable of running on edge devices (like Raspberry Pi) or standard PCs, making it an accessible smart security solution for homes and small businesses.

## 2. Key Features
*   **Human Detection:** Utilizes **YOLOv8** (You Only Look Once) for high-speed, accurate human detection.
*   **Smart Authentication:** Integrates **Face Recognition** to distinguish between "Authorized Personnel" (Green Box) and "Intruders" (Red Box).
*   **Region of Interest (ROI):** Allows users to define specific "Danger Zones" (e.g., behind a counter or near a safe) where detection triggers a critical alert.
*   **Real-Time Alerts:** Sends instant notifications with high-resolution snapshots to the user's **Telegram** account.
*   **Remote Control:** Users can Arm/Disarm the system remotely via Telegram commands.

## 3. Technologies Used
*   **Language:** Python 3.9+
*   **Computer Vision:** OpenCV, Ultralytics YOLOv8, Dlib (Face Recognition)
*   **Communication:** Python Telegram Bot (Async)
*   **Concurrency:** Threading & Asyncio for non-blocking performance

---

## 4. Task Distribution

### **Member 1: AI & Computer Vision Lead**
*   **Focus:** The "Brain" and "Eyes" of the system.
*   **Tasks:**
    *   **Object Detection:** Implement YOLOv8 inference and optimization (`detector.py`).
    *   **Face Recognition:** Develop the authentication logic and manage the "Known Faces" database (`face_auth.py`).
    *   **Logic Implementation:** Design the Region of Interest (ROI) algorithms to filter false alarms.
    *   **Data Management:** Collect and preprocess images for authorized personnel.

### **Member 2: System Architect & Integrator**
*   **Focus:** The "Voice" and "Body" of the system.
*   **Tasks:**
    *   **IoT Communication:** Develop the asynchronous Telegram Bot for real-time alerts and remote control (`notifier.py`).
    *   **System Orchestration:** Implement multi-threaded camera capture and the main event loop (`main.py`).
    *   **Infrastructure:** Handle environment setup, configuration management, and dependency resolution.
    *   **Testing & QA:** Perform integration testing, edge-case handling (e.g., network loss), and documentation.

---

## 5. Expected Outcome
A fully functional, standalone Python application that connects to a webcam, detects intruders in real-time, and successfully sends alerts to a mobile device with less than 2 seconds of latency.
