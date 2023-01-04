import streamlit as st
import pandas as pd
import numpy as np
from sections import individual_stats
import utils
import media.icon_constants as icons

df = utils.get_data()
all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))


cols = st.columns([3, 1])
cols[0].markdown(f"<h1>Individual stats &nbsp;{icons.PLAYER}</h1>", unsafe_allow_html=True)

player = cols[1].selectbox(label="Player Name", options=all_players)

player_matches = utils.get_player_stats(player, df)
st.markdown(f"<hr><h5>{icons.STATS_ICON}&nbsp;Player Stats</h5>", unsafe_allow_html=True)
individual_stats.display_player_win_loss_stats(player_matches)


### Partner wise stats
st.markdown(f"<hr><h5>{icons.TEAMMATE}&nbsp;Player - Partner stats</h5>", unsafe_allow_html=True)
individual_stats.display_player_partner_stats(player_matches, player)


### Player Daily stats
st.markdown(f"<hr><h5>{icons.CALENDAR}&nbsp;Player - Date wise stats</h5>", unsafe_allow_html=True)
individual_stats.display_player_daily_stats(player_matches, player)