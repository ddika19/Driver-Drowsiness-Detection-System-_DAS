import cv2
import dlib
from imutils import face_utils
from scipy.spatial import distance as dist
import paho.mqtt.client as mqtt
import numpy as np
import time
import json

# CONFIGURATION CONSTANTS (easy to tune)
MQTT_BROKER    = "your_ip _ address"
MQTT_PORT      = 1883
CAMERA_INDEX   = 0
EAR_THRESHOLD  = 0.25
CONSEC_FRAMES  = 20
MAR_THRESHOLD  = 0.6
YAWN_FRAMES    = 15

class MQTTManager:
    def __init__(self):
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except AttributeError:
            self.client = mqtt.Client()
        
    def connect(self, broker_ip, port):
        try:
            self.client.connect(broker_ip, port, 60)
            self.client.loop_start()
            print(f"[INFO] Connected to MQTT Broker: {broker_ip}:{port}")
        except Exception as e:
            print(f"[ERROR] Could not connect to MQTT Broker: {e}")

    def send_alert(self, level, ear, mar, frame_count):
        buzzer_hz = 0
        buzzer_ms = 0
        
        if level == 1:
            buzzer_hz, buzzer_ms = 1000, 200
        elif level == 2:
            buzzer_hz, buzzer_ms = 2500, 800
        elif level == 3:
            buzzer_hz, buzzer_ms = 800, 300
            
        alert_payload = {
            "alert": True, "level": level, "buzzer_hz": buzzer_hz,
            "buzzer_ms": buzzer_ms, "timestamp": time.time()
        }
        
        data_payload = {
            "ear": round(ear, 3) if ear is not None else 0.0,
            "mar": round(mar, 3) if mar is not None else 0.0,
            "alert_level": level, "consec_frames": frame_count,
            "status": self._get_status_string(level), "timestamp": time.time()
        }
        
        self.client.publish("driver/drowsy/alert", json.dumps(alert_payload))
        self.client.publish("driver/drowsy/data", json.dumps(data_payload))

    def _get_status_string(self, level):
        if level == 0: return "OK"
        if level == 1: return "WARNING"
        if level == 2: return "ALARM"
        if level == 3: return "YAWN"
        return "UNKNOWN"

    def send_clear(self, ear, mar):
        alert_payload = {
            "alert": False, "level": 0, "buzzer_hz": 0, "buzzer_ms": 0, "timestamp": time.time()
        }
        data_payload = {
            "ear": round(ear, 3) if ear is not None else 0.0,
            "mar": round(mar, 3) if mar is not None else 0.0,
            "alert_level": 0, "consec_frames": 0, "status": "OK", "timestamp": time.time()
        }
        self.client.publish("driver/drowsy/alert", json.dumps(alert_payload))
        self.client.publish("driver/drowsy/data", json.dumps(data_payload))

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


