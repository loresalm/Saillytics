import folium  # type: ignore
import utils_wind as utw

wind_path = "inputs/wind/wind_data.json"
date = "2025-05-10"
target_time = "16:00"

speed, dir_str, deg = utw.get_wind(wind_path, date, target_time)

# Create map centered on a sample location
m = folium.Map(location=[52.45, 13.18], zoom_start=12)

lat, lon = 52.42, 13.18  # replace with boat location


utw.plot_wind(m, lat, lon, speed, deg)

m.save("outputs/plots/wind_map.html")
