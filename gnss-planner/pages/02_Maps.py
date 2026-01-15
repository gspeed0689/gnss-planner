from pages import satellite_cache
import streamlit as st
from skyfield.api import EarthSatellite, load, wgs84
import requests
import pytz
import folium
import streamlit_folium as stf
from datetime import datetime, timedelta
import pandas as pd
import geopandas as gpd
from shapely import LineString
import numpy as np
import pathlib
from io import StringIO

for k, v in st.session_state.items():
    st.session_state[k] = v

st.set_page_config(layout="wide")

st.title("Satellite Maps")

ts = load.timescale()

celeste_tle_gnss = "https://celestrak.org/NORAD/elements/gp.php?GROUP=gnss&FORMAT=tle"

def get_GNSS_TLE():
    satcache = satellite_cache.get_last_cache_record()
    # st.code(satcache)
    if satcache:
        if satcache.access_datetime > datetime.now() - timedelta(days=3):
            return satcache.content
        else:
            r = requests.get(celeste_tle_gnss)
            tle = r.content.decode(r.encoding)
            satellite_cache.create_cache_record(datetime.now(), tle)
            return tle
    else:
        r = requests.get(celeste_tle_gnss)
        tle = r.content.decode(r.encoding)
        satellite_cache.create_cache_record(datetime.now(), tle)
        return tle
    
constellations = ["NAVSTAR", "GLONASS", "GALILEO", "BEIDOU", "QZSS", "OTHER"]
satellites = {x: {} for x in constellations}

c = 0
for line in StringIO(get_GNSS_TLE()).readlines():
    if c == 0:
        satellite_name = line
        while satellite_name[-1] in ["\n", "\t", " ", "\r"]:
            satellite_name = satellite_name[:-1]
        if "GPS" in satellite_name:
            constellation = "NAVSTAR"
        elif "COSMOS" in satellite_name:
            constellation = "GLONASS"
        elif "BEIDOU" in satellite_name:
            constellation = "BEIDOU"
        elif "GALILEO" in satellite_name:
            constellation = "GALILEO"
        elif "QZS" in satellite_name:
            constellation = "QZSS"
        else:
            constellation = "OTHER"
    elif c == 1:
        satellite_line1 = line
    elif c == 2:
        satellite_line2 = line
    c += 1
    if c == 3:
        satellites[constellation][satellite_name] = EarthSatellite(satellite_line1, satellite_line2, satellite_name, ts)
        c = 0

timezone = pytz.timezone(st.session_state["timezone"])

time_start = datetime.combine(st.session_state["date_start"], st.session_state["time_start"], tzinfo=timezone)
time_stop = datetime.combine(st.session_state["date_stop"], st.session_state["time_stop"], tzinfo=timezone)

ts_time_start = ts.utc(time_start)
ts_time_stop = ts.utc(time_stop)

time_steps = []
time_temp = time_start
while time_temp < time_stop:
    time_steps.append(time_temp)
    time_temp += timedelta(minutes=15)

satellite_earth_positions = pd.DataFrame(columns=["Constellation", "Satellite", "Time", "Orbit", "Lat", "Lon"])

for const in constellations[:]:
    for sat in satellites[const].keys():
        sat_obj = satellites[const][sat]
        for time_t in time_steps:
            temp_t = ts.utc(time_t)
            temp_geo = sat_obj.at(temp_t)
            # st.code(temp_geo.xyz.km)
            temp_lat, temp_lon = wgs84.latlon_of(temp_geo)
            temp_row = (const, sat, time_t, str(temp_geo.xyz.km), temp_lat.degrees, temp_lon.degrees)
            try:
                satellite_earth_positions.loc[max(satellite_earth_positions.index) + 1] = temp_row
            except:
                satellite_earth_positions.loc[0] = temp_row

# st.dataframe(satellite_earth_positions)

geometry = gpd.points_from_xy(satellite_earth_positions["Lon"], satellite_earth_positions["Lat"])
satellite_earth_geopositions = gpd.GeoDataFrame(satellite_earth_positions, geometry=geometry)

# st.dataframe(satellite_earth_geopositions)

satellite_lines = satellite_earth_geopositions.groupby(["Constellation", "Satellite"])["geometry"].apply(lambda x: LineString(x.tolist()))

satellite_lines = gpd.GeoDataFrame(satellite_lines, geometry="geometry")

# st.dataframe(satellite_lines)

satellite_map = folium.Map([0,0], zoom_start=2)

# st.write(dir(satellite_lines))

for ix, record in satellite_lines.iterrows():
    # st.code(dir(record.geometry.coords))
    # st.code(type(record.geometry.coords))
    folium.PolyLine([list(x)[::-1] for x in record.geometry.coords]).add_to(satellite_map)

stf.st_folium(satellite_map, width=1200)