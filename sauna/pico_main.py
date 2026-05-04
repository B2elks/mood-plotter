"""Frökenur Bastu — Pico W firmware.

Reads a DS18B20 temperature sensor and POSTs to the server every INTERVAL seconds.

Wiring:
  DS18B20 DATA → GP16  (with 4.7kΩ pull-up resistor between DATA and 3.3V)
  DS18B20 VCC  → 3.3V
  DS18B20 GND  → GND

Onboard LED behavior:
  - Slow blink while connecting to WiFi
  - Quick double-blink when a reading is sent successfully
  - Solid on while a reading or POST is failing
  - Off when idle waiting for next reading

Install:
  1. Flash MicroPython for Pico W from micropython.org
  2. Edit WIFI_SSID / WIFI_PASS below
  3. Copy this file to the Pico as `main.py`
  4. Reset — it auto-runs
"""

import machine
import network
import onewire
import ds18x20
import time
import urequests

# === CONFIG ===
WIFI_SSID = "BYT-MIG"
WIFI_PASS = "BYT-MIG"
SERVER_URL = "https://bastu.skyttberg.nu/api/temp"
SENSOR_PIN = 16
INTERVAL = 30           # seconds between readings
POST_TIMEOUT = 8        # HTTP timeout in seconds
WIFI_TIMEOUT = 30       # seconds to wait for initial wifi
WATCHDOG_TIMEOUT_MS = 8000  # reset if main loop hangs longer than this

# === HARDWARE ===
led = machine.Pin("LED", machine.Pin.OUT)
ow = onewire.OneWire(machine.Pin(SENSOR_PIN))
ds = ds18x20.DS18X20(ow)
wlan = network.WLAN(network.STA_IF)
wdt = machine.WDT(timeout=WATCHDOG_TIMEOUT_MS)


def blink(times, on_ms=80, off_ms=120):
    for _ in range(times):
        led.on()
        time.sleep_ms(on_ms)
        led.off()
        time.sleep_ms(off_ms)


def connect_wifi():
    """Connect (or reconnect) to WiFi. Blocks up to WIFI_TIMEOUT seconds."""
    wlan.active(True)
    if wlan.isconnected():
        return True
    print("WiFi: connecting to", WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    waited = 0
    while not wlan.isconnected() and waited < WIFI_TIMEOUT:
        led.on()
        time.sleep_ms(250)
        led.off()
        time.sleep_ms(250)
        waited += 1
        wdt.feed()
    if wlan.isconnected():
        print("WiFi OK", wlan.ifconfig()[0])
        return True
    print("WiFi FAIL")
    return False


def read_temp():
    """Read DS18B20. Returns float °C or None."""
    try:
        roms = ds.scan()
        if not roms:
            print("Sensor: none found")
            return None
        ds.convert_temp()
        time.sleep_ms(750)  # DS18B20 needs ~750ms to convert
        temp = ds.read_temp(roms[0])
        if temp is None or temp < -40 or temp > 125:
            print("Sensor: bogus reading", temp)
            return None
        return temp
    except Exception as e:
        print("Sensor error:", e)
        return None


def send_temp(temp):
    """POST temperature. Returns True on 2xx."""
    body = '{"temp":%.1f}' % temp
    resp = None
    try:
        resp = urequests.post(
            SERVER_URL,
            headers={"Content-Type": "application/json"},
            data=body,
            timeout=POST_TIMEOUT,
        )
        ok = 200 <= resp.status_code < 300
        print("POST %.1f → %d" % (temp, resp.status_code))
        return ok
    except Exception as e:
        print("POST error:", e)
        return False
    finally:
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass


# === MAIN ===
print("Frökenur Bastu sensor starting…")
connect_wifi()

while True:
    wdt.feed()

    if not wlan.isconnected():
        print("WiFi dropped, reconnecting…")
        led.on()
        wlan.disconnect()
        time.sleep(1)
        connect_wifi()

    wdt.feed()
    temp = read_temp()
    wdt.feed()

    if temp is None:
        led.on()  # solid = sensor problem
    else:
        ok = send_temp(temp)
        if ok:
            led.off()
            blink(2)  # quick double-blink on success
        else:
            led.on()  # solid = network/post problem

    # Sleep in small chunks so the watchdog stays fed
    remaining = INTERVAL
    while remaining > 0:
        wdt.feed()
        step = min(2, remaining)
        time.sleep(step)
        remaining -= step
