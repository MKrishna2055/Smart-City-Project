# ESP32 BMP280 dashboard integration

The dashboard now offers a **Temperature Data Source** selector:

- **City weather** keeps the current map/Open-Meteo behavior.
- **ESP32 BMP280 sensor** displays the newest temperature and pressure sent by the physical board.

## Configure the Flask deployment

Set `SENSOR_API_KEY` as an environment variable in Render. Use a long random value and do not commit it to Git.

The ESP32 sends JSON to:

```text
POST /api/esp32/readings
```

with this header:

```text
X-Sensor-Key: <SENSOR_API_KEY>
```

The UI polls `GET /api/esp32/latest` every 30 seconds. It shows the city weather by default, so the existing map behavior is unchanged.

## Configure the ESP32

1. Open `esp32/bmp280_dashboard.py` in Thonny.
2. Update `WIFI_SSID`, `WIFI_PASSWORD`, `DASHBOARD_URL`, and `SENSOR_API_KEY`.
3. Keep the BMP280 wiring: `SDA -> GPIO 8`, `SCL -> GPIO 9`, `VCC -> 3.3V`, `GND -> GND`.
4. Run it in Thonny to test, then save/copy it onto the ESP32 as `main.py` for automatic startup.

The `DASHBOARD_URL` must include your public Render URL and end with `/api/esp32/readings`.

## Notes

- The example posts one reading per minute to avoid excess traffic.
- The application uses SQLite because the existing project does. Render's default filesystem is ephemeral, so readings may be lost after a redeploy unless the service has persistent storage.
