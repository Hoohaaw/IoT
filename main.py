import network
import socket
from machine import Pin, ADC
import time

# WiFi credentials
SSID = "MOVISTAR-WIFI6-C070"
PASSWORD = "j3bfYrju4SDN6bFd79MJ"

# Battery monitoring (GP26 / ADC0 via voltage divider)
battery_sensor = ADC(26)
low_battery_led = Pin(15, Pin.OUT)
LOW_BATTERY_THRESHOLD = 3.4

def read_battery_voltage():
    raw = battery_sensor.read_u16()
    adc_voltage = raw * 3.3 / 65535
    battery_voltage = adc_voltage * 2  # voltage divider ratio (10k/10k)
    return battery_voltage

def check_battery():
    voltage = read_battery_voltage()
    if voltage < LOW_BATTERY_THRESHOLD:
        low_battery_led.on()
    else:
        low_battery_led.off()
    return voltage

# Temperature sensor
temp_sensor = ADC(4)
cached_temp = None
last_temp_time = 0

def read_temperature():
    raw = temp_sensor.read_u16()
    voltage = raw * 3.3 / 65535
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature

def update_temperature():
    global cached_temp, last_temp_time
    now = time.time()
    if cached_temp is None or now - last_temp_time >= 600:
        cached_temp = read_temperature()
        last_temp_time = now
        battery_v = check_battery()
        print(f"Temperature updated: {cached_temp:.1f} °C | Battery: {battery_v:.2f}V")
    return cached_temp

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting to WiFi...")
while not wlan.isconnected():
    time.sleep(1)

print(f"Connected! Open: http://{wlan.ifconfig()[0]}")

# Read and serve files
def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def get_dashboard():
    html = read_file('dashboard.html')
    temp = update_temperature()
    html = html.replace('-- °C', f'{temp:.1f} °C')
    return html

# Start server
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(5)

print("Server running...")

s.settimeout(1)

while True:
    try:
        cl, addr = s.accept()
    except OSError:
        continue

    try:
        request = cl.recv(1024).decode('utf-8')

        # Route requests
        if 'GET /temp.css' in request:
            response = read_file('temp.css')
            cl.send("HTTP/1.0 200 OK\r\nContent-type: text/css\r\n\r\n")
        elif 'GET /dashboard.js' in request:
            response = read_file('dashboard.js')
            cl.send("HTTP/1.0 200 OK\r\nContent-type: application/javascript\r\n\r\n")
        elif 'GET /data' in request:
            temp = update_temperature()
            response = '{"temperature": %.1f}' % temp
            cl.send("HTTP/1.0 200 OK\r\nContent-type: application/json\r\nCache-Control: no-store\r\nContent-Length: %d\r\n\r\n" % len(response))
        elif 'GET / ' in request:
            response = get_dashboard()
            cl.send("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
        else:
            cl.send("HTTP/1.0 404 Not Found\r\n\r\n")
            cl.close()
            continue

        cl.send(response)
    except Exception as e:
        print("Error:", e)
    finally:
        cl.close()