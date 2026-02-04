import serial
import threading
from datetime import datetime, timedelta
import math
import platform

system_os = platform.system()

from serial_utils import find_gga_port
from geo_utils import *
from file_utils import create_new_file, write_geojson, update_track_index, write_positions_to_file

# Global kontrollvariabler
manual_save_requested = False
terminate_requested = False
path_trackIndex = "C:/Users/reidb/PycharmProjects/250609_KML_norgeskart/venv/251220_webvisning/tracks/trackIndex.js"
data = {}
base_dir = "GPS_data"
barn_coor = [61.185881, 5.987860]
timeout_lagring = 60
## Rovers
rovers = {
    "1" : "Muli",
    "2" : "Metrac",
    "3" : "Fiat",
    "4" : "Massey",
    "5" : "Tesla"
}

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
def save_track(id):
    if data[id]["coor"] is not None and data[id]["coor"] and (len(data[id]["coor"]) > 2):
        file_path, start_time = create_new_file(base_dir, rovers[id], system_os)
        print(file_path)
        write_geojson(file_path, data[id], "test", calculate_path_length(data[id]["coor"]))
        # Oppdater trackindex
        #print(file_path)
        indexPath = file_path.split(rovers[id])[0] + rovers[id] + "/trackIndex.js"
        update_track_index(indexPath, str(start_time)[0:10], str(start_time)[11:19].replace(":", "-"), str(start_time)[11:19].replace(":", "-"), data[id]["state"], rovers[id])

        # Tøm buffer og oppdater siste mottatte tid
    data[id]["last_received"] = datetime.now()
    data[id]["coor"].clear()

def save_all_track():
    print("lagrer alla spor")
    for ids in data:
        save_track(ids)

def check_timeout_saving():
    for ids in data:
        if data[ids]["last_received"] is not None:
            #print("Delta Time " + str(ids) + ": " + str(datetime.now() - data[ids]["last_received"]))
            if (datetime.now() - data[ids]["last_received"] > timedelta(seconds=timeout_lagring) ):
                print("Lang tid i mellom")
                ## Her skal det lagres for den aktuelle roveren
                save_track(ids)


def main():
    print( system_os)
    global manual_save_requested, terminate_requested
    baudrate, tol = 9600, 0.005  # 0.5 m
    raw_coords = []
    last_saved_count = 0
    #file_path, start_time = create_new_file(base_dir)
    last_received_time = datetime.now()
    #print(f"Lagrer til fil: {file_path}")
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
                if len(line) > 5:
                    #print(line)

                    if line[1:6] == ",GGA,":
                        now = datetime.now()
                        id = line[0]
                        last_received_time = now
                        res = parse_gngga(line[2:])
                        print(res)
                        if id not in data:
                            data[id] = {"coor":[] , "last_received": None}
                        if res:
                            if not data[id]["coor"]:
                                data[id]["coor"].append([res[2], res[1]])
                                data[id]["last_received"] = now
                                data[id]["start_time"] = now
                                data[id]["state"] = line[-1]
                            else:
                                dist = haversine_distance(res[2], res[1], data[id]["coor"][-1][0], data[id]["coor"][-1][1])
                                #print("Distanse " + str(dist))
                                if dist >= 20:
                                    data[id]["coor"].append([res[2], res[1]])
                                    data[id]["last_received"] = now
                                    #print(data)
                ## Check how long since last received

                if manual_save_requested:
                    save_all_track()
                    manual_save_requested = False
                check_timeout_saving()
                """
                if data[1] is not None:
                    if ( check_muli_emptying(data[1]) ): # Check if the tractor are in the barn and emptying hay
                        save_track(1)
                """


        except KeyboardInterrupt:
            print("\nAvslutter med Ctrl+C…")

    # Ved avslutning
    save_all_track()

if __name__ == "__main__":
    main()
