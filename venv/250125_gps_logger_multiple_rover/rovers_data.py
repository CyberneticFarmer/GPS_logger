
from datetime import datetime, timedelta

print("hello")


def test1():
    print("test5")


def add_point(id, lat, lng, data):
    if id not in data:
        data[id] = {"coor":[] , "last_received": None}
    data[id]["coor"].append([lat, lng])
    data[id]["last_received"] = datetime.now()
    return data




