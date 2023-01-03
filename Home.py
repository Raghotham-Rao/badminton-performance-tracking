import streamlit as st
import pandas as pd
import numpy as np
from fetch_sheets_data import Gsheet
import os
import json
import plotly.express as px
import plotly.graph_objects as go
import utils
from sections import venue_section, leaderboard, datewise_stats
import media.icon_constants as icons

st.set_page_config(layout="wide")

sidebar = st.sidebar

sidebar.title("Badminton Tracking")

df = utils.get_data()

st.markdown(f"<h1>Badminton Tracking{icons.MAIN_LOGO}</h1>", unsafe_allow_html=True)

st.markdown(f"<h3>Total Games Played: {df.shape[0]}</h3>", unsafe_allow_html=True)

all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))

st.markdown(f"<hr><h5>{icons.LEADERBOARD}&nbsp;Leaderboard</h5>", unsafe_allow_html=True)
leaderboard.display_leaderboard(df, all_players)

st.markdown(f"<hr><h5>{icons.CALENDAR}&nbsp;Date Wise stats</h5>", unsafe_allow_html=True)
datewise_stats.display_date_section(df)

st.markdown(f"<hr><h5>{icons.STADIUM}&nbsp;Venue Wise stats</h5>", unsafe_allow_html=True)
venue_section.display_venue_stats(df)

st.markdown("<hr>", unsafe_allow_html=True)