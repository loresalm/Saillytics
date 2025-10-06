
from datetime import time
import utils_gpx as utgpx

gpx_path = "regattas data/2025-06-11T14-45-11.582Z_Watersports_sailing.gpx"

start_time = time(18, 10, 0)  # 18:00:00
end_time = time(19, 30, 0)  # 18:00:00

points_with_time, speeds, speeds_clean, accelerations = utgpx.gpx_pipeline(gpx_path, start_time, end_time, smoothing_win=7, acc_trsh=2, downsample_s=8)

utgpx.plot_map(points_with_time, speeds_clean, output_path="outputs/track_map.html")

utgpx.plot_speed_acceleration(points_with_time, accelerations,
                              speeds, speeds_clean, "outputs/speed_acc.png")
