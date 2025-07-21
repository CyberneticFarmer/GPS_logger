import os
import json
from datetime import datetime

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
