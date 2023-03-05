import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import os
from fetch_sheets_data import Gsheet
import json
import plotly.graph_objects as go


def get_player_stats(player, df: pd.DataFrame):
    player_matches = df[
        np.where(
            np.logical_or.reduce([df[i] == player for i in ["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]]),
            True,
            False
        )
    ].copy()
    
    player_matches["belongs_to"] = np.where(
        np.logical_or(
            *[player_matches[i] == player for i in ["team_1_player_1", "team_1_player_2"]]
        ),
        'team_1',
        'team_2'
    )
    
    player_matches['player_team_points'] = np.where(
        player_matches["belongs_to"] == 'team_1',
        player_matches["points_team_1"],
        player_matches["points_team_2"]
    )
    
    player_matches['result'] = np.where(player_matches.belongs_to == player_matches.winner, "win", "loss")
    player_matches['is_win'] = np.where(player_matches.result == "win", 1, 0)
    
    return player_matches

def get_gsheet():
    if os.environ["STREAMLIT_APP_MODE"] == "test":
        with open(os.environ['CONFIG_FILE_PATH']) as f:
            return Gsheet(json.load(f))
    else:
        return Gsheet(st.secrets['gsheet_configs'])
    
def add_expense_data(expense_data):
    get_gsheet().add_expense("badminton_tracking", "expense_tracker", expense_data)

def get_expenses_data():
    gsheet = get_gsheet()
    return gsheet.get_sheet_data("badminton_tracking", "expense_tracker")

def get_data():
    gsheet = get_gsheet()
    df = gsheet.get_sheet_data("badminton_tracking", "Form Responses 1").drop(["result"], axis=1)

    df.columns = ["timestamp", "date", "team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2", "points_team_1", "points_team_2", "venue"]

    df['winner'] = np.where(df.points_team_1 > df.points_team_2, 'team_1', 'team_2')
    df['margin'] = abs(df.points_team_1 - df.points_team_2)
    df['total_points_per_game'] = df["points_team_1"] + df["points_team_2"]
    df['date'] = pd.to_datetime(df['date']).dt.strftime("%Y-%m-%d")
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df = df.applymap(lambda x: f'{x}'.lower().strip() if isinstance(x, str) else x)
    df['point_bins'] = pd.cut(
        df['total_points_per_game'],
        [0, 30, 35, 40, 45, float("inf")],
        right=False,
        labels=['< 30', '30 - 35', '35 - 40', '40 - 45', "> 45"]
    )

    return df.sort_values("timestamp")

def create_go_table_figure(df):
    go_table = go.Table(
        header=dict(
            values=df.columns, 
            align="left", 
            height=40, 
            fill_color="lightslategrey", 
            font=dict(color="white", size=16, family="Arial")
        ),
        cells=dict(
            values=[df[i] for i in df.columns], 
            align="left", 
            height=30,
            fill_color='#eceff1'
        )
    )
    fig = go.Figure(go_table)
    fig.update_layout(margin=dict(t=0, b=0))
    return fig