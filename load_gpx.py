
from datetime import time
import utils_gpx as utgpx

gpx_path = "inputs/regattas/2025-06-11T14-45-11.582Z_Watersports_sailing.gpx"

start_time = time(18, 10, 0)  # 18:00:00
end_time = time(19, 30, 0)  # 18:00:00

pt, s, s_clean, s_clean_norm, acc = utgpx.gpx_pipeline(gpx_path,
                                                       start_time,
                                                       end_time,
                                                       smooth_win=7,
                                                       acc_trsh=2,
                                                       downsamp_s=8)

utgpx.plot_map(pt, s_clean_norm, output_path="outputs/plots/track_map.html")

utgpx.plot_speed_acceleration(pt, acc, s, s_clean_norm,
                              "outputs/plots/speed_acc.png")
