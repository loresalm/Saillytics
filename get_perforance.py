import utils_wind as utw
import utils_gpx as utgpx
from datetime import time
from datetime import datetime
import matplotlib.pyplot as plt   # type: ignore
import numpy as np   # type: ignore


def compute_wind_boat_dataset(p_t, s_clean, wind_data):
    """
    p_t: list of (lat, lon, datetime)
    s_clean: list of cleaned speeds (same length as p_t)
    wind_data: list of dicts with 'time' (HH:MM), 'speed', 'deg'
    """

    # Convert wind times to minutes since midnight
    wind_times = np.array([int(datetime.strptime(w["time"], "%H:%M").hour)
                           * 60 +
                           int(datetime.strptime(w["time"], "%H:%M").minute)
                           for w in wind_data])
    wind_speeds = np.array([w["speed"] for w in wind_data])
    wind_dirs = np.array([w["deg"] for w in wind_data])

    results = []

    for (lat, lon, t), v in zip(p_t, s_clean):
        # Time of boat point in minutes since midnight
        boat_min = t.hour * 60 + t.minute + t.second / 60

        # Linear interpolation of wind speed and direction
        w_speed = np.interp(boat_min, wind_times, wind_speeds)
        w_dir = np.interp(boat_min, wind_times, wind_dirs)

        # Estimate boat heading from consecutive positions if possible
        idx = p_t.index((lat, lon, t))
        if idx > 0:
            lat0, lon0, _ = p_t[idx - 1]
            dx, dy = lon - lon0, lat - lat0
            boat_heading = (np.degrees(np.arctan2(dx, dy)) + 360) % 360
        else:
            boat_heading = np.nan

        # Compute wind_boat_angle (difference between headings)
        if not np.isnan(boat_heading):
            wind_boat_angle = (w_dir - boat_heading + 360) % 360
        else:
            wind_boat_angle = np.nan

        # Compute speed ratio
        speed_ratio = v / w_speed if w_speed != 0 else np.nan

        results.append({
            "time": t,
            "lat": lat,
            "lon": lon,
            "boat_speed": float(v),
            "wind_speed": float(w_speed),
            "boat_heading": float(boat_heading),
            "wind_dir": float(w_dir),
            "wind_boat_angle": float(wind_boat_angle),
            "speed_ratio": float(speed_ratio)
        })

    return results


def plot_speed_ratio_vs_angle(dataset, out_file="speed_ratio_vs_angle.png"):
    angles = [d["wind_boat_angle"]
              for d in dataset if d["wind_boat_angle"] is not None]
    ratios = [d["speed_ratio"]
              for d in dataset if d["speed_ratio"] is not None]

    plt.figure(figsize=(6, 4))
    plt.scatter(angles, ratios, c=ratios, cmap="jet", alpha=0.7)
    plt.xlabel("Wind–Boat Angle (°)")
    plt.ylabel("Speed Ratio (boat/wind)")
    plt.title("Speed Ratio vs. Wind–Boat Angle")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out_file, dpi=150)
    plt.close()


def plot_polar_speed_ratio(dataset, out_file="polar_speed_ratio.png"):
    angles = np.radians([d["wind_boat_angle"] for d in dataset])
    ratios = np.array([d["speed_ratio"] for d in dataset])

    _, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.scatter(angles, ratios, c=ratios, cmap="jet", s=50, alpha=0.8)

    ax.set_theta_zero_location("N")   # 0° at top
    ax.set_theta_direction(-1)        # clockwise
    ax.set_rlabel_position(30)
    ax.grid(True, color="#000000", linestyle="-", linewidth=1.2)
    ax.set_title("Speed Ratio vs Wind–Boat Angle", pad=20)

    plt.tight_layout()
    plt.savefig(out_file, dpi=150, bbox_inches="tight")
    plt.close()


wind_path = "wind_data.json"
gpx_path = "regattas data/2025-06-11T14-45-11.582Z_Watersports_sailing.gpx"
date = "2025-05-10"
target_time = "16:00"

start_time = time(18, 10, 0)  # 18:00:00
end_time = time(19, 30, 0)  # 18:00:00

wind_data = utw.get_wind_range(wind_path, date, time(18, 0, 0), time(20, 0, 0))
for entry in wind_data:
    print(entry)

p_t, s, s_clean, accel = utgpx.gpx_pipeline(gpx_path, start_time,
                                            end_time, smoothing_win=7,
                                            acc_trsh=2, downsample_s=8,
                                            normalize_speed=False)

dataset = compute_wind_boat_dataset(p_t, s_clean, wind_data)
plot_speed_ratio_vs_angle(dataset)
plot_polar_speed_ratio(dataset)

"""
print("points with times")
print(p_t[:5])
print("speeds")
print(s[:5])
print("cleaned speeds")
print(s_clean[:5])
print("accelerations")
print(accel[:5])
"""
