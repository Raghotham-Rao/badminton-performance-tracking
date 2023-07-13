import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import utils
from st_aggrid import AgGrid, GridOptionsBuilder, AgGridTheme, ColumnsAutoSizeMode


def display_player_win_loss_stats(player_matches: pd.DataFrame):
    player_win_loss_columns = st.columns([3, 1, 2])
    player_win_loss_df = player_matches.groupby("result").agg(**{
        "total_games": pd.NamedAgg("result", "count"), 
        "average_ppg": pd.NamedAgg("player_team_points", "mean"),
        **{f"{fn}_margin": pd.NamedAgg("margin", fn) for fn in ["mean", "max", "min"]}
    }).round(decimals=2)

    win_loss_pie = px.pie(
        player_win_loss_df,
        values="total_games",
        names=player_win_loss_df.index,
        template="plotly_white",
        color=player_win_loss_df.index,
        color_discrete_map={"win":'#b5de2b', "loss":'lightslategrey'},
        hole=0.3
    )
    win_loss_pie.update_layout(width=250, showlegend=False, margin=dict(l=80, b=120, t=0))
    player_win_loss_columns[2].plotly_chart(
        win_loss_pie
    )

    player_win_loss_columns[0].markdown('<h6 style="margin-top: 40px">Overall Stats:</h6>', unsafe_allow_html=True)

    builder = GridOptionsBuilder.from_dataframe(player_win_loss_df.T.reset_index())
    builder.configure_column("index", header_name="Metric")
    grid_options = builder.build()

    with player_win_loss_columns[0]:
        AgGrid(
            player_win_loss_df.T.reset_index(),
            gridOptions=grid_options,
            theme=AgGridTheme.STREAMLIT,
            custom_css=utils.AGGRID_TABLE_STYLES,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            allow_unsafe_jscode=True,
            height=205
        )

def display_player_partner_stats(player_matches: pd.DataFrame, player):
    player_partner_cols = st.columns([3, 2])

    player_matches['partner'] = np.where(
        player_matches["belongs_to"] == 'team_1',
        np.where(
            player_matches["team_1_player_1"] == player,
            player_matches["team_1_player_2"],
            player_matches["team_1_player_1"]
        ),
        np.where(
            player_matches["team_2_player_1"] == player,
            player_matches["team_2_player_2"],
            player_matches["team_2_player_1"]
        ),
    )

    player_partner_stats = player_matches.groupby(["partner"]).agg(**{
        "total_games": pd.NamedAgg("result", "count"), 
        "wins": pd.NamedAgg("is_win", "sum"),
        "average_ppg": pd.NamedAgg("player_team_points", "mean")
    })
    player_partner_stats["win_pct"] = round(player_partner_stats['wins'] * 100 / player_partner_stats['total_games'], 2)
    player_partner_stats["average_ppg"] = round(player_partner_stats["average_ppg"], 2)

    best_teammate = player_partner_stats["win_pct"].idxmax()
    player_partner_stats = player_partner_stats.reset_index()

    player_partner_cols[0].markdown('<h6 style="margin-top: 40px">Partnerwise Stats:</h6>', unsafe_allow_html=True)

    with player_partner_cols[0]:
        builder = GridOptionsBuilder.from_dataframe(player_partner_stats)
        grid_options = builder.build()
        grid_options['getRowStyle'] = utils.get_js_code_for_row_color('partner', best_teammate)

        AgGrid(
            player_partner_stats,
            gridOptions=grid_options,
            theme=AgGridTheme.STREAMLIT,
            custom_css=utils.AGGRID_TABLE_STYLES,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            allow_unsafe_jscode=True
        )

    partner_list = player_partner_stats.index.to_list()
    bar_colors = ['lightslategrey' for i in range(player_partner_stats.shape[0])]
    bar_colors[partner_list.index(player_partner_stats['win_pct'].idxmax())] = '#b5de2b'

    player_partner_cols[1].markdown('<h6 style="margin-top: 40px">&emsp;&emsp;Partnerwise Win Percentages:</h6>', unsafe_allow_html=True)

    partner_bar_chart = go.Figure(
        go.Bar(
            y=player_partner_stats.index,
            x=player_partner_stats['win_pct'],
            orientation='h',
            marker_color=bar_colors,
            hovertemplate="Win Percentage: %{x} %"
        )
    )
    partner_bar_chart.update_layout(
        plot_bgcolor="white",
        width=300,
        margin=dict(b=0, l=100, t=0),
        height=player_partner_stats.shape[0] * 50
    )

    player_partner_cols[-1].plotly_chart(
        partner_bar_chart
    )

def display_player_daily_stats(player_matches: pd.DataFrame, player):
    daily_stat_cols = st.columns([4, 2])
    daily_performance = player_matches.groupby(["date", "result"]).agg(**{
        "total_games": pd.NamedAgg("result", "count"), 
        "average_ppg": pd.NamedAgg("player_team_points", "mean"),
        **{f"{fn}_margin": pd.NamedAgg("margin", fn) for fn in ["mean", "max", "min"]}
    })

    daily_performance_bar_chart = px.bar(
        daily_performance.reset_index(),
        x='date',
        y='total_games',
        color='result',
        barmode="group",
        template="simple_white",
        color_discrete_map={"win":'#b5de2b', "loss":'lightslategrey'},
        title=f"{player}'s Daily Performance",
        width=800,
        height=400
    )

    daily_stat_cols[0].markdown('<h6 style="margin-top: 40px">Daily Stats:</h6>', unsafe_allow_html=True)

    daily_performance_res_ignored = player_matches.groupby(["date"]).agg(**{
        "total_games": pd.NamedAgg("result", "count"), 
        "wins": pd.NamedAgg("is_win", "sum"),
        "average_ppg": pd.NamedAgg("player_team_points", "mean")
    })
    
    best_day = daily_performance_res_ignored['total_games'].idxmax()
    daily_performance_res_ignored = daily_performance_res_ignored.reset_index()
    
    daily_performance_res_ignored['win_pct'] = round(daily_performance_res_ignored['wins'] * 100 / daily_performance_res_ignored['total_games'], 2)
    daily_performance_res_ignored["average_ppg"] = round(daily_performance_res_ignored["average_ppg"], 2)

    with daily_stat_cols[0]:
        builder = GridOptionsBuilder.from_dataframe(daily_performance_res_ignored)
        grid_options = builder.build()
        grid_options['getRowStyle'] = utils.get_js_code_for_row_color('date', best_day)

        AgGrid(
            daily_performance_res_ignored,
            gridOptions=grid_options,
            theme=AgGridTheme.STREAMLIT,
            custom_css=utils.AGGRID_TABLE_STYLES,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            allow_unsafe_jscode=True,
            height=400
        )

    daily_win_pct = go.Scatter(
        x=daily_performance_res_ignored["date"],
        y=daily_performance_res_ignored["win_pct"],
        line_color="#b5de2b",
        fill="tozeroy"
    )

    daily_win_pct_fig = go.Figure(daily_win_pct)
    daily_win_pct_fig.update_layout(plot_bgcolor="#f9f9ff", title="Daily win percentages")

    st.plotly_chart(
        daily_win_pct_fig
    )