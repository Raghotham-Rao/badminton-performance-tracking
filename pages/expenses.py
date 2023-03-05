import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import utils
import media.icon_constants as icons


df = utils.get_data()
all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))
all_players.remove("other")

st.title("Expense Tracker")
st.markdown("<hr>", unsafe_allow_html=True)

cols = st.columns([2, 1])

with cols[0]:
    try:
        df = utils.get_expenses_data()
        if df.empty:
            st.subheader("No Expenses Tracked Yet")
        else:
            st.dataframe(df)
    except:
        st.subheader("No Expenses Tracked Yet")

with cols[1]:
    with st.form("add_expense", clear_on_submit=True):
        st.subheader("Add Expense")
        game_date = st.date_input("expense_date")
        amount = st.slider("amount", min_value=0, max_value=1500, step=10, value=250)
        paid_by = st.selectbox("paid_by", options=all_players)
        add_new_expense = st.form_submit_button("Add")
        if add_new_expense:
            utils.add_expense_data([f'{game_date}', amount, paid_by])
            df = utils.get_expenses_data()
