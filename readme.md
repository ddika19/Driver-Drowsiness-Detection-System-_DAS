# Driver Drowsiness Detection with IoT & MQTT Integration 🚗😴

An intelligent driver safety system that detects driver drowsiness in real time using computer vision and IoT integration. The system uses a laptop webcam to monitor eye activity and identifies drowsiness using the **Eye Aspect Ratio (EAR)** method. When prolonged eye closure is detected, a signal is sent using **MQTT protocol** to a **NodeMCU (ESP8266)**, which activates a buzzer to alert the driver.

---

## Features ✨

- 👁️ Real-time eye tracking using facial landmarks  
- 😴 Driver drowsiness detection using Eye Aspect Ratio (EAR)  
- 🎥 Live webcam monitoring using laptop camera  
- 📡 MQTT-based IoT communication  
- 🚨 Physical buzzer alert using NodeMCU (ESP8266)  
- ⚡ Real-time alert system for sleepy drivers  

---

## Tech Stack 🛠️

### Software
- Python
- OpenCV
- Dlib
- NumPy
- SciPy
- Imutils
- MQTT (Paho MQTT)
- Arduino IDE

### Hardware
- NodeMCU (ESP8266)
- Buzzer
- Jumper Wires
- USB Cable
- Laptop Webcam

---

## Project Workflow ⚙️

```text
Laptop Camera
      ↓
Face Detection
      ↓
Eye Landmark Detection
      ↓
EAR Calculation
      ↓
Drowsiness Detection
      ↓
Python Sends MQTT Alert
      ↓
MQTT Broker
      ↓
NodeMCU Receives Signal
      ↓
Buzzer Alert
```

---

## Eye Aspect Ratio (EAR)

The system detects drowsiness using Eye Aspect Ratio (EAR).

When the EAR value remains below a threshold for a certain number of frames, the system identifies the driver as drowsy.

Formula:

EAR = (||p2 - p6|| + ||p3 - p5||) / (2 × ||p1 - p4||)

---

## Hardware Requirements 🔧

### Components Required

| Component | Purpose |
|------------|---------|
| NodeMCU (ESP8266) | IoT communication and buzzer control |
| Laptop Webcam | Real-time driver monitoring |
| Buzzer | Driver alert system |
| Jumper Wires | Circuit connections |
| USB Cable | Power and programming NodeMCU |
| Laptop/PC | Runs drowsiness detection model |

---

## Hardware Connections 🔌

### NodeMCU Pin Connections

| Component | NodeMCU Pin |
|-----------|--------------|
| Buzzer (+) | D5 (GPIO14) |
| Buzzer (-) | GND |

### Wiring Diagram

```text
        NodeMCU (ESP8266)
        ┌──────────────┐
        │              │
D5 ------> (+) Buzzer  │
GND -----> (-) Buzzer  │
        │              │
        └──────────────┘
```
![alt text](image.png)
---

## Project Structure 📂

```text
Driver-Drowsiness-Detection/
│── drowsiness_detection.py
│── nodemcu_mqtt_buzzer.ino
│── alarm.wav
│── requirements.txt
│── README.md
│── .gitignore
```

---

## Installation & Setup 🚀

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Driver-Drowsiness-Detection.git
cd Driver-Drowsiness-Detection
```

---

### 2. Install Dependencies

Install required libraries:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install opencv-python dlib imutils scipy playsound requests numpy paho-mqtt
```

---

### 3. Download Required Dlib Model

Download the facial landmark model file:

:contentReference[oaicite:0]{index=0}

After downloading:

1. Extract the `.bz2` file  
2. Place:

```text
shape_predictor_68_face_landmarks.dat
```

inside the project folder.

Expected structure:

```text
Driver-Drowsiness-Detection/
│── drowsiness_detection.py
│── shape_predictor_68_face_landmarks.dat
│── nodemcu_mqtt_buzzer.ino
```

---

# MQTT Setup 📡

## What is MQTT?

MQTT (Message Queuing Telemetry Transport) is a lightweight messaging protocol used for IoT communication.

In this project:

```text
Python Detection System
        ↓
    MQTT Broker
        ↓
NodeMCU (ESP8266)
        ↓
      Buzzer
```

- Python publishes drowsiness alerts  
- NodeMCU subscribes to messages  
- MQTT broker acts as communication bridge

---

## Install MQTT Broker (Mosquitto)

Download:

:contentReference[oaicite:1]{index=1}

Install and start broker:

```bash
mosquitto
```

Default configuration:

```text
Broker Address: localhost
Port: 1883
```

---

## Install MQTT Library for Python

```bash
pip install paho-mqtt
```

---

## Install MQTT Library for NodeMCU

Open Arduino IDE:

```text
Sketch → Include Library → Manage Libraries
```

Search:

```text
PubSubClient
```

Install:

PubSubClient

---

## MQTT Topic Used

```text
driver/drowsiness
```

---

## Finding Your Laptop IP Address

Open Command Prompt:

```bash
ipconfig
```

Find:

```text
IPv4 Address
```

Example:

```text
192.168.1.100
```

This becomes your MQTT broker IP inside NodeMCU code.

---

## NodeMCU Setup 🌐

1. Open:

```text
nodemcu_mqtt_buzzer.ino
```

2. Add WiFi credentials:

```cpp
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
```

3. Add MQTT broker IP:

```cpp
const char* mqtt_server = "192.168.1.100";
```

Replace with your laptop IP.

4. Upload code to NodeMCU.

5. Open Serial Monitor (`115200 baud`) to confirm connection.

Expected:

```text
Connected to WiFi
Connected to MQTT Broker
Subscribed to topic: driver/drowsiness
```

---

## Running the Project ▶️

### Start MQTT Broker

```bash
mosquitto
```

---

### Run Detection System

```bash
python drowsiness_detection.py
```

---

## System Working ⚡

```text
Eyes Closed
      ↓
EAR Threshold Triggered
      ↓
Python Publishes MQTT Message
      ↓
NodeMCU Receives Signal
      ↓
Buzzer ON 🚨
```

---

## Testing MQTT Communication 🧪

You can test MQTT manually using MQTTX.

Download:

:contentReference[oaicite:2]{index=2}

Send message:

Topic:

```text
driver/drowsiness
```

Message:

```text
sleepy
```

Expected:

```text
NodeMCU buzzer activates
```

---

## Software Requirements 💻

Required Python Libraries:

```bash
opencv-python
dlib
imutils
scipy
playsound
numpy
requests
paho-mqtt
```

Generate requirements file:

```bash
pip freeze > requirements.txt
```

---

## Troubleshooting ⚠️

### NodeMCU not receiving messages

Check:

- Same WiFi network  
- Correct MQTT broker IP  
- Broker running on port `1883`  
- Correct topic name  

---

### MQTT Connection Error

Restart Mosquitto:

```bash
mosquitto
```

---

### Camera Not Working

Check:

- Webcam permissions enabled  
- Camera index (`cv2.VideoCapture(0)`)

---

### Dlib Model Error

Ensure:

```text
shape_predictor_68_face_landmarks.dat
```

exists in project folder.

---

## Future Improvements 🚀

- 😮 Yawn detection  
- 📱 Mobile notifications  
- 🌙 Night vision support  
- ☁️ Cloud analytics dashboard  
- 🧭 Head pose estimation  
- 📍 GPS integration  

---

## Author 👩‍💻

Made by **Deeksha Singh**