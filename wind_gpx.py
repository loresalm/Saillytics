from datetime import time
import utils_gpx as utgpx
import utils_wind as utw

gpx_path = "inputs/regattas/2025-06-04T14-50-42.569Z_Watersports_sailing.gpx"

start_time = time(17, 57, 0)  # 18:00:00
end_time = time(19, 30, 0)  # 18:00:00

pt, s, s_clean, s_clean_norm, acc = utgpx.gpx_pipeline(gpx_path,
                                                       start_time,
                                                       end_time,
                                                       smooth_win=7,
                                                       acc_trsh=2,
                                                       downsamp_s=8)


wind_path = "inputs/wind/wind_data.json"
date = "2025-06-04"
annotated_points = utw.assign_wind_to_track(pt, wind_path, date)

utw.plot_map_with_wind(annotated_points, s_clean_norm,
                       output_path="outputs/plots/track_map_wind.html")
