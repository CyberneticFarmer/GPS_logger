import serial
import math
from datetime import datetime, timedelta
import os
import json

def convert_to_decimal(degree_min, direction):
    degrees = int(float(degree_min) / 100)
    minutes = float(degree_min) - degrees * 100
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def parse_gngga(sentence):
    parts = sentence.split(',')
    if len(parts) >= 6 and parts[0].endswith("GGA"):
        time_raw = parts[1]
        lat_raw = parts[2]
        lat_dir = parts[3]
        lon_raw = parts[4]
        lon_dir = parts[5]
        if not lat_raw or not lon_raw:
            return None
        time_formatted = f"{time_raw[0:2]}:{time_raw[2:4]}:{time_raw[4:6]}"
        lat = convert_to_decimal(lat_raw, lat_dir)
        lon = convert_to_decimal(lon_raw, lon_dir)
        return time_formatted, lat, lon
    return None

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c * 1000 * 100 # meter

def create_new_file(base_dir):
    now = datetime.now()
    day_dir = now.strftime("%Y-%m-%d")
    full_dir = os.path.join(base_dir, day_dir)
    os.makedirs(full_dir, exist_ok=True)
    file_name = now.strftime("%H%M%S") + ".geojson"
    file_path = os.path.join(full_dir, file_name)
    return file_path, now

def write_geojson(file_path, coordinates, start_time):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "start_time": start_time.strftime("%H:%M:%S"),
                    "points": len(coordinates)
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            }
        ]
    }
    with open(file_path, "w") as geojson_file:
        json.dump(geojson_data, geojson_file, indent=2)
    print(f"GeoJSON lagret: {file_path}")

def main():
    port = 'COM13'
    baudrate = 115200
    base_dir = "GPS_data"

    coordinates = []
    lat_saved = None
    lon_saved = None
    file_path, start_time = create_new_file(base_dir)
    last_update_time = datetime.now()

    print(f"Lagrer til fil: {file_path}")

    with serial.Serial(port, baudrate, timeout=1) as ser:
        print("Lytter på COM-porten for GNGGA-data...\nTrykk Ctrl+C for å stoppe.")
        try:
            while True:
                now = datetime.now()

                # Timeout: Har det gått mer enn 60 sek siden forrige punkt?
                if coordinates and (now - last_update_time > timedelta(seconds=10)):
                    print("Ingen nye punkter på 60 sekunder – lagrer og starter ny fil.")
                    write_geojson(file_path, coordinates, start_time)

                    # Start ny fil
                    coordinates = []
                    lat_saved = None
                    lon_saved = None
                    file_path, start_time = create_new_file(base_dir)
                    last_update_time = now
                    print(f"Starter ny fil: {file_path}")

                line = ser.readline().decode('ascii', errors='ignore').strip()
                if line.startswith('$GNGGA'):
                    result = parse_gngga(line)
                    if result:
                        time_str, lat, lon = result
                        if lat_saved is None or lon_saved is None:
                            lat_saved = lat
                            lon_saved = lon
                            coordinates.append([lon, lat])
                            last_update_time = now
                            print(f"{time_str} - Første posisjon lagret ({lat:.6f}, {lon:.6f})")
                        else:
                            distance = haversine_distance(lat, lon, lat_saved, lon_saved)
                            if distance > 4:  # meter
                                coordinates.append([lon, lat])
                                lat_saved = lat
                                lon_saved = lon
                                last_update_time = now
                                print(f"{time_str} - Ny posisjon ({lat:.6f}, {lon:.6f}) lagt til, avstand: {distance:.2f} m")

        except KeyboardInterrupt:
            print("\nAvslutter og lagrer siste fil...")
            if coordinates:
                write_geojson(file_path, coordinates, start_time)


if __name__ == "__main__":
    main()



