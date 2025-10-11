import gpxpy  # type: ignore
import folium  # type: ignore
import pytz  # type: ignore
from geopy.distance import geodesic  # type: ignore
import numpy as np  # type: ignore
import matplotlib.cm as cm  # type: ignore
import matplotlib.colors as mcolors  # type: ignore
import matplotlib.pyplot as plt  # type: ignore


def get_gpx_points(gpx_path, start_time, end_time):
    # Load GPX file
    with open(gpx_path, "r") as f:
        gpx = gpxpy.parse(f)

    berlin = pytz.timezone("Europe/Berlin")

    # Extract points and times after start_time
    points_with_time = []
    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                local_time = p.time.astimezone(berlin).time()
                if local_time >= start_time and local_time <= end_time:
                    points_with_time.append((p.latitude, p.longitude, p.time))

    if len(points_with_time) < 2:
        raise ValueError(f"Not enough GPX points after {start_time}")

    return points_with_time


def downsample_gpx(points_with_time, interval_seconds=30):
    if not points_with_time:
        return []

    downsampled = [points_with_time[0]]  # always keep first point
    last_time = points_with_time[0][2]

    for pt in points_with_time[1:]:
        current_time = pt[2]
        if (current_time - last_time).total_seconds() >= interval_seconds:
            downsampled.append(pt)
            last_time = current_time

    return downsampled


def get_velocity(points_with_time):
    # Compute speeds (m/s) between consecutive points
    speeds = []
    for i in range(1, len(points_with_time)):
        p1 = points_with_time[i-1]
        p2 = points_with_time[i]
        dist_m = geodesic(p1[:2], p2[:2]).meters  # distance in meters
        delta_t = (p2[2] - p1[2]).total_seconds()  # time difference in seconds
        speed = dist_m / delta_t if delta_t > 0 else 0
        speeds.append(speed)
    [s * 1.94384 for s in speeds]
    return speeds


def get_accelerations(points_with_time):
    # Convert GPX times safely to plain Python datetimes
    times = [p[2].replace(tzinfo=None) for p in points_with_time[1:]]
    speeds = get_velocity(points_with_time)
    accelerations = []
    for i in range(1, len(speeds)):
        dv = speeds[i] - speeds[i-1]
        dt = (times[i] - times[i-1]).total_seconds()
        accelerations.append(dv/dt if dt > 0 else 0)
    return accelerations


def clean_speeds(points_with_time, speeds, threshold_k=3):
    """
    Small threshold_k (e.g., 2) → more aggressive cleaning
    (will smooth out more data, might remove valid sharp turns or gusts).

    Large threshold_k (e.g., 5) → more tolerant, only removes extreme spikes.
    """

    times = [p[2].replace(tzinfo=None) for p in points_with_time[1:]]

    # Compute accelerations
    acc = get_accelerations(points_with_time)
    mean, std = np.mean(acc), np.std(acc)
    threshold = mean + threshold_k * std

    speeds_clean = speeds.copy()
    for i in range(1, len(speeds)-1):
        dv = speeds[i] - speeds[i-1]
        dt = (times[i] - times[i-1]).total_seconds()
        a = dv/dt if dt > 0 else 0
        if abs(a) > threshold:  # outlier
            # interpolate between neighbors
            speeds_clean[i] = (speeds[i-1] + speeds[i+1]) / 2
    return speeds_clean


def smooth_signal(values, window_size=5):
    if window_size < 2:
        return values
    kernel = np.ones(window_size) / window_size
    return np.convolve(values, kernel, mode="same")


def normalize(values):
    vmin, vmax = min(values), max(values)
    if vmax == vmin:  # avoid division by zero
        return [0.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


def gpx_pipeline(gpx_path, start_t, end_t, smooth_win=7,
                 acc_trsh=2, downsamp_s=8):

    points_with_time = get_gpx_points(gpx_path, start_t, end_t)
    points_with_time = downsample_gpx(points_with_time, downsamp_s)
    speeds = get_velocity(points_with_time)
    accelerations = get_accelerations(points_with_time)
    speeds_clean = clean_speeds(points_with_time, speeds, threshold_k=acc_trsh)
    speeds_clean = smooth_signal(speeds_clean, window_size=smooth_win)

    speeds_clean_norm = normalize(speeds_clean)

    return (points_with_time, speeds, speeds_clean,
            speeds_clean_norm, accelerations)


def plot_map(points_with_time, speeds, output_path="track_map.html"):
    """
    Plot GPX track with speed-based coloring and dots at every point.

    points_with_time: list of tuples [(lat, lon, datetime), ...]
    speeds: list of normalized speeds [0,1] corresponding to points_with_time
    output_path: path to save the HTML map
    """
    # Create Folium map centered on first point
    m = folium.Map(location=points_with_time[0][:2], zoom_start=14)

    # Colormap: red=fast, green=slow
    cmap = cm.get_cmap("RdYlGn_r")

    # Add colored line segments
    for i in range(1, len(points_with_time)):
        segment = [points_with_time[i-1][:2], points_with_time[i][:2]]
        color = mcolors.to_hex(cmap(speeds[i-1]))
        folium.PolyLine(segment, color=color, weight=5).add_to(m)

    # Add a dot for every GPX point (no outline)
    for pt in points_with_time:
        folium.CircleMarker(
            location=pt[:2],
            radius=1,
            color=None,         # no border
            weight=0,
            fill=True,
            fill_color="black",
            fill_opacity=0.8
        ).add_to(m)

    # Save to HTML (open in browser to view)
    m.save(output_path)


def plot_speed_acceleration(points_with_time, accelerations, speeds_raw,
                            speeds_clean, output_path_plot):

    # Extract times
    times = [p[2].replace(tzinfo=None) for p in points_with_time[1:]]

    # Create figure with 3 subplots sharing x-axis
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(20, 10), sharex=True)

    # Raw speed
    ax1.plot(times, speeds_raw, "-o", color="blue",
             markersize=3, label="Raw Speed (knots)")
    ax1.set_ylabel("Speed (knots)")
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Acceleration
    ax2.plot(times[1:], accelerations, "-o", color="red",
             markersize=3, label="Acceleration (m/s²)")
    ax2.set_ylabel("Acceleration (m/s²)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    # Cleaned speed
    ax3.plot(times, speeds_clean, "-o", color="green",
             markersize=3, label="Cleaned Speed (knots)")
    ax3.set_ylabel("Cleaned Speed (knots)")
    ax3.legend()
    ax3.grid(True, linestyle="--", alpha=0.5)

    # Common X-axis label
    ax3.set_xlabel("Time")

    plt.suptitle("Speed, Acceleration, and Cleaned Speed over Time")
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)  # make room for suptitle
    plt.savefig(output_path_plot, dpi=150)
    plt.close(fig)
