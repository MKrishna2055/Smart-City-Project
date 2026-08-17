"""Send ESP32-S3 BMP280 readings to the Smart City dashboard.

Save this as main.py on an ESP32-S3 running MicroPython. Before uploading,
set WIFI_SSID, WIFI_PASSWORD, DASHBOARD_URL and SENSOR_API_KEY below.
"""

from machine import Pin, I2C
from time import sleep
import json
import network
import struct

try:
    import urequests as requests
except ImportError:
    from urllib import urequest as requests


# ---------- Configure these four values ----------
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
DASHBOARD_URL = "https://YOUR-RENDER-SERVICE.onrender.com/api/esp32/readings"
SENSOR_API_KEY = "SET_THE_SAME_SECRET_AS_RENDER"

DEVICE_ID = "esp32-s3-bmp280-01"
LOCATION = "Smart City sensor node"
SEND_INTERVAL_SECONDS = 60


class BMP280:
    """Minimal BMP280 I2C driver for temperature and pressure."""

    def __init__(self, i2c, address=0x76):
        self.i2c = i2c
        self.address = address
        chip_id = i2c.readfrom_mem(address, 0xD0, 1)[0]
        if chip_id != 0x58:
            raise OSError("BMP280 not found (chip id: {})".format(chip_id))

        calibration = i2c.readfrom_mem(address, 0x88, 24)
        (
            self.T1, self.T2, self.T3, self.P1, self.P2, self.P3,
            self.P4, self.P5, self.P6, self.P7, self.P8, self.P9,
        ) = struct.unpack("<HhhHhhhhhhhh", calibration)

        # Temperature x1, pressure x1, normal measurement mode.
        i2c.writeto_mem(address, 0xF4, b"\x27")

    def read(self):
        data = self.i2c.readfrom_mem(self.address, 0xF7, 6)
        adc_pressure = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_temperature = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)

        temperature_var1 = (((adc_temperature >> 3) - (self.T1 << 1)) * self.T2) >> 11
        temperature_var2 = (
            ((((adc_temperature >> 4) - self.T1) * ((adc_temperature >> 4) - self.T1)) >> 12)
            * self.T3
        ) >> 14
        fine_temperature = temperature_var1 + temperature_var2
        temperature = ((fine_temperature * 5 + 128) >> 8) / 100.0

        pressure_var1 = fine_temperature - 128000
        pressure_var2 = pressure_var1 * pressure_var1 * self.P6
        pressure_var2 += (pressure_var1 * self.P5) << 17
        pressure_var2 += self.P4 << 35
        pressure_var1 = ((pressure_var1 * pressure_var1 * self.P3) >> 8) + ((pressure_var1 * self.P2) << 12)
        pressure_var1 = (((1 << 47) + pressure_var1) * self.P1) >> 33

        if pressure_var1 == 0:
            return temperature, 0

        pressure = 1048576 - adc_pressure
        pressure = (((pressure << 31) - pressure_var2) * 3125) // pressure_var1
        pressure_var1 = (self.P9 * (pressure >> 13) * (pressure >> 13)) >> 25
        pressure_var2 = (self.P8 * pressure) >> 19
        pressure = ((pressure + pressure_var1 + pressure_var2) >> 8) + (self.P7 << 4)
        return temperature, pressure / 256.0 / 100.0  # hPa


def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    if wifi.isconnected():
        return wifi

    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(40):
        if wifi.isconnected():
            print("Wi-Fi connected:", wifi.ifconfig()[0])
            return wifi
        sleep(0.5)
    raise OSError("Could not connect to Wi-Fi")


def post_reading(temperature, pressure):
    payload = {
        "device_id": DEVICE_ID,
        "location": LOCATION,
        "temperature": round(temperature, 2),
        "pressure": round(pressure, 2),
    }
    response = requests.post(
        DASHBOARD_URL,
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "X-Sensor-Key": SENSOR_API_KEY,
        },
    )
    try:
        print("Dashboard response:", response.status_code, response.text)
    finally:
        response.close()


i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
bmp280 = BMP280(i2c)

while True:
    try:
        temperature, pressure = bmp280.read()
        print("Temperature: {:.2f} C | Pressure: {:.2f} hPa".format(temperature, pressure))
        connect_wifi()
        post_reading(temperature, pressure)
    except Exception as error:
        print("Sensor upload failed:", error)

    sleep(SEND_INTERVAL_SECONDS)
