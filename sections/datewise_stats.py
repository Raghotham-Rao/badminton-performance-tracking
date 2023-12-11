import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import utils
from st_aggrid import GridOptionsBuilder, AgGrid, AgGridTheme
from datetime import datetime, timedelta
import json

def display_heatmap(df):
    current_year_jan_1 = datetime(datetime.now().year, 1, 1)

    x = list(range(1, 53))
    y = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    first_day_ind = y.index(current_year_jan_1.strftime("%a"))

    y = y[first_day_ind:] + y[:first_day_ind]

    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week
    df['day'] = df['date'].dt.day_of_week
    df['year'] = df['date'].dt.year

    df = df[df['date'] >= str(current_year_jan_1.date())]

    nz = [[0 for i in range(52)] for j in range(7)]
    hover_text = np.array([list(range(i, i + 7)) for i in range(0, 364, 7)]).T.tolist()
    hover_text = [[f'0 games played on {current_year_jan_1.date() + timedelta(days=i)}' for i in j] for j in hover_text]

    for i in json.loads(df.to_json(orient="records")):
        nz[(i["day"] + (7 - first_day_ind)) % 7][i["week"] - 1] = i["total_games"]
        hover_text[(i["day"] + (7 - first_day_ind)) % 7][i["week"] - 1] = f'{i["total_games"]} games played on {datetime.fromtimestamp(i["date"] / 1000).strftime("%a")}, {datetime.fromtimestamp(i["date"] / 1000).date()}'

    fig = go.Figure(data=go.Heatmap(
        z = nz[::-1],
        x = x,
        y = y[::-1],
        xgap=4,
        ygap=4,
        hovertext=hover_text[::-1],
        hovertemplate="%{hovertext}",
        colorscale=px.colors.sequential.Greens,
        showscale=False
    ))

    fig.update_layout(
        width=750, 
        height=150, 
        margin=dict(b=0, t=0, r=0)
    )
    st.plotly_chart(fig)


def display_date_section(df: pd.DataFrame):
    date_cols = st.columns([4, 2])

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

    # with date_cols[0]:
    #     datewise_stats = AgGrid(
    #         date_df, 
    #         gridOptions=grid_options, 
    #         theme=AgGridTheme.MATERIAL, 
    #         allow_unsafe_jscode=True,
    #         height=500,
    #         fit_columns_on_grid_load=True,
    #         custom_css=utils.AGGRID_TABLE_STYLES
    #     )

    with date_cols[0]:
        st.markdown(f"""
            <div style="margin-bottom: 10px; margin-top: 10px">
                <h6>Daily Trend:</h6>
            </div>
            """, 
            unsafe_allow_html=True
        )
        display_heatmap(date_df)
        st.markdown(f"""
            <div>
                <h6>Most games played in a day:</h6>
                <h3>{max_games} Games on {max_games_played_on}</h3>
            </div>
            """, 
            unsafe_allow_html=True
        )