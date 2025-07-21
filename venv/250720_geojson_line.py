import serial
import serial.tools.list_ports
import math
import time
from datetime import datetime, timedelta
import os
import json

# Konvertering og parsing (som før)…

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
        lat_raw = parts[2]; lat_dir = parts[3]
        lon_raw = parts[4]; lon_dir = parts[5]
        if not lat_raw or not lon_raw:
            return None
        time_str = f"{time_raw[0:2]}:{time_raw[2:4]}:{time_raw[4:6]}"
        lat = convert_to_decimal(lat_raw, lat_dir)
        lon = convert_to_decimal(lon_raw, lon_dir)
        return time_str, lat, lon
    return None

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c * 1000  # i meter

def dp_simplify(points, epsilon):
    # Rekursiv implementasjon av RDP
    if len(points) < 3:
        return points
    # Finn punkt med maks avstand
    start, end = points[0], points[-1]
    max_dist, index = 0.0, 0
    for i in range(1, len(points)-1):
        cx, cy = points[i]
        # beregn perpendicular avstand til linjen start–end
        x0, y0 = cx, cy
        x1, y1 = start; x2, y2 = end
        num = abs((y2 - y1)*x0 - (x2 - x1)*y0 + x2*y1 - y2*x1)
        den = math.hypot(y2 - y1, x2 - x1)
        dist = num / den if den else 0
        if dist > max_dist:
            max_dist, index = dist, i
    if max_dist > epsilon:
        left = dp_simplify(points[:index+1], epsilon)
        right = dp_simplify(points[index:], epsilon)
        return left[:-1] + right
    else:
        return [start, end]

def find_gga_port(baudrate=115200, timeout=1, search_duration=3):
    print("Leter etter port som sender GGA-data...")
    ports = serial.tools.list_ports.comports()
    for p in ports:
        try:
            with serial.Serial(p.device, baudrate=baudrate, timeout=timeout) as ser:
                print(f"Tester {p.device}…")
                t0 = time.time()
                while time.time() - t0 < search_duration:
                    line = ser.readline().decode('ascii', errors='ignore').strip()
                    if line.startswith('$GNGGA'):
                        print(f"Fant GGA-data på {p.device}")
                        return p.device
        except Exception:
            pass
    print("Fant ingen gyldig port.")
    return None

def create_new_file(base_dir):
    now = datetime.now()
    day_dir = now.strftime("%Y-%m-%d")
    os.makedirs(os.path.join(base_dir, day_dir), exist_ok=True)
    fname = now.strftime("%H%M%S") + ".geojson"
    return os.path.join(base_dir, day_dir, fname), now

def write_geojson(path, coords, start_time):
    geojson = {
        "type":"FeatureCollection",
        "features":[{"type":"Feature",
                     "properties":{"start_time": start_time.strftime("%H:%M:%S"), "points":len(coords)},
                     "geometry":{"type":"LineString","coordinates": coords}
                     }]
    }
    with open(path, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON lagret: {path}")

def main():
    baudrate, tol = 115200, 0.5  # toleranse 0.5 m
    base_dir = "GPS_data"
    port = find_gga_port(baudrate)
    if not port:
        return

    raw_coords = []
    simplified = []
    file_path, start_time = create_new_file(base_dir)
    last_time = datetime.now()
    print(f"Lagrer til fil: {file_path}")

    with serial.Serial(port, baudrate=baudrate, timeout=1) as ser:
        print(f"Lytter på {port}… Ctrl+C for å stoppe.")
        try:
            while True:
                now = datetime.now()
                if raw_coords and (now - last_time > timedelta(seconds=10)):
                    simplified = dp_simplify(raw_coords, tol)
                    write_geojson(file_path, simplified, start_time)
                    raw_coords.clear()
                    simplified.clear()
                    file_path, start_time = create_new_file(base_dir)
                    last_time = now
                    print(f"Ny fil: {file_path}")

                line = ser.readline().decode('ascii', errors='ignore').strip()
                if line.startswith('$GNGGA'):
                    res = parse_gngga(line)
                    if res:
                        _, lat, lon = res
                        raw_coords.append([lon, lat])
                        last_time = now

        except KeyboardInterrupt:
            print("\nAvslutter…")
            if raw_coords:
                simplified = dp_simplify(raw_coords, tol)
                write_geojson(file_path, simplified, start_time)

if __name__ == "__main__":
    main()
