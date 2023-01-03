import streamlit as st
import plotly.express as px
import pandas as pd

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
        hole=0.4,
        title="Venue Most Visited",
        width=350
    )
    venue_pie_fig.update_traces(
        textposition='inside',
        showlegend=False
    )
    venue_pie_fig.update_layout(margin=dict(l=100), title=dict(xanchor="center"))

    venue_cols[1].plotly_chart(
        venue_pie_fig
    )

    st.markdown("<h6>Overall Venue stats</h6>", unsafe_allow_html=True)
    st.columns([3, 1])[0].table(
        df.groupby("venue").agg(**{
            "total_games": pd.NamedAgg("date", "count"), 
            "average_ppg": pd.NamedAgg("total_points_per_game", "mean"),
            **{f"{fn}_margin": pd.NamedAgg("margin", fn) for fn in ["mean", "max", "min"]}
        })
    )