import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import utils

def display_player_win_loss_stats(player_matches: pd.DataFrame):
    player_win_loss_columns = st.columns([3, 1, 2])
    player_win_loss_df = player_matches.groupby("result").agg(**{
        "total_games": pd.NamedAgg("result", "count"), 
        "average_ppg": pd.NamedAgg("player_team_points", "mean"),
        **{f"{fn}_margin": pd.NamedAgg("margin", fn) for fn in ["mean", "max", "min"]}
    })

    win_loss_pie = px.pie(
        player_win_loss_df,
        values="total_games",
        names=player_win_loss_df.index,
        template="plotly_white",
        color=player_win_loss_df.index,
        color_discrete_map={"win":'#b5de2b', "loss":'lightslategrey'},
        hole=0.3
    )
    win_loss_pie.update_layout(width=300, showlegend=False, margin=dict(l=50, b=0, t=0))
    player_win_loss_columns[2].plotly_chart(
        win_loss_pie
    )

    player_win_loss_columns[0].markdown('<h6 style="margin-top: 40px">Overall Stats:</h6>', unsafe_allow_html=True)
    player_performance_fig = utils.create_go_table_figure(player_win_loss_df.T.reset_index())
    player_performance_fig.update_traces(header_values=['Metric', 'During Losses', 'During Wins'])
    player_performance_fig.update_layout(margin=dict(t=0, b=0), height=400)
    player_win_loss_columns[0].plotly_chart(
        player_performance_fig
    )
    # player_win_loss_columns[1].table(player_win_loss_df.T)

def display_player_partner_stats(player_matches: pd.DataFrame, player):
    player_partner_cols = st.columns([2, 1])

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

    player_partner_cols[0].markdown('<h6 style="margin-top: 40px">Partnerwise Stats:</h6>', unsafe_allow_html=True)
    player_partner_table_fig = utils.create_go_table_figure(player_partner_stats.reset_index())
    player_partner_table_fig.update_traces(columnwidth=[1, 1, 1, 1, 2], cells_fill_color=[np.where(player_partner_stats['win_pct'] == player_partner_stats['win_pct'].max(), '#b5de2b', '#eceff1')])
    player_partner_table_fig.update_layout(margin=dict(t=0,b=0))

    player_partner_cols[0].plotly_chart(player_partner_table_fig)
    # player_partner_cols[0].table(player_partner_stats)

    partner_list = player_partner_stats.index.to_list()
    bar_colors = ['lightslategrey' for i in range(player_partner_stats.shape[0])]
    bar_colors[partner_list.index(player_partner_stats['win_pct'].idxmax())] = '#b5de2b'

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
        title_text="Partnerwise win percentages",
        width=300
    )

    player_partner_cols[1].plotly_chart(
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
        color_discrete_sequence=['#b5de2b', 'lightslategrey'],
        title=f"{player}'s Daily Performance",
        height=300,
        width=400
    )

    daily_stat_cols[0].markdown('<h6 style="margin-top: 40px">Daily Stats:</h6>', unsafe_allow_html=True)

    daily_performance_res_ignored = player_matches.groupby(["date"]).agg(**{
        "total_games": pd.NamedAgg("result", "count"), 
        "wins": pd.NamedAgg("is_win", "sum"),
        "average_ppg": pd.NamedAgg("player_team_points", "mean")
    }).reset_index()
    daily_performance_res_ignored['win_pct'] = round(daily_performance_res_ignored['wins'] * 100 / daily_performance_res_ignored['total_games'], 2)
    daily_performance_res_ignored["average_ppg"] = round(daily_performance_res_ignored["average_ppg"], 2)

    daily_performance_table_fig = utils.create_go_table_figure(daily_performance_res_ignored)
    daily_performance_table_fig.update_traces(columnwidth=[2, 2, 2, 2, 3])


    daily_stat_cols[0].plotly_chart(
        daily_performance_table_fig
    )

    daily_stat_cols[1].plotly_chart(
        daily_performance_bar_chart
    )