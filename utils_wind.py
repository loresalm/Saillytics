import json
import folium  # type: ignore
import math
from datetime import datetime
import matplotlib.cm as cm  # type: ignore
import matplotlib.colors as mcolors  # type: ignore


# Convert wind direction in degrees to endpoint coordinates
def winddir2coord(lat, lon, bearing, speed, scale=0.01):
    # simple approximation, scale adjusts arrow length
    rad = math.radians(bearing)
    return (lat + scale * speed * math.sin(rad),
            lon + scale * speed * math.cos(rad))


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


def get_wind_range(wind_path, date, start_time, end_time):
    with open(wind_path) as f:
        data = json.load(f)

    records = data.get(date, {}).get("records", [])
    results = []

    for r in records:
        t = datetime.strptime(r["Time"], "%H:%M").time()
        if start_time <= t <= end_time:
            deg_str = r["Wind Direction"].split("°")[0]
            results.append({
                "date": date,
                "time": r["Time"],
                "speed": r["Wind Speed (kts)"],
                "dir_str": deg_str,
                "deg": float(deg_str)
            })
    return results


def load_wind_records(wind_path, date):
    with open(wind_path) as f:
        data = json.load(f)
    records = data[date]["records"]

    # Convert wind records to datetime + numeric values
    times, speeds, dirs_deg = [], [], []
    for r in records:
        t = datetime.strptime(f"{date} {r['Time']}", "%Y-%m-%d %H:%M")
        times.append(t)
        speeds.append(float(r["Wind Speed (kts)"]))
        dirs_deg.append(float(r["Wind Direction"].split("°")[0]))
    return times, speeds, dirs_deg


def interpolate_wind(times, speeds, dirs_deg, target_time):
    """
    Linearly interpolate wind speed and direction for target_time
    between the two nearest hourly records.
    """

    if target_time <= times[0]:
        return speeds[0], dirs_deg[0]
    if target_time >= times[-1]:
        return speeds[-1], dirs_deg[-1]

    for i in range(1, len(times)):
        if times[i-1] <= target_time <= times[i]:
            # time fraction between the two hourly records
            total = (times[i] - times[i-1]).total_seconds()
            frac = (target_time - times[i-1]).total_seconds() / total

            # linear interpolation
            speed = speeds[i-1] + frac * (speeds[i] - speeds[i-1])

            # handle wind direction interpolation (circular variable!)
            d1, d2 = dirs_deg[i-1], dirs_deg[i]
            diff = (d2 - d1 + 180) % 360 - 180  # shortest angular distance
            deg = (d1 + frac * diff) % 360

            return speed, deg
    return None, None


def assign_wind_to_track(points_with_time, wind_path, date):
    """
    For each GPX point, assign interpolated wind speed and direction.
    Returns list of tuples: (lat, lon, time, wind_speed, wind_deg)
    """
    times, speeds, dirs_deg = load_wind_records(wind_path, date)

    annotated = []
    for lat, lon, t in points_with_time:
        speed, deg = interpolate_wind(times, speeds,
                                      dirs_deg, t.replace(tzinfo=None))
        annotated.append((lat, lon, t, speed, deg))
    return annotated


def plot_wind(m, lat, lon, speed, deg):
    end_lat, end_lon = winddir2coord(lat, lon, deg, speed)

    folium.PolyLine([(lat, lon), (end_lat, end_lon)],
                    color="blue",
                    weight=2,
                    opacity=0.7).add_to(m)
    return m


def endpoint(lat, lon, deg, dist_nm):
    """Compute endpoint given start, bearing (deg),
    and distance in nautical miles."""
    R = 3440.065  # Earth radius in nautical miles
    d = dist_nm / R
    lat1, lon1 = math.radians(lat), math.radians(lon)
    brng = math.radians(deg)

    lat2 = math.asin(math.sin(lat1) * math.cos(d) +
                     math.cos(lat1) * math.sin(d) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d) * math.cos(lat1),
                             math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


def normalize(values):
    """
    Normalize list of values to range [0, 1].
    min(values) -> 0, max(values) -> 1
    """
    vmin, vmax = min(values), max(values)
    if vmax == vmin:  # avoid division by zero if constant
        return [0.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


def plot_map_with_wind(annotated_points, speeds, output_path="track_map.html"):
    """
    Plot GPX track with speed-colored line and wind arrows.

    annotated_points: [(lat, lon, datetime, wind_speed, wind_deg), ...]
    speeds: list of normalized sailing speeds [0,1]
    """
    m = folium.Map(location=annotated_points[0][:2], zoom_start=14)
    cmap_speed = cm.get_cmap("RdYlGn_r")

    # --- Normalize wind speed between 0-1 ---
    wind_speeds = [p[3] for p in annotated_points if p[3] is not None]
    wind_norm = normalize(wind_speeds)
    [print(w) for w in wind_norm]

    # --- Sailing track (colored by boat speed) ---
    for i in range(1, len(annotated_points)):
        segment = [annotated_points[i-1][:2], annotated_points[i][:2]]
        color = mcolors.to_hex(cmap_speed(speeds[i-1]))
        folium.PolyLine(segment, color=color, weight=5).add_to(m)
        folium.PolyLine(segment, color="black", weight=1,
                        opacity=0.8, dash_array="5,5").add_to(m)

    # --- Points and Wind Arrows ---
    for (lat, lon, _, w_speed, w_deg), wn in zip(annotated_points, wind_norm):

        # Dot
        folium.CircleMarker(location=(lat, lon), radius=2,
                            color=None, fill=True,
                            fill_color="black").add_to(m)
        if w_speed is not None and w_deg is not None:

            # Scaled arrow (length ~ wind speed)
            end_lat, end_lon = endpoint(lat, lon, w_deg, wn * 0.05)
            folium.PolyLine([(lat, lon), (end_lat, end_lon)],
                            color="black", weight=2, opacity=0.8).add_to(m)

            # Standardized arrow (length = constant)
            end_lat2, end_lon2 = endpoint(lat, lon, w_deg, 0.05)
            folium.PolyLine([(lat, lon), (end_lat2, end_lon2)],
                            color="black", weight=1,
                            opacity=0.8, dash_array="5,5").add_to(m)

    m.save(output_path)
