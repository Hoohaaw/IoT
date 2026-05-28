import network
import ujson
import utime
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# WiFi credentials
SSID = "MOVISTAR-WIFI6-C070"
PASSWORD = "j3bfYrju4SDN6bFd79MJ"

# MQTT settings — replace STUDENT_ID with your LNU student ID (e.g. "al224cj")
STUDENT_ID = "ap224gy"
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC_SENSOR = "lnu/iot/" + STUDENT_ID + "/sensor"
TOPIC_LED = "lnu/iot/" + STUDENT_ID + "/command/led"
TOPIC_WIFI = "lnu/iot/" + STUDENT_ID + "/wifi"
CLIENT_ID = "pico-" + STUDENT_ID

# MicroPython epoch is 2000-01-01; Unix epoch is 1970-01-01 (946684800s difference)
EPOCH_OFFSET = 946684800

# Hardware
command_led = Pin("LED", Pin.OUT)  # onboard LED responds to dashboard commands
temp_sensor = ADC(4)

def read_temperature():
    raw = temp_sensor.read_u16()
    voltage = raw * 3.3 / 65535
    return 27 - (voltage - 0.706) / 0.001721

def on_message(_topic, msg):
    try:
        data = ujson.loads(msg)
        state = data.get("state", False)
        command_led.value(1 if state else 0)
        print("LED:", "ON" if state else "OFF")
    except Exception as e:
        print("Bad command payload:", e)

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Scan before connecting — chip returns results when not yet associated
scan_results = wlan.scan()
nets = [{"ssid": n[0].decode(), "rssi": n[3]} for n in scan_results]
print("WiFi scan found:", len(nets), "networks")

wlan.connect(SSID, PASSWORD)
print("Connecting to WiFi...")
while not wlan.isconnected():
    utime.sleep(1)
print("WiFi connected:", wlan.ifconfig()[0])

# Connect to MQTT broker
client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
client.set_callback(on_message)
client.connect()
client.subscribe(TOPIC_LED)
print("MQTT connected to", MQTT_BROKER)
print("Publishing to:", TOPIC_SENSOR)
print("Subscribed to:", TOPIC_LED)

# Publish scan results (retained so Node-RED gets it even if it connects later)
client.publish(TOPIC_WIFI, ujson.dumps({"networks": nets}), retain=True)
print("WiFi scan published:", len(nets), "networks")

PUBLISH_INTERVAL = 10
last_publish = -PUBLISH_INTERVAL  # publish immediately on first loop

while True:
    client.check_msg()
    now = utime.time()
    if now - last_publish >= PUBLISH_INTERVAL:
        temp = read_temperature()
        unix_ts = now + EPOCH_OFFSET
        payload = ujson.dumps({"value": round(temp, 1), "timestamp": unix_ts})
        client.publish(TOPIC_SENSOR, payload)
        print("Published:", payload)
        last_publish = now
    utime.sleep_ms(100)
