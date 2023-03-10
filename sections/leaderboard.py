import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import utils


def display_leaderboard(df, players_list):
    leaderboard_cols = st.columns([2, 1])

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
    leader_board_fig = utils.create_go_table_figure(leaderboard_df.head(10))
    leader_board_fig.update_traces(cells_fill_color=[np.where(leaderboard_df['wins_pct'] == leaderboard_df['wins_pct'].max(), '#b5de2b', '#eceff1')])
    leader_board_fig.update_layout(margin=dict(t=0))
    leaderboard_cols[0].plotly_chart(leader_board_fig)