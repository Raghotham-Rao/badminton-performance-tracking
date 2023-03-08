import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import utils
import media.icon_constants as icons
from datetime import datetime

def text_color(amount):
    if amount < 50:
        return "#4caf50"
    elif amount < 100:
        return "#ff9800"
    else:
        return "tomato"

def get_players_on_date(df):
    players_on_date = df[['date', 'team_1_player_1', 'team_1_player_2', 'team_2_player_1', 'team_2_player_2']].copy()

    # players_on_date['date'] = players_on_date['date'].apply(lambda x: f'{datetime.strptime(x, "%m/%d/%Y").date()}')

    players_on_date = players_on_date.groupby("date").agg({
        'team_1_player_1': 'unique',
        'team_1_player_2': 'unique',
        'team_2_player_1': 'unique',
        'team_2_player_2': 'unique'
    })

    players_on_date['players'] = players_on_date[['team_1_player_1', 'team_1_player_2', 'team_2_player_1', 'team_2_player_2']].apply(
        lambda x: list(set(', '.join([', '.join(x[i]) for i in range(4)]).split(', '))), 
        axis=1
    )
    players_on_date = players_on_date[['players']]
    players_on_date['number_of_players'] = players_on_date['players'].str.len()

    return players_on_date

def get_balances(player_share_df):
    balances = player_share_df.groupby(['players', 'paid_by'][::-1]).agg({
        'date': 'count',
        'share': 'sum'
    }).reset_index()

    balances = balances[balances['paid_by'] != balances['players']]

    balances = pd.merge(
        balances,
        balances,
        left_on=['paid_by', 'players'],
        right_on=['players', 'paid_by'],
        how="left"
    )

    balances['owes'] = np.where(
        balances['paid_by_y'].isna(),
        balances['share_x'],
        np.where(
            balances['share_x'] > balances['share_y'],
            balances['share_x'] - balances['share_y'],
            0
        )
    )

    balances = balances[['players_x', 'paid_by_x', 'owes', 'date_x']]
    balances.columns = ['player', 'owes_to', 'amount', 'for_days']

    balances = balances[balances['amount'] > 0].round(decimals=2)

    return balances


df = utils.get_data()
all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))
all_players.remove("other")

with st.sidebar:
    with st.form("add_expense", clear_on_submit=True):
        st.subheader("Add Expense")
        game_date = st.date_input("expense_date")
        amount = st.number_input("amount", min_value=0, max_value=1500, step=10, value=250)
        paid_by = st.selectbox("paid_by", options=all_players)
        add_new_expense = st.form_submit_button("Add")
        if add_new_expense:
            utils.add_expense_data([f'{game_date}', amount, paid_by])

players_on_date_df = get_players_on_date(df)

st.markdown(f"<h1>{icons.EXPENSE_TRACKER}&nbsp; Expense Tracker</h1>", unsafe_allow_html=True)

expenses_tracked = True
try:
    expenses_df = utils.get_expenses_data()
except:
    expenses_tracked = False

if expenses_tracked and expenses_df.empty:
    st.subheader("No Expenses Tracked Yet")
else:
    st.markdown(f"<hr><h5>{icons.CALENDAR}&nbsp;Daily Expenses</h5>", unsafe_allow_html=True)
    expenses_fig = utils.create_go_table_figure(expenses_df)
    expenses_fig.update_traces(cells_fill_color=[np.where(expenses_df['amount'] == expenses_df['amount'].max(), '#b5de2b', '#eceff1')])
    expenses_fig.update_layout(margin=dict(t=0, b=0), width=350, height=225)
    st.plotly_chart(expenses_fig)

    player_share_df = pd.merge(players_on_date_df.explode('players'), expenses_df, how="inner", on="date")
    player_share_df['share'] = player_share_df['amount'] / player_share_df['number_of_players']

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<h5>{icons.CALCULATOR}&nbsp;Balances</h5>", unsafe_allow_html=True)
    balances = get_balances(player_share_df)
    balances_dict = balances.to_dict(orient='records')

    for balance in balances_dict:
        st.markdown(f"<li style='font-family: Monospace; letter-spacing: 2px;'>{balance['player']} owes <span style='color: {text_color(balance['amount'])};'>&#8377;{balance['amount']}</span> to {balance['owes_to']}</li>", unsafe_allow_html=True)


    st.markdown(f"<hr><h5>{icons.CALENDAR}&nbsp;Day-wise Players Attended</h5>", unsafe_allow_html=True)

    st.dataframe(pd.merge(players_on_date_df, expenses_df, how="inner", on="date").set_index('date'))
