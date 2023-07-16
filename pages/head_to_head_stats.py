import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import utils
import media.icon_constants as icons
from st_aggrid import AgGrid, AgGridTheme, GridOptionsBuilder

def get_game_result_string(game):
        return f"{game['total_points_per_game']} points: ({game['team_1_player_1']}, {game['team_1_player_2']}) {game['points_team_1']} - {game['points_team_2']} ({game['team_2_player_1']}, {game['team_2_player_2']}) on {game['date']} at {game['venue']}"


df = utils.get_data()
overall_avg_ppg = round(df["total_points_per_game"].mean(), 2)
st.markdown(f"<h1>Head To Head Stats &nbsp;{icons.HEAD_2_HEAD}</h1><hr>", unsafe_allow_html=True)

all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))
team_1, team_2 = None, None

with st.sidebar:
    with st.form("head_2_head_form"):
        team_1 = [st.selectbox(label="Team 1 Player 1", options=all_players), st.selectbox(label="Team 1 Player 2", options=all_players)]
        team_2 = [st.selectbox(label="Team 2 Player 1", options=all_players), st.selectbox(label="Team 2 Player 2", options=all_players)]
        st.form_submit_button("Find")

if len(set(team_1 + team_2)) == 4:
    player_matches = utils.get_player_stats(team_1[0], df)
    player_matches['partner'] = np.where(
        player_matches["belongs_to"] == 'team_1',
        np.where(
            player_matches["team_1_player_1"] == team_1[0],
            player_matches["team_1_player_2"],
            player_matches["team_1_player_1"]
        ),
        np.where(
            player_matches["team_2_player_1"] == team_1[0],
            player_matches["team_2_player_2"],
            player_matches["team_2_player_1"]
        ),
    )
    head_2_head_df = player_matches[np.where(
        player_matches['belongs_to'] == 'team_1',
        np.logical_and.reduce([
            player_matches['partner'] == team_1[1],
            player_matches['team_2_player_1'].isin(team_2),
            player_matches['team_2_player_2'].isin(team_2),
        ]),
        np.logical_and.reduce([
            player_matches['partner'] == team_1[1],
            player_matches['team_1_player_1'].isin(team_2),
            player_matches['team_1_player_2'].isin(team_2),
        ])
    )].copy().reset_index()

    if head_2_head_df.empty:
        st.markdown("<h3 style='font-weight: lighter; text-align: center; margin-top: 10%;'>No Matches has been played between the pairs.</h3>", unsafe_allow_html=True)

    else:

        head_2_head_df["other_team_points"] = head_2_head_df["total_points_per_game"] - head_2_head_df["player_team_points"]

        longest_game = head_2_head_df.iloc[head_2_head_df["total_points_per_game"].idxmax(), :].to_dict()
        recent_game = head_2_head_df.sort_values('timestamp').iloc[-1, :].to_dict()

        head_2_head_stats = {
            "total_games": head_2_head_df.shape[0],
            "team_1_wins": head_2_head_df["is_win"].sum(),
            "average_ppg": head_2_head_df["total_points_per_game"].mean(),
            "average_margin_of_victory": head_2_head_df["margin"].mean(),
            "avg_team1_pts": round(head_2_head_df["player_team_points"].mean(), 2),
            "avg_team2_pts": round(head_2_head_df["other_team_points"].mean(), 2),
            "longest_game": get_game_result_string(longest_game)
        }

        head_2_head_stats["team_2_wins"] = head_2_head_stats["total_games"] - head_2_head_stats["team_1_wins"]
        head_2_head_stats["games_gone_beyond_deuce"] = (head_2_head_df["total_points_per_game"] > 40).sum()

        summary_cols = st.columns([3, 2])
        summary_cols[0].subheader(f"Total Games Played: {head_2_head_stats['total_games']}")
        summary_cols[0].markdown(f"<hr><h6>No of Games beyond Deuce: {head_2_head_stats['games_gone_beyond_deuce']}</h6>", unsafe_allow_html=True)
        summary_cols[0].markdown(f"<h6>Longest Game: </h6><p>{head_2_head_stats['longest_game']}</p>", unsafe_allow_html=True)
        summary_cols[0].markdown(f"<h6>Recent Game: </h6><p>{get_game_result_string(recent_game)}</p>", unsafe_allow_html=True)

        ppg_meter = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=head_2_head_stats['average_ppg'],
                title="Avg PPG",
                delta={"reference": overall_avg_ppg}
            )
        ).update_traces(gauge_bar_color="#9ccc65").update_layout(width=300, margin=dict(l=120, b=50))

        summary_cols[1].plotly_chart(ppg_meter)

        head_2_head_stats["team_1_avg_win_margin"] = round(head_2_head_df[head_2_head_df["is_win"] == 1]["margin"].mean(), 2)
        head_2_head_stats["team_2_avg_win_margin"] = round(head_2_head_df[head_2_head_df["is_win"] == 0]["margin"].mean(), 2)

        head_2_head_stats["team_1_min_points_in_game"] = head_2_head_df["player_team_points"].min()
        head_2_head_stats["team_2_min_points_in_game"] = head_2_head_df["other_team_points"].min()

        head_2_head_stats["team_1_largest_win"] = np.nan if head_2_head_stats["team_1_wins"] == 0 else get_game_result_string(head_2_head_df.iloc[head_2_head_df[head_2_head_df["is_win"] == 1]["margin"].idxmax(), :].to_dict())
        head_2_head_stats["team_2_largest_win"] = np.nan if head_2_head_stats["team_2_wins"] == 0 else get_game_result_string(head_2_head_df.iloc[head_2_head_df[head_2_head_df["is_win"] == 0]["margin"].idxmax(), :].to_dict())

        head_2_head_stats["team_1_games_won_after_deuce"] = np.nan if head_2_head_stats["team_1_wins"] == 0 else head_2_head_df[(head_2_head_df["total_points_per_game"] > 40) & (head_2_head_df["is_win"] == 1)].shape[0]
        head_2_head_stats["team_2_games_won_after_deuce"] = np.nan if head_2_head_stats["team_2_wins"] == 0 else head_2_head_df[(head_2_head_df["total_points_per_game"] > 40) & (head_2_head_df["is_win"] == 0)].shape[0]

        comparision_table_list = [
            ["Wins", "Average points per game", "Average Win Margin", "Minimum Points in a Game", "Games Won post Deuce", "Largest Win"],
            [head_2_head_stats["team_1_wins"], head_2_head_stats["avg_team1_pts"], head_2_head_stats["team_1_avg_win_margin"], head_2_head_stats["team_1_min_points_in_game"], head_2_head_stats["team_1_games_won_after_deuce"], head_2_head_stats["team_1_largest_win"]],
            [head_2_head_stats["team_2_wins"], head_2_head_stats["avg_team2_pts"], head_2_head_stats["team_2_avg_win_margin"], head_2_head_stats["team_2_min_points_in_game"], head_2_head_stats["team_2_games_won_after_deuce"], head_2_head_stats["team_2_largest_win"]]
        ]

        h2h_table_df = pd.DataFrame(comparision_table_list[1:], columns=comparision_table_list[0]).T.reset_index()
        h2h_table_df.columns = ["metric", " - ".join(team_1), " - ".join(team_2)]

        builder = GridOptionsBuilder.from_dataframe(h2h_table_df)
        builder.configure_default_column(width=250)
        builder.configure_columns(
             [" - ".join(team_1), " - ".join(team_2)],
             wrapText=True, 
             autoHeight=True,
             width=350
        )
        grid_options = builder.build()

        st.markdown(f"<hr><h5>Stat Table: </h5>", unsafe_allow_html=True)

        AgGrid(
             h2h_table_df,
             gridOptions = grid_options,
             custom_css=utils.AGGRID_TABLE_STYLES,
             theme=AgGridTheme.MATERIAL,
             height=600
        )
else:
    st.warning("Please ensure that the player names given as team players are distinct")