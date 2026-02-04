import serial
import threading
from datetime import datetime, timedelta

from serial_utils import find_gga_port
from geo_utils import parse_gngga, haversine_distance, is_almost_straight
from file_utils import create_new_file, write_geojson, update_track_index, write_positions_to_file

# Global kontrollvariabler
manual_save_requested = False
terminate_requested = False
path_trackIndex = "C:/Users/reidb/PycharmProjects/250609_KML_norgeskart/venv/251220_webvisning/tracks/trackIndex.js"
def user_input_thread():
    global manual_save_requested, terminate_requested
    while True:
        cmd = input().strip().lower()
        if cmd == "l":
            manual_save_requested = True
            print("LAGRE")
        elif cmd == "stopp":
            terminate_requested = True
            break
        else:
            print("Ukjent kommando. Bruk 'l' eller 'stopp'.")

def main():
    global manual_save_requested, terminate_requested
    baudrate, tol = 115200, 0.005  # 0.5 m
    base_dir = "GPS_data"
    raw_coords = []
    last_saved_count = 0
    file_path, start_time = create_new_file(base_dir)
    last_received_time = datetime.now()
    print(f"Lagrer til fil: {file_path}")
    print("Skriv 'lagre' for å lagre manuelt, eller 'stopp' for å avslutte.")
    port = find_gga_port(baudrate)
    if not port:
        return


    # Start tråd for å lytte på brukerens inndata lagre
    threading.Thread(target=user_input_thread, daemon=True).start()

    with serial.Serial(port, baudrate=baudrate, timeout=1) as ser:
        print(f"Lytter på {port}… Ctrl+C eller 'stopp' for å avslutte.")
        try:
            while not terminate_requested:
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
                            #write_positions_to_file([[lon,lat]],"C:/Users/reidb/PycharmProjects/250609_KML_norgeskart/venv/251220_webvisning/live/vehicles.js")
                        else:
                            prev_lon, prev_lat = raw_coords[-1]
                            dist = haversine_distance(lat, lon, prev_lat, prev_lon)
                            print(str(res) + " " + str(dist))
                            if dist >= 10:
                                if len(raw_coords) >= 2:
                                    if is_almost_straight(raw_coords[-2], raw_coords[-1], new_point):
                                        raw_coords.pop()
                                        print("Fjerner koordinat")
                                raw_coords.append(new_point)

                # Automatisk lagring etter inaktivitet
                if (datetime.now() - last_received_time > timedelta(seconds=10) ) or manual_save_requested:
                    if (len(raw_coords) > last_saved_count):
                        write_geojson(file_path, raw_coords, start_time)
                        #update_track_index("trackIndex.js", "25-12-20", "t54", "Hello23", "./tracks/2025-01-11/track5.js")
                        #update_track_index("trackIndex.js", file_path, start_time, "Hello23", file_path)
                        ##print(file_path)
                        ##print(start_time[0:8])
                        update_track_index("C:/Users/reidb/PycharmProjects/250609_KML_norgeskart/venv/251220_webvisning/tracks/trackIndex.js", str(start_time)[0:10], str(start_time)[11:19].replace(":", "-"), str(start_time)[11:19].replace(":", "-"), file_path)
                        update_track_index("trackIndex.js", str(start_time)[0:10], str(start_time)[11:19].replace(":", "-"), str(start_time)[11:19].replace(":", "-"), file_path)

                    #tes




                        print(f"Lagrer {len(raw_coords)} punkter til {file_path} (automatisk)")
                        raw_coords.clear()
                        last_saved_count = 0
                    file_path, start_time = create_new_file(base_dir)
                    last_received_time = datetime.now()
                    manual_save_requested = False
                    print(f"Ingen mottak på 10 sek – ny fil startet: {file_path}")

        except KeyboardInterrupt:
            print("\nAvslutter med Ctrl+C…")

    # Ved avslutning
    if len(raw_coords) > last_saved_count:
        write_geojson(file_path, raw_coords, start_time)
        print(f"Lagrer {len(raw_coords)} punkter til {file_path} ved avslutning.")
    else:
        print("Ingen nye punkter siden forrige lagring.")

if __name__ == "__main__":
    main()