class DrowsinessDetector:
    def __init__(self, mqtt_manager):
        self.mqtt_manager = mqtt_manager
        print("[INFO] Loading facial landmark predictor...")
        self.detector = dlib.get_frontal_face_detector()
        try:
            self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        except RuntimeError:
            print("[ERROR] shape_predictor_68_face_landmarks.dat not found!")
            print("Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
            exit(1)
            
        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        (self.mStart, self.mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["inner_mouth"]
        
        self.eye_counter = 0
        self.yawn_counter = 0
        self.alert_level = 0
        self.prev_time = 0
        self.fps = 0

    def _eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    def _mouth_aspect_ratio(self, mouth):
        A = dist.euclidean(mouth[1], mouth[7])
        B = dist.euclidean(mouth[2], mouth[6])
        C = dist.euclidean(mouth[3], mouth[5])
        D = dist.euclidean(mouth[0], mouth[4])
        return (A + B + C) / (2.0 * D)

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        ear = None
        mar = None
        status = "OK"

        if len(rects) > 0:
            shape = self.predictor(gray, rects[0])
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[self.lStart:self.lEnd]
            rightEye = shape[self.rStart:self.rEnd]
            mouth = shape[self.mStart:self.mEnd]

            ear = (self._eye_aspect_ratio(leftEye) + self._eye_aspect_ratio(rightEye)) / 2.0
            mar = self._mouth_aspect_ratio(mouth)

            if mar > MAR_THRESHOLD:
                self.yawn_counter += 1
                if self.yawn_counter >= YAWN_FRAMES:
                    self.alert_level = 3
                    status = "YAWN"
            else:
                self.yawn_counter = 0
                
            if self.yawn_counter < YAWN_FRAMES:
                if ear < EAR_THRESHOLD:
                    self.eye_counter += 1
                    if self.eye_counter >= CONSEC_FRAMES:
                        self.alert_level = 2
                        status = "ALARM"
                    elif self.eye_counter >= 10:
                        self.alert_level = 1
                        status = "WARNING"
                else:
                    self.eye_counter = 0
                    self.alert_level = 0
                    status = "OK"

            color = (0, 255, 0) if self.alert_level == 0 else (0, 0, 255)
            cv2.drawContours(frame, [cv2.convexHull(leftEye)], -1, color, 1)
            cv2.drawContours(frame, [cv2.convexHull(rightEye)], -1, color, 1)
            cv2.drawContours(frame, [cv2.convexHull(mouth)], -1, (255, 0, 255) if status == "YAWN" else color, 1)

        else:
            self.eye_counter, self.yawn_counter, self.alert_level = 0, 0, 0
            
        return frame, {"ear": ear, "mar": mar, "level": self.alert_level, "eye_frames": self.eye_counter, "yawn_frames": self.yawn_counter, "status": status}

    def _trigger_alert(self, level, ear, mar, frames):
        self.mqtt_manager.send_alert(level, ear, mar, frames)

    def _clear_alert(self, ear, mar):
        self.mqtt_manager.send_clear(ear, mar)

    def _draw_hud(self, frame, ear, mar, alert_level, eye_frames):
        h, w = frame.shape[:2]
        curr_time = time.time()
        self.fps = 1 / (curr_time - self.prev_time) if self.prev_time > 0 else 0
        self.prev_time = curr_time
        
        cv2.putText(frame, f"FPS: {int(self.fps)}", (w - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (320, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        cv2.putText(frame, f"EAR: {ear:.3f}" if ear else "EAR: N/A", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"MAR: {mar:.3f}" if mar else "MAR: N/A", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame Count: {eye_frames}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        status_text, color = ("OK", (0, 255, 0))
        if alert_level == 1: status_text, color = ("WARNING", (0, 255, 255))
        elif alert_level == 2: status_text, color = ("ALARM!", (0, 0, 255))
        elif alert_level == 3: status_text, color = ("YAWNING", (255, 0, 255))
            
        cv2.putText(frame, f"STATUS: {status_text}", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        if alert_level == 2:
            cv2.rectangle(frame, (0, h - 50), (w, h), (0, 0, 255), -1)
            cv2.putText(frame, "DRIVER SLEEPING - ALARM TRIGGERED", (w//2 - 250, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    def run(self):
        print("[INFO] Starting video stream...")
        cap = cv2.VideoCapture(CAMERA_INDEX)
        prev_level = 0
        frame_counter = 0
        
        while True:
            ret, frame = cap.read()
            if not ret: break
                
            frame, status_dict = self.process_frame(frame)
            level = status_dict["level"]
            
            if level > 0:
                if frame_counter % 5 == 0:
                    self._trigger_alert(level, status_dict["ear"], status_dict["mar"], max(status_dict["eye_frames"], status_dict["yawn_frames"]))
            else:
                if prev_level > 0:
                    self._clear_alert(status_dict["ear"], status_dict["mar"])
                elif frame_counter % 30 == 0:
                    self.mqtt_manager.client.publish("driver/drowsy/data", json.dumps({"ear": round(status_dict["ear"], 3) if status_dict["ear"] else 0.0, "mar": round(status_dict["mar"], 3) if status_dict["mar"] else 0.0, "alert_level": 0, "consec_frames": 0, "status": "OK", "timestamp": time.time()}))
                    
            prev_level = level
            self._draw_hud(frame, status_dict["ear"], status_dict["mar"], level, status_dict["eye_frames"])
            cv2.imshow("Drowsiness Detector", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            frame_counter += 1
                
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    mqtt_mgr = MQTTManager()
    mqtt_mgr.connect(MQTT_BROKER, MQTT_PORT)
    time.sleep(1)
    detector = DrowsinessDetector(mqtt_mgr)
    detector.run()
    mqtt_mgr.disconnect()
