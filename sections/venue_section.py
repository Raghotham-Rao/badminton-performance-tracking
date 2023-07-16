import streamlit as st
import plotly.express as px
import pandas as pd
import utils
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, AgGridTheme

def display_venue_stats(df: pd.DataFrame):

    venue_cols = st.columns([3, 2])
    venue_bar_chart = px.bar(
        df.groupby(["point_bins", "venue"]).agg(**{
            "total_games": pd.NamedAgg("date", "count")
        }).reset_index(),
        x="venue",
        y="total_games",
        color="point_bins",
        template="plotly_white",
        color_discrete_sequence=px.colors.sequential.Viridis_r,
        title="Total Games played at different venues",
        width=600
    )

    venue_bar_chart.update_traces(showlegend=False)

    venue_cols[0].plotly_chart(
        venue_bar_chart
    )

    venue_pie_fig = px.pie(
        df.groupby(["venue"]).agg(**{
            "total_games": pd.NamedAgg("date", "count")
        }).reset_index(),
        values="total_games",
        names="venue",
        color_discrete_sequence=px.colors.sequential.Viridis_r,
        hole=0.3,
        title="Venue Most Visited",
        width=350
    )
    venue_pie_fig.update_traces(
        textposition='inside',
        showlegend=False,
        pull=0.05
    )
    venue_pie_fig.update_layout(margin=dict(l=100), title=dict(xanchor="center"))

    venue_cols[1].plotly_chart(
        venue_pie_fig
    )

    st.markdown("<h6 style='margin-top:50px'>Overall Venue stats</h6>", unsafe_allow_html=True)

    with st.columns([9, 1])[0]:
        venue_stats_df = df.groupby("venue").agg(**{
            "total_games": pd.NamedAgg("date", "count"), 
            "average_ppg": pd.NamedAgg("total_points_per_game", "mean"),
            **{f"{fn}_margin": pd.NamedAgg("margin", fn) for fn in ["mean", "max", "min"]}
        })

        venue_most_visited = venue_stats_df["total_games"].idxmax()

        venue_stats_df = venue_stats_df.reset_index().round(decimals=2)

        builder = GridOptionsBuilder.from_dataframe(venue_stats_df)

        grid_options = builder.build()
        grid_options['getRowStyle'] = utils.get_js_code_for_row_color('venue', venue_most_visited)

        leader_board = AgGrid(
            venue_stats_df, 
            gridOptions=grid_options, 
            theme=AgGridTheme.MATERIAL, 
            allow_unsafe_jscode=True,
            custom_css=utils.AGGRID_TABLE_STYLES
        )