import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import utils

def display_date_section(df):
    date_cols = st.columns([3, 2])

    date_df = df.groupby("date").agg(**{
        "total_games": pd.NamedAgg("date", "count"),
        "average_ppg": pd.NamedAgg("total_points_per_game", "mean"),
    })
    date_df["average_ppg"] = round(date_df["average_ppg"], 2)

    date_stats_fig = utils.create_go_table_figure(date_df.reset_index())
    date_stats_fig.update_layout(width=450, margin=dict(b=0))

    date_cols[0].plotly_chart(date_stats_fig)
    date_cols[1].markdown(f"""
        <div style="margin-left: 20px">
            <h6>Most games played in a day:</h6>
            <h2>{date_df['total_games'].max()} Games on {date_df['total_games'].idxmax()}</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )