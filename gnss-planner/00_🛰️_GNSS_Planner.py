import streamlit as st
import streamlit_folium as stf
import folium
from folium.plugins import Draw
from datetime import datetime, timedelta
import pytz 

for k, v in st.session_state.items():
    if k.startswith("_"):
        st.session_state[k[1:]] = v

st.set_page_config(layout="wide",
                   page_title="GNSS Planner", 
                   page_icon="🛰️")

st.title("GNSS Planner")

with st.form(key="time_settings"):

    # start date time
    sdc1, sdc2 = st.columns(2)
    date_start = sdc1.date_input("What is the start date?", key="_date_start")
    time_start = sdc2.time_input("What is the start time?", key="_time_start")

    # end date time
    edc1, edc2 = st.columns(2)
    date_stop = edc1.date_input("What is the end date?", key="_date_stop")
    time_stop = edc2.time_input("What is the end time?", key="_time_stop")

    # location settings
    lsc1, lsc2 = st.columns(2)
    altitude = lsc1.number_input("Altitude in meters", 
                                min_value=-500, 
                                max_value=20_200_000,  #orbital altitude of navstar
                                step=5, 
                                value=10, 
                                key="_altitude")
    cutoff = lsc2.number_input("Horizon Cutoff in degrees", 
                               min_value=0, 
                               max_value=90, 
                               value=10,
                               step=5,
                               key="_cutoff")

    if "default_timezone" not in st.session_state.keys():
        st.session_state["default_timezone"] = "Europe/Amsterdam"

    timezone = st.selectbox("Select timezone", 
                            options=pytz.common_timezones, 
                            index=pytz.common_timezones.index(st.session_state["default_timezone"]),
                            key="_timezone")

    # loc1, loc2 = st.columns(2)
    # loc1.number_input("latitude", value=st.session_state["home_marker"][0])
    # loc1.number_input("longitude", value=st.session_state["home_marker"][1])

    st.form_submit_button("Submit settings")

if "home_marker" not in st.session_state.keys():
    st.session_state["home_marker"] = [50, 0]

location_selection_map = folium.Map(st.session_state["home_marker"], zoom_start=5, width=800)

if "home_marker" in st.session_state.keys():
    home_marker = folium.Marker(st.session_state["home_marker"], icon=folium.Icon(color="red", icon="home")).add_to(location_selection_map)


location_selection_render = stf.st_folium(location_selection_map, width=800)

if st.button("Update Location", key="update_location"):
    st.session_state["home_marker"] = [location_selection_render["center"]["lat"], location_selection_render["center"]["lng"]]
    st.rerun()

# st.write(st.session_state)

# if st.button("Save All"):
    # for k, v in st.session_state.items():
    #     st.session_state[k] = v

# st.write(dir(pytz.timezone(pytz.common_timezones[5])))