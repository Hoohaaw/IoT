# IoT Assignment Report — 1dv027

## 1. Project Links

| Resource | URL |
|----------|-----|
| Dashboard | https://iot-production-c7c4.up.railway.app/ui |
| Node-RED backend | https://iot-production-c7c4.up.railway.app |
| GitHub repository | https://github.com/Hoohaaw/IoT |

---

## 2. Project Overview

This project implements an end-to-end IoT pipeline that monitors temperature from a physical Raspberry Pi Pico WH. The device scans nearby WiFi networks once on boot and publishes the results, then reads the internal temperature sensor every 10 seconds and publishes the value over MQTT. A Node-RED backend ingests the data, stores it in a SQLite database for persistence, and displays it in real-time on a web dashboard. The dashboard shows live temperature, a historical chart, a list of nearby WiFi networks with signal strength, a Pico online/offline status indicator, and allows the user to toggle the device's onboard LED via MQTT commands.

---

## 3. Architecture & Data Flow

```
┌─────────────────────────────┐
│   Raspberry Pi Pico WH      │
│   main.py (MicroPython)     │
│                             │
│  WiFi scan → on boot        │
│  ADC4 → temperature read    │
│  onboard LED → command LED  │
└────────────┬────────────────┘
             │ MQTT publish
             │ lnu/iot/ap224gy/wifi     (once on boot, retained)
             │ lnu/iot/ap224gy/sensor   (every 10 seconds)
             ▼
┌─────────────────────────────┐
│   MQTT Broker               │
│   broker.emqx.io:1883       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│   Node-RED (deployed on Railway)                │
│                                                 │
│  [mqtt in] → [json] → [sqlite INSERT]           │  persist
│  [mqtt in] → [template] + [chart]               │  real-time UI
│  [inject on start] → [sqlite SELECT] → [chart]  │  history load
│  [mqtt in] → [template: WiFi list]              │  WiFi scan display
│  [timer/15s] → [flow context] → [status widget] │  Pico online check
│  [dashboard buttons] → [mqtt out: LED cmd]      │  device control
└──────────────────────┬──────────────────────────┘
                       │ MQTT publish
                       │ lnu/iot/ap224gy/command/led
                       │ {"state": true/false}
                       ▼
             Back to Pico WH device
```

---

## 4. Database Strategy

**Technology:** SQLite via `node-red-node-sqlite`

SQLite was chosen because it requires no separate server process, stores data in a single file (`iot_data.db`), and is well-supported in Node-RED. It is well-suited for single-device time-series data at this scale.

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS sensor_readings (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  value       REAL    NOT NULL,   -- temperature in °C
  timestamp   INTEGER NOT NULL,   -- Unix timestamp from device
  received_at TEXT    NOT NULL    -- ISO 8601 UTC time recorded by Node-RED
);
```

**Historical data access:** On Node-RED startup, an inject node fires after 1.5 seconds and runs:

```sql
SELECT value, timestamp, received_at
FROM sensor_readings
ORDER BY id DESC
LIMIT 10
```

The 10 most recent readings are reversed into chronological order and fed into the dashboard chart, so the chart is pre-populated when a user opens the dashboard.

---

## 5. MQTT Topics & Payload Documentation

| Topic | Direction | Publisher | Subscriber | Payload format |
|-------|-----------|-----------|------------|----------------|
| `lnu/iot/ap224gy/sensor` | Device → Backend | Raspberry Pi Pico WH | Node-RED | `{"value": 23.5, "timestamp": 1710063386}` |
| `lnu/iot/ap224gy/wifi` | Device → Backend | Raspberry Pi Pico WH | Node-RED | `{"networks": [{"ssid": "MyNet", "rssi": -45}]}` |
| `lnu/iot/ap224gy/command/led` | Dashboard → Device | Node-RED | Raspberry Pi Pico WH | `{"state": true}` or `{"state": false}` |

**Field descriptions:**

- `value` — temperature in °C, rounded to 1 decimal place
- `timestamp` — Unix epoch seconds (MicroPython `utime.time()` + 946684800 offset)
- `networks` — array of nearby WiFi networks, each with `ssid` (string) and `rssi` (integer, dBm)
- `state` — boolean; `true` turns the onboard LED on, `false` turns it off

---

## 6. Reflection

**Why did you choose Node-RED Dashboard as the frontend technology?**
I chose node-red for my frontend because there are a lot of pre built components that are given for free. And they are very easy to use. 

Also to connect a point of data to a component is way easier to just connect nodes instead of having to write JS code to make it work. This decreases development time by alot.

There might be less freedom in the things we can do as developers with this solution. But its a quetsion about scope. And for this assignment it made sense to me to use Node-red for these reasons.

**Real-time MQTT vs REST polling — what are the tradeoffs?**
The main difference is the event driven appraoch to MQTT. instead of having to query a API endpoint to see if there is changes to be made MQTT sends updates when there is new data. Since MQTT is working in a Subscribe/Publish way the data gets sent immediatly when a change is happening. 

The tradeoff is however the fact that there has to be a persisten connection between client and broker. And if that fails, there is no data to be served. 

**What was the biggest challenge?**
The biggest challenge was to find the way to connect the active sensors to the MQTT broker. For me this unveiled a lot of issues. I could not get the mpremote package to work. I then had to get into the IDE Thonny to instead just install the UMQTT.simple library directly to it through the library handler provided. Which then adds it to the Picos lib folder. Very much easier in my opinion. 

But this whole process to hook up the Pico the our wifi was also troublesome. For some reason our wifi router had some trouble with me trying to connect to it from the code directly. Therefore I had to sit an entire morning trying to figure out how to configure the router to accept the picos attempt to connect. I still dont really know what the issue was truly but now it works. 
