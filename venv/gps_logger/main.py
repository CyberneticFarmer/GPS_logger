import serial
from datetime import datetime, timedelta

from serial_utils import find_gga_port
from geo_utils import parse_gngga, haversine_distance, is_almost_straight
from file_utils import create_new_file, write_geojson

def main():
    baudrate, tol = 115200, 0.005  # 0.5 m
    base_dir = "GPS_data"
    port = find_gga_port(baudrate)
    if not port:
        return

    raw_coords = []
    file_path, start_time = create_new_file(base_dir)
    last_received_time = datetime.now()
    print(f"Lagrer til fil: {file_path}")

    with serial.Serial(port, baudrate=baudrate, timeout=1) as ser:
        print(f"Lytter på {port}… Ctrl+C for å stoppe.")
        try:
            while True:
                line = ser.readline().decode('ascii', errors='ignore').strip()
                if line.startswith('$GNGGA'):
                    now = datetime.now()
                    last_received_time = now

                    res = parse_gngga(line)
                    if res:
                        _, lat, lon = res
                        new_point = [lon, lat]
                        if not raw_coords:
                            raw_coords.append(new_point)
                        else:
                            prev_lon, prev_lat = raw_coords[-1]
                            dist = haversine_distance(lat, lon, prev_lat, prev_lon)
                            print(str(res) + " " + str(dist))
                            if dist >= 0.02:
                                if len(raw_coords) >= 2:
                                    if is_almost_straight(raw_coords[-2], raw_coords[-1], new_point):
                                        raw_coords.pop()
                                raw_coords.append(new_point)

                if (datetime.now() - last_received_time > timedelta(seconds=10)):
                    if raw_coords:
                        write_geojson(file_path, raw_coords, start_time)
                    file_path, start_time = create_new_file(base_dir)
                    last_received_time = datetime.now()
                    print(f"Ingen mottak på 10 sek – ny fil startet: {file_path}")

        except KeyboardInterrupt:
            print("\nAvslutter…")
            if raw_coords:
                write_geojson(file_path, raw_coords, start_time)

if __name__ == "__main__":
    main()
