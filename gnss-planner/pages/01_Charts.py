from pages import satellite_cache
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load, wgs84
import requests
import pytz
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pathlib
from io import StringIO

for k, v in st.session_state.items():
    st.session_state[k] = v

st.set_page_config(layout="wide")

st.title("Satellite Graphs")

ts = load.timescale()
# st.write(st.session_state)

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
    
# st.write(get_GNSS_TLE())
    
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
    time_temp += timedelta(minutes=5)

obslat, obslon = st.session_state["home_marker"]
observer = wgs84.latlon(obslat, obslon, st.session_state["altitude"])

cutoff = st.session_state["cutoff"]

satellite_observer_positions = pd.DataFrame(columns=["Constellation", "Satellite", "Time", "Altitude", "Azimuth", "Distance"])
satellite_observer_counts = pd.DataFrame(columns=["Constellation", "Time", "Count"])

for const in constellations:
    for sat in satellites[const].keys():
        sat_obj = satellites[const][sat]
        obs_diff = sat_obj - observer
        for time_t in time_steps:
            # st.code(time_t)
            temp_t = ts.utc(time_t)
#             temp_geo = sat_obj.at(temp_t)
#             temp_latlon = wgs84.latlon_of(temp_geo)
            temp_alt, temp_az, temp_dist = obs_diff.at(temp_t).altaz()
            temp_row = (const, sat, time_t, temp_alt.degrees, temp_az.degrees, temp_dist.km)
            # st.code(f"{temp_alt.degrees > 0} -- {temp_alt.degrees} - {temp_az.degrees} - {temp_dist.km}")
            if temp_alt.degrees >= cutoff:
                try:
                    satellite_observer_positions.loc[max(satellite_observer_positions.index) + 1] = temp_row
                except:
                    satellite_observer_positions.loc[0] = temp_row

satellite_observer_positions["TimeString"] = [x.isoformat(sep="T") for x in satellite_observer_positions["Time"]]

satellite_observer_counts = satellite_observer_positions.groupby(["Constellation", "TimeString"]).count().reset_index()
# st.dataframe(satellite_observer_counts)
# for i in satellite_observer_counts.index:
#     st.code(i)
# for const in constellations:
#     for time_t in time_steps:
#         temppd = satellite_observer_positions.mask(satellite_observer_positions["Constellation"] == const)
#         temppd = temppd.mask(satellite_observer_positions["TimeString"] == time_t.isoformat(sep="T"))
#         st.write(temppd.count(0))

# satellite_observer_counts = satellite_observer_positions.groupby(["Constellation"], 1)
# st.dataframe(satellite_observer_counts)

count_fig = px.area(satellite_observer_counts,
                    x="TimeString",
                    y="Satellite",
                    color="Constellation", 
                    height=600)
count_fig.update_layout(title="Satellite Counts by Constellation Over Time")
st.plotly_chart(count_fig)

line_fig = px.line(satellite_observer_positions, 
                  x="Time", 
                  y="Altitude",
                  color="Satellite",
                  line_dash="Constellation",
                  height=600)
line_fig.update_layout(title="Satellite Altitudes Over Time")
st.plotly_chart(line_fig)

satellite_observer_positions["DisplayAltitude"] = [abs(x-90) for x in satellite_observer_positions["Altitude"]]

# polar_fig = px.scatter_polar(satellite_observer_positions,
#                              r="DisplayAltitude", 
#                              theta="Azimuth",
#                              color="Satellite", 
#                              symbol="Constellation",
#                              direction="clockwise",
#                              )

polar_fig = go.Figure()

polar_fig.add_trace(go.Scatterpolar(
    r=satellite_observer_positions["DisplayAltitude"],
    theta=satellite_observer_positions["Azimuth"],
    mode="lines"
))
tens = np.zeros((360))
tens = np.abs(tens + cutoff - 90)
ra360 = np.arange(360)
polar_fig.add_trace(go.Scatterpolar(
    r=tens,
    theta=ra360, 
    mode="lines"
))
polar_fig.update_layout(height=600)
polar_fig.update_layout(
    polar=dict(
        radialaxis=dict(
            range=[0, 91],
            ticktext=[f"{90-tick}°" for tick in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]],  # noqa: E501
            tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
            tickmode="array",
            gridcolor="lightgray",
            showgrid=True,
            linewidth=0.5,
        ),
        angularaxis=dict(
            ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
            tickvals=np.arange(0, 360, 45),
            direction='clockwise',
            gridcolor="lightgray",
            showgrid=True,
            linewidth=0.5,
        ),
        bgcolor='white',
    ),
    showlegend=False,
    title='All-Sky View with Alt/Az Grid',
    width=700,
    height=700,

)
st.plotly_chart(polar_fig)
        