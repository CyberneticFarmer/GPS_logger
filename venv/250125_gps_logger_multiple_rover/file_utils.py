import os
import json
from datetime import datetime
import re
from pathlib import Path
"""
def create_new_file(base_dir):
    now = datetime.now()
    day_dir = "C:/Users/reidb/PycharmProjects/250609_KML_norgeskart/venv/260201_web/tracks" + now.strftime("%Y-%m-%d")
    os.makedirs(os.path.join(base_dir, day_dir), exist_ok=True)
    fname = now.strftime("%H%M%S") + ".js"
    return os.path.join(base_dir, day_dir, fname), now
"""

def create_new_file(base_dir, rover, sys):
    now = datetime.now()
    print(sys)
    if (sys == "Windows"):
        day_dir = "C:/Users/reidb/PycharmProjects/250609_KML_norgeskart/venv/260201_web/tracks/" + rover + "/"+ now.strftime("%Y-%m-%d")
        print("HELLO")
    elif sys == "Linux":
        day_dir = "/var/www/html/rover/tracks/" + rover + "/"+ now.strftime("%Y-%m-%d")
    else:
        print("FEIL ved oppretting av filnavn i create_new_file")
        exit()

    os.makedirs(os.path.join(base_dir, day_dir), exist_ok=True)
    fname = now.strftime("%H%M%S") + ".js"
    return os.path.join(base_dir, day_dir, fname), now

def write_geojson12(path, coords, start_time):
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

def test2():
    print("dette virker")

def write_geojson(path, rover, track_name, length):
    coords = rover["coor"]
    delta = rover["last_received"] - rover["start_time"]
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    track_time = f"{hours}h {minutes}m {seconds}s"
    avg_speed = round((length/1000) / (total_seconds/3600),1)

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "start_time": rover["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "points": len(coords),
                    "end_time": rover["last_received"].strftime("%Y-%m-%d %H:%M:%S"),
                    "track_time": track_time,
                    "track_length": round(length),
                    "avg_speed": avg_speed
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            }
        ]
    }

    js_content = f"export const track = {{\n  name: {json.dumps(track_name)},\n  geojson: {json.dumps(geojson, indent=2)}\n}};\n"

    with open(path, "w") as f:
        f.write(js_content)

    print(f"JS GeoJSON saved: {path}")


def update_track_index(
        index_path,
        date_str,
        track_id,
        label,
        state_rover,
        rover
):
    """
    Updates trackIndex.js by adding a new track entry.
    """
    print(rover)

    # If file doesn't exist, create a new index
    if not os.path.exists(index_path):
        index_data = {}
    else:
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract JS object
        match = re.search(r"export const trackIndex\s*=\s*(\{.*\});", content, re.S)
        if not match:
            raise ValueError("Invalid trackIndex.js format")

        index_data = json.loads(match.group(1))

    # Ensure date bucket exists
    if date_str not in index_data:
        index_data[date_str] = []

    # Prevent duplicate IDs
    if any(t["id"] == track_id for t in index_data[date_str]):
        print(f"Track id '{track_id}' already exists for {date_str}")
        return
    track_path = "./tracks/" + rover + "/" + date_str + "/" + track_id.replace("-","") + ".js" # ./tracks/2025-12-21\\160644.js"
    # Append new entry
    index_data[date_str].append({
        "id": track_id,
        "label": label,
        "path": track_path,
        "state": str(state_rover)
    })

    # Write back JS file
    js_output = (
            "export const trackIndex = "
            + json.dumps(index_data, indent=2)
            + ";\n"
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(js_output)

    print(f"trackIndex.js updated: {track_id}")




def write_positions_to_file(positions, path):
    """
    positions: [[lat, lng], [lat, lng], ...]
    path: f.eks "vehicles.js"
    """

    lines = []
    lines.append("// vehicles.js")
    lines.append("const vehicles = [")

    for i, (lat, lng) in enumerate(positions, start=1):
        lines.append(
            f'    {{ id: {i}, name: "Bil {i}", lat: {lat}, lng: {lng} }},'
        )

    # Fjern komma på siste element
    if len(positions) > 0:
        lines[-1] = lines[-1].rstrip(",")

    lines.append("];")

    content = "\n".join(lines)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
