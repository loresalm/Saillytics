
import gpxpy
import folium
from datetime import datetime, time
import pytz
from geopy.distance import geodesic
import numpy as np
import matplotlib.pyplot as plt

import utils_gpx as utgpx

gpx_path = "regattas data/2025-06-11T14-45-11.582Z_Watersports_sailing.gpx"

start_time = time(18, 10, 0)  # 18:00:00
end_time = time(19, 30, 0)  # 18:00:00

points_with_time = utgpx.get_gpx_points(gpx_path, start_time, end_time)
points_with_time = utgpx.downsample_gpx(points_with_time, 8)
speeds = utgpx.get_velocity(points_with_time)
accelerations = utgpx.get_accelerations(points_with_time)
speeds_clean = utgpx.clean_speeds(points_with_time, speeds, threshold_k=2)
speeds_clean = utgpx.smooth_signal(speeds_clean, window_size=7)
speeds_clean = utgpx.normalize(speeds_clean)

utgpx.plot_map(points_with_time, speeds_clean, output_path="outputs/track_map.html")

utgpx.plot_speed_acceleration(points_with_time, accelerations,
                              speeds, speeds_clean, "outputs/speed_acc.png")
