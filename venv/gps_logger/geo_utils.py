import math

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
    return R * c * 1000 * 100  # i centimeter

def is_almost_straight(p1, p2, p3, angle_tolerance=5):
    def bearing(a, b):
        dy = b[1] - a[1]
        dx = b[0] - a[0]
        return math.degrees(math.atan2(dy, dx))

    angle1 = bearing(p1, p2)
    angle2 = bearing(p2, p3)
    diff = abs(angle1 - angle2) % 360
    if diff > 180:
        diff = 360 - diff
    return diff < angle_tolerance
