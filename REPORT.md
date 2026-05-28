# IoT Assignment Report — 1dv027

## 1. Project Links

| Resource | URL |
|----------|-----|
| Dashboard |  |
| Node-RED backend |  |
| Wokwi simulation |  |
| GitHub repository | https://github.com/Hoohaaw/IoT |

---

## 2. Project Overview

This project implements an end-to-end IoT pipeline that monitors temperature from a Raspberry Pi Pico W simulated in Wokwi. The device reads the internal temperature sensor every 10 seconds and publishes the value over MQTT. A Node-RED backend ingests the data, stores it in a SQLite database for persistence, and displays it in real-time on a web dashboard. The dashboard also allows the user to toggle the device's onboard LED via MQTT commands.

---

## 3. Architecture & Data Flow

```
┌─────────────────────────────┐
│   Wokwi (Pico W)            │
│   main.py (MicroPython)     │
│                             │
│  ADC4 → temperature read    │
│  ADC26 → battery monitor    │
│  GPIO15 → low-battery LED   │
│  onboard LED → command LED  │
└────────────┬────────────────┘
             │ MQTT publish
             │ lnu/iot/<id>/sensor
             │ {"value": 23.5, "timestamp": 1710063386}
             ▼
┌─────────────────────────────┐
│   MQTT Broker               │
│   broker.emqx.io:1883       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│   Node-RED                                  │
│                                             │
│  [mqtt in] → [json] → [sqlite INSERT]       │  persist
│  [mqtt in] → [gauge] + [chart]              │  real-time UI
│  [inject on start] → [sqlite SELECT] → [chart] │  history load
│  [dashboard buttons] → [mqtt out: LED cmd]  │  device control
└──────────────────────┬──────────────────────┘
                       │ MQTT publish
                       │ lnu/iot/<id>/command/led
                       │ {"state": true/false}
                       ▼
             Back to Wokwi device
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
LIMIT 100
```

The 100 most recent readings are reversed into chronological order and fed into the dashboard chart, so the chart is pre-populated when a user opens the dashboard.

---

## 5. MQTT Topics & Payload Documentation

| Topic | Direction | Publisher | Subscriber | Payload format |
|-------|-----------|-----------|------------|----------------|
| `lnu/iot/<student_id>/sensor` | Device → Backend | Wokwi (Pico W) | Node-RED | `{"value": 23.5, "timestamp": 1710063386}` |
| `lnu/iot/<student_id>/command/led` | Dashboard → Device | Node-RED | Wokwi (Pico W) | `{"state": true}` or `{"state": false}` |

**Field descriptions:**

- `value` — temperature in °C, rounded to 1 decimal place
- `timestamp` — Unix epoch seconds (MicroPython `utime.time()` + 946684800 offset)
- `state` — boolean; `true` turns the onboard LED on, `false` turns it off

---

## 6. Reflection

**Why did you choose Node-RED Dashboard as the frontend technology?**


**Real-time MQTT vs REST polling — what are the tradeoffs?**


**What was the biggest challenge?**

