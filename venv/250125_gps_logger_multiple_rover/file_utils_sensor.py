import json
from datetime import datetime, timezone
import os

def save_sensor_string_to_js(input_string):
    # Ensure folder exists
    if (sys == "Windows"):
        folder = "C:/Users/reidb/PycharmProjects/250609_KML_norgeskart/venv/260209_web_analog/data"
    elif sys == "Linux":
        folder = "/var/www/html/Analog"


    os.makedirs(folder, exist_ok=True)

    # Clean input <A1,235,3.96>
    clean = input_string.strip()[1:-1]
    uid, value, battery = clean.split(",")

    # Timestamp at receive time (UTC)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Data point
    data_point = {
        "time": timestamp,
        "value": int(value),
        "battery": float(battery)
    }

    js_file = os.path.join(folder, f"{uid}.js")

    # Load existing data
    if os.path.exists(js_file):
        with open(js_file, "r") as f:
            content = f.read()
            start = content.find("[")
            end = content.rfind("]")
            data_array = json.loads(content[start:end+1])
    else:
        data_array = []

    # Append new reading
    data_array.append(data_point)

    # Write back to JS file
    with open(js_file, "w") as f:
        f.write("const sensorData = ")
        f.write(json.dumps(data_array, indent=2))
        f.write(";")
