import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import utils
from st_aggrid import GridOptionsBuilder, AgGrid, AgGridTheme

def display_date_section(df: pd.DataFrame):
    date_cols = st.columns([3, 2])

    date_df = df.groupby("date").agg(**{
        "total_games": pd.NamedAgg("date", "count"),
        "average_ppg": pd.NamedAgg("total_points_per_game", "mean"),
    })
    date_df["average_ppg"] = round(date_df["average_ppg"], 2)
    max_games, max_games_played_on = date_df['total_games'].max(), date_df['total_games'].idxmax()
    date_df = date_df.reset_index()

    builder = GridOptionsBuilder.from_dataframe(date_df)

    grid_options = builder.build()
    grid_options['getRowStyle'] = utils.get_js_code_for_row_color('date', max_games_played_on)

    with date_cols[0]:
        datewise_stats = AgGrid(
            date_df, 
            gridOptions=grid_options, 
            theme=AgGridTheme.MATERIAL, 
            allow_unsafe_jscode=True,
            height=500,
            fit_columns_on_grid_load=True,
            custom_css=utils.AGGRID_TABLE_STYLES
        )

    date_cols[1].markdown(f"""
        <div style="margin-left: 20px">
            <h6>Most games played in a day:</h6>
            <h2>{max_games} Games on {max_games_played_on}</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )