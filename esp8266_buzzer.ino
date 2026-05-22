#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID     = "Dika71";
const char* WIFI_PASSWORD = "dika711";
const char* MQTT_BROKER   = "your_ip_address";
const int MQTT_PORT       = 1883;

#define BUZZER_PIN D1
#define RED_LED    D2
#define YELLOW_LED D3
#define GREEN_LED  D4

WiFiClient espClient;
PubSubClient client(espClient);

int current_level = 0;
bool is_alert = false;
int buzzer_hz = 0;
int buzzer_ms = 0;

unsigned long last_mqtt_reconnect = 0;
unsigned long last_heartbeat = 0;
unsigned long buzzer_start_time = 0;
int prev_level = -1;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  is_alert = doc["alert"];
  current_level = doc["level"];
  buzzer_hz = doc["buzzer_hz"];
  buzzer_ms = doc["buzzer_ms"];
  
  if(current_level == 0) {
      noTone(BUZZER_PIN);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);

  setup_wifi();
  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(callback);
}

void reconnect() {
  if (!client.connected()) {
    if (millis() - last_mqtt_reconnect > 5000) {
      last_mqtt_reconnect = millis();
      Serial.print("Attempting MQTT connection...");
      if (client.connect("ESP8266Client")) {
        Serial.println("connected");
        client.subscribe("driver/drowsy/alert");
      } else {
        Serial.print("failed, rc=");
        Serial.print(client.state());
        Serial.println(" try again in 5 seconds");
      }
    }
  }
}

void handle_leds() {
  if (current_level == 0) {
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
  } else if (current_level == 1) {
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, LOW);
    digitalWrite(YELLOW_LED, HIGH);
  } else if (current_level == 2) {
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
    if ((millis() / 500) % 2 == 0) {
      digitalWrite(RED_LED, HIGH);
    } else {
      digitalWrite(RED_LED, LOW);
    }
  } else if (current_level == 3) {
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(RED_LED, HIGH);
  }
}

void handle_buzzer() {
  if (current_level == 0) {
    noTone(BUZZER_PIN);
    return;
  }
  
  unsigned long current_time = millis();
  
  if (current_level == 1) {
    if (current_time - buzzer_start_time < 1800) {
      unsigned long cycle = (current_time - buzzer_start_time) % 600;
      if (cycle < 200) tone(BUZZER_PIN, 1000);
      else noTone(BUZZER_PIN);
    } else {
      noTone(BUZZER_PIN);
    }
  } else if (current_level == 2) {
    unsigned long cycle = (current_time - buzzer_start_time) % 1000;
    if (cycle < 800) tone(BUZZER_PIN, 2500);
    else noTone(BUZZER_PIN);
  } else if (current_level == 3) {
    if (current_time - buzzer_start_time < 3000) {
      unsigned long cycle = (current_time - buzzer_start_time) % 600;
      if (cycle < 300) tone(BUZZER_PIN, 800);
      else noTone(BUZZER_PIN);
    } else {
      noTone(BUZZER_PIN);
    }
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }
  
  if (!client.connected()) {
    reconnect();
  } else {
    client.loop();
  }
  
  if (current_level != prev_level) {
    buzzer_start_time = millis();
    prev_level = current_level;
  }

  handle_leds();
  handle_buzzer();

  if (millis() - last_heartbeat > 30000) {
    last_heartbeat = millis();
    if (client.connected()) {
      StaticJsonDocument<200> heartbeat;
      heartbeat["ip"] = WiFi.localIP().toString();
      heartbeat["rssi"] = WiFi.RSSI();
      heartbeat["alert_level"] = current_level;
      
      char out[200];
      serializeJson(heartbeat, out);
      client.publish("driver/buzzer/status", out);
    }
  }
}
