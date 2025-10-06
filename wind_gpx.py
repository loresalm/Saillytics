from datetime import time
import utils_gpx as utgpx
import folium
import utils_wind as utw

gpx_path = "regattas data/2025-06-04T14-50-42.569Z_Watersports_sailing.gpx"

start_time = time(17, 57, 0)  # 18:00:00
end_time = time(19, 30, 0)  # 18:00:00

points_with_time, speeds, speeds_clean, accelerations = utgpx.gpx_pipeline(gpx_path, start_time, end_time, smoothing_win=7, acc_trsh=2, downsample_s=18)


wind_path = "wind_data.json"
date = "2025-06-04"
annotated_points = utw.assign_wind_to_track(points_with_time, wind_path, date)

for pt in annotated_points[:5]:
    print(pt)

utw.plot_map_with_wind(annotated_points, speeds_clean, output_path="track_map_wind.html")