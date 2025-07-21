import serial
import serial.tools.list_ports
import time

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
