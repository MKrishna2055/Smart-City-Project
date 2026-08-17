# USB-connected ESP32 BMP280 dashboard integration

This project supports two display modes:

- **City weather**: current weather for the selected map location.
- **ESP32 BMP280 sensor**: the newest BMP280 value received through the laptop bridge.

This setup does **not** need Wi-Fi on the ESP32. Keep the board connected to the laptop by USB.

## 1. Deploy the Flask project

Deploy the project to Render and set a secret environment variable:

```text
SENSOR_API_KEY=<a long random secret>
```

The laptop bridge posts data to `POST /api/esp32/readings`. The dashboard reads the newest value from `GET /api/esp32/latest` every five seconds without reloading the page.

## 2. Run the ESP32 sensor program

1. Open `esp32/bmp280_serial.py` in Thonny.
2. Save/copy it to the ESP32 as `main.py`.
3. Reset the board.

It prints one JSON reading every two seconds, for example:

```json
{"temperature": 30.98, "pressure": 909.35}
```

BMP280 wiring: `SDA -> GPIO 8`, `SCL -> GPIO 9`, `VCC -> 3.3V`, `GND -> GND`.

## 3. Run the laptop bridge

Close Thonny and any serial monitor first; only one application can use the COM port.

Open `bridge/laptop_serial_bridge.py` and edit:

```python
SERIAL_PORT = "COM6"
DASHBOARD_URL = "https://YOUR-RENDER-SERVICE.onrender.com/api/esp32/readings"
SENSOR_API_KEY = "the same secret set in Render"
```

Install the laptop dependencies once:

```powershell
py -m pip install -r bridge/requirements.txt
```

Then run the bridge:

```powershell
py bridge/laptop_serial_bridge.py
```

When it prints `Uploaded: ...`, open the dashboard and select **ESP32 BMP280 sensor** in the Temperature Data Source selector.

The laptop needs internet access and must keep this bridge program running. Press `Ctrl+C` to stop it.
