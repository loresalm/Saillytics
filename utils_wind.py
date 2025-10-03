import json
import folium
import math

# Convert wind direction in degrees to endpoint coordinates
def endpoint(lat, lon, bearing, speed, scale=0.01):
    # simple approximation, scale adjusts arrow length
    rad = math.radians(bearing)
    return lat + scale * speed * math.sin(rad), lon + scale * speed * math.cos(rad)


def get_wind(wind_path, date, target_time):
    with open(wind_path) as f:
        data = json.load(f)
    records = data[date]["records"]
    # Find the record for that time
    record = next((r for r in records if r["Time"] == target_time), None)

    if record:
        speed = record["Wind Speed (kts)"]
        dir_str = record["Wind Direction"].split("°")[0]
        deg = float(dir_str)
        
        return speed, dir_str, deg
    else:
        print(f"No wind record found for time {target_time}")
        return None, None, None


def plot_wind(m, lat, lon, speed, deg):
    end_lat, end_lon = endpoint(lat, lon, deg, speed)

    folium.PolyLine([(lat, lon), (end_lat, end_lon)],
                    color="blue",
                    weight=2,
                    opacity=0.7).add_to(m)
    return m