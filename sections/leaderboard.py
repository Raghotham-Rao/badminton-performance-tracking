import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, AgGridTheme, JsCode
import utils


def display_leaderboard(df, players_list):
    leaderboard_cols = st.columns([8, 3])

    leaderboard = []

    for player in players_list:
        player_stats = utils.get_player_stats(player, df)
        
        total_games, wins = player_stats.shape[0], player_stats['is_win'].sum()
        leaderboard.append({
            "player": player,
            "total_games": total_games,
            "wins": wins,
            "wins_pct": round(wins * 100 / total_games, 2),
            "form": ' '.join(player_stats.iloc[-5:, :]['result'].apply(lambda x: x[0].upper()).to_list())[::-1]
        })

    leaderboard_df = pd.DataFrame(leaderboard).sort_values("wins_pct", ascending=False)
    leaderboard_df = leaderboard_df[leaderboard_df['total_games'] > 25]
    leaderboard_df = leaderboard_df[leaderboard_df['player'] != 'other']
    leaderboard_df['player'] = leaderboard_df['player'].str.capitalize()
    leader = leaderboard_df.sort_values('wins_pct', ascending=False).iloc[0, 0]

    builder = GridOptionsBuilder.from_dataframe(leaderboard_df)

    builder.configure_columns(leaderboard_df.columns, width=140)
    builder.configure_column('player', width=140)
    builder.configure_column('total_games', width=180)

    grid_options = builder.build()
    grid_options['getRowStyle'] = utils.get_js_code_for_row_color('player', leader)

    with leaderboard_cols[0]:
        leader_board = AgGrid(
            leaderboard_df, 
            gridOptions=grid_options, 
            theme=AgGridTheme.MATERIAL, 
            allow_unsafe_jscode=True,
            custom_css=utils.AGGRID_TABLE_STYLES
        )