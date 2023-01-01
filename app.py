import streamlit as st
import pandas as pd
import numpy as np
from fetch_sheets_data import Gsheet
import os
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

gsheet = None
if os.environ["STREAMLIT_APP_MODE"] == "test":
    with open(os.environ['CONFIG_FILE_PATH']) as f:
        gsheet = Gsheet(json.load(f))
else:
    gsheet = Gsheet(st.secrets['gsheet_configs'])

df = gsheet.get_sheet_data("badminton_tracking", "Form Responses 1").drop(["Timestamp", "result"], axis=1)
df.columns = ["date", "team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2", "points_team_1", "points_team_2", "venue"]

df['winner'] = np.where(df.points_team_1 > df.points_team_2, 'team_1', 'team_2')
df['margin'] = abs(df.points_team_1 - df.points_team_2)
df['total_points_per_game'] = df["points_team_1"] + df["points_team_2"]

df = df.applymap(lambda x: f'{x}'.lower().strip() if isinstance(x, str) else x)
df['point_bins'] = pd.cut(
    df['total_points_per_game'],
    [0, 30, 35, 40, 45, float("inf")],
    right=False,
    labels=['< 30', '30 - 35', '35 - 40', '40 - 45', "> 45"]
)


st.title("Badminton Tracking")

st.markdown(f"<h3>Total Games Played: {df.shape[0]}</h3><hr>", unsafe_allow_html=True)

st.markdown("<h5>Venue Wise stats</h5>", unsafe_allow_html=True)
venue_cols = st.columns(2)

venue_cols[0].plotly_chart(
    px.bar(
        df.groupby(["point_bins", "venue"]).agg(**{
            "total_games": pd.NamedAgg("date", "count")
        }).reset_index(),
        x="venue",
        y="total_games",
        color="point_bins",
        template="plotly_white",
        color_discrete_sequence=px.colors.sequential.Viridis_r,
        title="Total Games played at different venues"
    )
)

venue_pie_fig = px.pie(
    df.groupby(["venue"]).agg(**{
        "total_games": pd.NamedAgg("date", "count")
    }).reset_index(),
    values="total_games",
    names="venue",
    color_discrete_sequence=px.colors.sequential.Viridis_r,
    hole=0.4,
    title="Venue Most Visited"
)
venue_pie_fig.update_traces(
    textposition='inside'
)

venue_cols[1].plotly_chart(
    venue_pie_fig
)

venue_cols[0].markdown("<h6>Overall Venue stats</h6>", unsafe_allow_html=True)
venue_cols[0].table(
    df.groupby("venue").agg(**{
        "total_games": pd.NamedAgg("date", "count"), 
        "average_ppg": pd.NamedAgg("total_points_per_game", "mean"),
        **{f"{fn}_margin": pd.NamedAgg("margin", fn) for fn in ["mean", "max", "min"]}
    })
)

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("<h5>Date Wise stats</h5>", unsafe_allow_html=True)
date_cols = st.columns(2)

date_df = df.groupby("date").agg(**{
    "total_games": pd.NamedAgg("date", "count"),
    "average_ppg": pd.NamedAgg("total_points_per_game", "mean"),
})

date_cols[0].table(date_df)
date_cols[1].markdown(f"""
    <div style="margin-left: 20px">
        <h6>Most games played in a day:</h6>
        <h2>{date_df['total_games'].max()} Games on {date_df['total_games'].idxmax()}</h2>
    </div>
    """, 
    unsafe_allow_html=True
)
st.markdown("<hr>", unsafe_allow_html=True)

### Player Section
st.markdown("<h5>Individual stats</h5>", unsafe_allow_html=True)
all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))
player = st.columns(4)[0].selectbox(label="Player Name", options=all_players)

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

player_win_loss_columns = st.columns(2)
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
    color_discrete_sequence=['#b5de2b', 'lightslategrey'],
    hole=0.3,
    title="Player performance"
)
win_loss_pie.update_layout(width=400)
player_win_loss_columns[0].plotly_chart(
    win_loss_pie
)

player_win_loss_columns[1].markdown('<h6 style="margin-top: 40px">Overall performance:</h6>', unsafe_allow_html=True)
player_win_loss_columns[1].table(player_win_loss_df.T)

### Partner wise stats

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h6>Player - Partner stats</h6>", unsafe_allow_html=True)

player_partner_cols = st.columns(2)

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

player_matches['is_win'] = np.where(player_matches['result'] == 'win', 1, 0)

player_partner_stats = player_matches.groupby(["partner"]).agg(**{
    "total_games": pd.NamedAgg("result", "count"), 
    "wins": pd.NamedAgg("is_win", "sum"),
    "average_ppg": pd.NamedAgg("player_team_points", "mean")
})
player_partner_stats["win_pct"] = round(player_partner_stats['wins'] * 100 / player_partner_stats['total_games'], 2)

player_partner_cols[0].markdown('<h6 style="margin-top: 40px">Partnerwise Stats:</h6>', unsafe_allow_html=True)
player_partner_cols[0].table(player_partner_stats)

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
    title_text="Partnerwise win percentages"
)

player_partner_cols[1].plotly_chart(
    partner_bar_chart
)


### Player Daily stats

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h6>Player - Partner stats</h6>", unsafe_allow_html=True)

daily_stat_cols = st.columns(2)
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
    height=500
)

daily_stat_cols[0].markdown('<h6 style="margin-top: 40px">Daily Stats:</h6>', unsafe_allow_html=True)

daily_performance_res_ignored = player_matches.groupby(["date"]).agg(**{
    "total_games": pd.NamedAgg("result", "count"), 
    "wins": pd.NamedAgg("is_win", "sum"),
    "average_ppg": pd.NamedAgg("player_team_points", "mean")
})
daily_performance_res_ignored['win_pct'] = round(daily_performance_res_ignored['wins'] * 100 / daily_performance_res_ignored['total_games'], 2)
daily_stat_cols[0].table(
    daily_performance_res_ignored
)

daily_stat_cols[1].plotly_chart(
    daily_performance_bar_chart
)


st.markdown("<hr><h5>Entire Data</h5>", unsafe_allow_html=True)
st.dataframe(df)