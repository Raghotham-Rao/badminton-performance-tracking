import streamlit as st
import pandas as pd
import numpy as np
from sections import individual_stats
import utils

df = utils.get_data()
all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))


cols = st.columns([3, 1])
cols[0].title('Individual stats')

player = cols[1].selectbox(label="Player Name", options=all_players)
st.markdown("<hr>", unsafe_allow_html=True)

player_matches = utils.get_player_stats(player, df)
individual_stats.display_player_win_loss_stats(player_matches)


### Partner wise stats
st.markdown("<hr><h6>Player - Partner stats</h6>", unsafe_allow_html=True)
individual_stats.display_player_partner_stats(player_matches, player)


### Player Daily stats
st.markdown("<hr><h6>Player - Date wise stats</h6>", unsafe_allow_html=True)
individual_stats.display_player_daily_stats(player_matches, player)