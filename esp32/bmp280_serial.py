"""Stream BMP280 measurements as JSON over USB serial.

Save this file on the ESP32-S3 as main.py. It requires no Wi-Fi. The laptop
bridge reads each JSON line from the board's COM port and sends it to Flask.
"""

from machine import Pin, I2C
from time import sleep
import json
import struct


class BMP280:
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
        i2c.writeto_mem(address, 0xF4, b"\x27")

    def read(self):
        data = self.i2c.readfrom_mem(self.address, 0xF7, 6)
        adc_pressure = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_temperature = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)

        var1 = (((adc_temperature >> 3) - (self.T1 << 1)) * self.T2) >> 11
        var2 = (((((adc_temperature >> 4) - self.T1) * ((adc_temperature >> 4) - self.T1)) >> 12) * self.T3) >> 14
        fine_temperature = var1 + var2
        temperature = ((fine_temperature * 5 + 128) >> 8) / 100.0

        var1 = fine_temperature - 128000
        var2 = var1 * var1 * self.P6
        var2 += (var1 * self.P5) << 17
        var2 += self.P4 << 35
        var1 = ((var1 * var1 * self.P3) >> 8) + ((var1 * self.P2) << 12)
        var1 = (((1 << 47) + var1) * self.P1) >> 33
        if var1 == 0:
            return temperature, 0

        pressure = 1048576 - adc_pressure
        pressure = (((pressure << 31) - var2) * 3125) // var1
        var1 = (self.P9 * (pressure >> 13) * (pressure >> 13)) >> 25
        var2 = (self.P8 * pressure) >> 19
        pressure = ((pressure + var1 + var2) >> 8) + (self.P7 << 4)
        return temperature, pressure / 256.0 / 100.0


i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
bmp280 = BMP280(i2c)

while True:
    temperature, pressure = bmp280.read()
    print(json.dumps({
        "temperature": round(temperature, 2),
        "pressure": round(pressure, 2),
    }))
    sleep(2)
