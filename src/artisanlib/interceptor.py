import paho.mqtt.client as mqtt
import ssl
import certifi
import json
import time
from threading import Thread, Event
import struct

# Konfigurasi MQTT
MQTT_BROKER = "53c95f21fd7f415c8ec029216dd46417.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "vulca/roaster/data"
USERNAME = "vul_pub"
PASSWORD = "4WTW8gJKO9sTQwx1K9hzDOGkstWmrQRt"

# === TAG DEFINITIONS (integer TLV) ===
TAG_BT          = 0x01  # Bean Temperature
TAG_LIMIT_BT    = 0x02  # Limit Bean Temp
TAG_ET          = 0x03  # Environment Temp
TAG_LIMIT_ET    = 0x04  # Limit Env Temp
TAG_AIRFLOW     = 0x05  # Airflow (%)
TAG_DRUMSPEED   = 0x06  # Drum Speed (%)
TAG_TIMESTAMP   = 0x07  # Epoch seconds (int)
TAG_DELTA_BT    = 0x08  # Delta Bean Temp
TAG_DELTA_ET    = 0x09  # Delta Env Temp
TAG_TIMER       = 0x0A  # Timer (s)

# === MQTT Setup ===
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(
    ca_certs=certifi.where(),
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected successfully.")
    else:
        print(f"[MQTT] Failed to connect, return code {rc}")

client.on_connect = on_connect
client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()  # Loop MQTT di thread terpisah

# === Inisialisasi Threading ===
class MqttInterceptor:
    def __init__(self):
        self._stop_event = Event()
    
    def publish_to_mqtt(self, et_value, bt_value, delta_et_value, delta_bt_value):
        # Jalankan di thread terpisah
        # Start a new thread to publish MQTT data asynchronously with the given roasting parameters
        Thread(target=self._publish_thread, args=(et_value, bt_value, delta_et_value, delta_bt_value)).start()
    
    def _publish_thread(self, et_value, bt_value, delta_et_value, delta_bt_value):
        if not self._stop_event.is_set():
            try:
                # Encode data ke dalam format TLV (Sama Persis dengan UI)
                payload = (
                    self.encode_tlv_int(TAG_TIMESTAMP, int(time.time())) +
                    self.encode_tlv_int(TAG_ET, int(float(et_value))) +
                    self.encode_tlv_int(TAG_BT, int(float(bt_value))) +
                    self.encode_tlv_int(TAG_DELTA_BT, int(float(delta_et_value))) +
                    self.encode_tlv_int(TAG_DELTA_ET, int(float(delta_bt_value)))
                )

                # Kirim payload ke MQTT
                client.publish(MQTT_TOPIC, payload)
                print(f"[MQTT PUBLISH] Data sent to '{MQTT_TOPIC}': ET={et_value}, BT={bt_value}")
            except Exception as e:
                print(f"[ERROR] MQTT Publish failed: {e}")
    
    def stop(self):
        self._stop_event.set()

    @staticmethod
    def encode_tlv_int(tag: int, value: int) -> bytes:
        """
        Encode one TLV field as:
          T = 1 byte tag
          L = 1 byte length (4)
          V = 4-byte unsigned int, big-endian
        """
        val_bytes = struct.pack(">I", value)
        return struct.pack("B", tag) + struct.pack("B", len(val_bytes)) + val_bytes
    
    @staticmethod
    def timer_to_int(timer_str):
        try:
            # Pisahkan menit dan detik
            minutes, seconds = map(int, timer_str.split(":"))
            # Konversikan ke total detik
            total_seconds = minutes * 60 + seconds
            return total_seconds
        except ValueError:
            print(f"[ERROR] Invalid timer format: {timer_str}")
            return 0