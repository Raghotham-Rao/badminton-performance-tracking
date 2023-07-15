import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import utils
import media.icon_constants as icons
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, AgGridTheme, JsCode

def text_color(amount):
    if amount < 300:
        return "#4caf50"
    elif amount < 600:
        return "#ff9800"
    else:
        return "tomato"

def get_players_on_date(df: pd.DataFrame):
    players_on_date = df[['date', 'team_1_player_1', 'team_1_player_2', 'team_2_player_1', 'team_2_player_2']].copy()

    players_on_date = players_on_date.groupby("date").agg({
        'team_1_player_1': 'unique',
        'team_1_player_2': 'unique',
        'team_2_player_1': 'unique',
        'team_2_player_2': 'unique'
    })

    players_on_date['players'] = players_on_date[['team_1_player_1', 'team_1_player_2', 'team_2_player_1', 'team_2_player_2']].apply(
        lambda x: [i for i in set(', '.join([', '.join(x[i]) for i in range(4)]).split(', ')) if i != 'other'], 
        axis=1
    )
    players_on_date = players_on_date[['players']]
    players_on_date['number_of_players'] = players_on_date['players'].str.len()

    return players_on_date

def get_balances(player_share_df: pd.DataFrame, settlements_df: pd.DataFrame, shuttle_expenses: pd.DataFrame):
    balances = player_share_df.groupby(['players', 'paid_by'][::-1]).agg({
        'date': 'count',
        'share': 'sum'
    }).reset_index()

    transformed_shuttle_expenses = shuttle_expenses[['paid_by', 'covered_for', 'expense_id', 'share']]
    transformed_shuttle_expenses.columns = ['paid_by', 'players', 'date', 'share']

    balances = pd.concat([balances, transformed_shuttle_expenses]).groupby(["paid_by", "players"]).agg({"share": "sum", "date": "min"}).reset_index()

    st.dataframe(balances)

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

    balances_post_settlement = pd.merge(
        balances,
        settlements_df,
        left_on=['player', 'owes_to'],
        right_on=['paid_by', 'paid_to'],
        how = "left"
    )

    balances_post_settlement['amount'] = np.where(
        balances_post_settlement['paid_to'].isna(),
        balances_post_settlement['amount_x'],
        np.where(
            balances_post_settlement['amount_x'] > balances_post_settlement['amount_y'],
            balances_post_settlement['amount_x'] - balances_post_settlement['amount_y'],
            0
        )
    )

    balances_post_settlement = balances_post_settlement[['player', 'owes_to', 'amount']].round(decimals=2)

    return balances_post_settlement


df = utils.get_data()
all_players = list(np.unique(df[["team_1_player_1", "team_1_player_2", "team_2_player_1", "team_2_player_2"]].values))
all_players.remove("other")
shuttle_expenses = utils.get_shuttle_expenses_data()
shuttle_expenses['covered_for'] = shuttle_expenses['shared_by'].str.split(', ')
shuttle_expenses['share'] = shuttle_expenses['amount'] / shuttle_expenses['covered_for'].apply(len)

shuttle_expenses = shuttle_expenses.explode('covered_for')[['expense_id', 'record_date', 'paid_by', 'amount', 'share', 'covered_for', 'comments']]
shuttle_expenses = shuttle_expenses[shuttle_expenses['paid_by'] != shuttle_expenses['covered_for']]

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
    expenses_df = utils.get_expenses_data().sort_values('date')
    settlements_df = utils.get_settlements_data().groupby(['paid_by', 'paid_to']).sum('amount').reset_index()
except:
    expenses_tracked = False

if expenses_tracked and expenses_df.empty:
    st.subheader("No Expenses Tracked Yet")
else:
    st.markdown(f"<hr><h5>{icons.CALENDAR}&nbsp;Daily Expenses</h5>", unsafe_allow_html=True)
    costliest_day = expenses_df.iloc[expenses_df['amount'].idxmax(), 0]
    expenses_df['paid_by'] = expenses_df['paid_by'].str.capitalize()

    builder = GridOptionsBuilder.from_dataframe(expenses_df)

    grid_options = builder.build()
    grid_options['getRowStyle'] = utils.get_js_code_for_row_color('date', costliest_day)

    overall_expenses_cols = st.columns([4, 3])

    with overall_expenses_cols[0]:
        expenses_table = AgGrid(
            expenses_df,
            grid_options,
            height=400,
            theme=AgGridTheme.MATERIAL,
            allow_unsafe_jscode=True,
            custom_css=utils.AGGRID_TABLE_STYLES
        )

    with overall_expenses_cols[1]:
        total_badminton_expenses = expenses_df['amount'].sum() + shuttle_expenses.drop_duplicates(subset=['expense_id'])['amount'].sum()
        st.markdown(f'''
            <div style="font-family: Monospace; margin-top: 10%; text-align: center">
                <p style="font-size: 14px; font-weight: bolder; text-align: center">Total Expenses till date</p>
                <p style="font-size: 48px">&#8377;{total_badminton_expenses}</p>
            </div>
        ''', unsafe_allow_html=True)

    player_share_df = pd.merge(players_on_date_df.explode('players'), expenses_df, how="inner", on="date")
    player_share_df['share'] = player_share_df['amount'] / player_share_df['number_of_players']

    st.dataframe(player_share_df)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<h5>{icons.CALCULATOR}&nbsp;Balances</h5>", unsafe_allow_html=True)
    balances = get_balances(player_share_df, settlements_df, shuttle_expenses)
    balances_dict = balances[balances['amount'] > 0].to_dict(orient='records')

    for balance in balances_dict:
        st.markdown(f"<li style='font-family: Monospace; letter-spacing: 2px;'>{balance['player']} owes <span style='color: {text_color(balance['amount'])};'>&#8377;{balance['amount']}</span> to {balance['owes_to']}</li>", unsafe_allow_html=True)


    st.markdown(f"<hr><h5>{icons.CALENDAR}&nbsp;Day-wise Players Attended</h5>", unsafe_allow_html=True)
    
    additional_styles = {
        "border": "1px solid lightgray",
        "padding": "5px",
        "border-radius": "30px",
        "font-family": "monospace",
        "text-align": "center"
    }

    merged_df = pd.merge(players_on_date_df, expenses_df, how="inner", on="date")

    # merged_df['players'] = "<span>" + merged_df['players'].str.join("</span> <span>") + "</span>"

    builder = GridOptionsBuilder.from_dataframe(merged_df)

    builder.configure_columns(merged_df.columns, width=140)

    builder.configure_column(
        "players", 
        width=500,
        cellRenderer=JsCode("""
        class UrlCellRenderer {
            init(params) {
                this.eGui = document.createElement('div'); 
                this.eGui.innerHTML = '<span class="tablets">' + params.value.join('</span> <span class="tablets">') + '</span>';
            }
            getGui() {
                return this.eGui;
            }
        }
    """)
    )

    grid_options = builder.build()

    AgGrid(
        # pd.merge(players_on_date_df, expenses_df, how="inner", on="date"),
        merged_df,
        grid_options,
        theme=AgGridTheme.MATERIAL,
        custom_css={
            **utils.AGGRID_TABLE_STYLES, 
            ".tablets": additional_styles
        },
        allow_unsafe_jscode=True,
        height=400
    )


    st.markdown(f"<hr><h5>{icons.STATS_ICON}&nbsp;Cost Analysis</h5>", unsafe_allow_html=True)

    cost_analysis_cols = st.columns(3)
    venue_wise_expenditure = pd.merge(
        expenses_df,
        df[['date', 'venue']].drop_duplicates(),
        left_on='date',
        right_on='date'
    ).groupby('venue').sum('amount').reset_index()


    with cost_analysis_cols[2]:
        venue_costs_pie = px.pie(
            venue_wise_expenditure,
            values="amount",
            names='venue',
            template="plotly_white",
            color_discrete_sequence=px.colors.sequential.OrRd_r[-venue_wise_expenditure.shape[0]:],
            title="Venue wise cost",
            hole=0.3,
            width=350,
        )
        venue_costs_pie.update_layout(showlegend=False, margin=dict(l=40))
        st.plotly_chart(venue_costs_pie)

    with cost_analysis_cols[1]:
        monthly_expenditure = expenses_df.copy()
        monthly_expenditure['month'] = pd.to_datetime(monthly_expenditure['date']).dt.month

        monthly_expenditure = monthly_expenditure.groupby(
            pd.to_datetime(monthly_expenditure['date']).dt.month_name()
        ).agg({'amount': 'sum', 'month': 'min'})

        monthly_expenditure['color'] = np.where(
            monthly_expenditure['amount'] == monthly_expenditure['amount'].max(),
            'crimson',
            'lightslategrey'
        )

        monthly_expenditure = monthly_expenditure.sort_values('month', ascending=False)
        monthly_expenditure_fig = go.Figure(
            go.Bar(
                y=monthly_expenditure.index,
                x=monthly_expenditure['amount'],
                orientation='h',
                marker_color=monthly_expenditure['color']
            )
        )

        monthly_expenditure_fig.update_layout(width=300, title="Monthy Expenditure", margin=dict(l=40))

        st.plotly_chart(
            monthly_expenditure_fig
        )

    with cost_analysis_cols[0]:
        monthly_expenditure['prev_month_expense'] = monthly_expenditure['amount'].shift(-1)
        curr_month_expense = monthly_expenditure.reset_index().iloc[0, :].to_dict()

        metric_fig = go.Figure(
            go.Indicator(
                mode="number+delta",
                value=curr_month_expense["amount"],
                title=curr_month_expense["date"],
                delta={"reference": curr_month_expense["prev_month_expense"]}
            )
        ).update_traces(gauge_bar_color="#8bc34a").update_layout(width=300, margin=dict(l=80, b=50, t=0))

        st.plotly_chart(metric_fig)

    st.markdown("---")

    settlement_cols = st.columns([3, 1, 3])
    with settlement_cols[0]:
        st.markdown(f"<h5>{icons.SETTLEMENTS}&nbsp;Track Settlements</h5>", unsafe_allow_html=True)
        with st.form("add_settlement", clear_on_submit=True):
            st.markdown(f"<h6>Add Settlement</hh>", unsafe_allow_html=True)
            paid_by = st.selectbox("paid_by", options=all_players)
            paid_to = st.selectbox("paid_to", options=all_players)
            amount = st.number_input("amount")
            add_new_settlement = st.form_submit_button("Add")
            if add_new_settlement:
                utils.add_settlement_data([f'{datetime.now().date()}', paid_by, paid_to, amount])


    with settlement_cols[2]:
        st.markdown(f"<h5>{icons.SETTLEMENTS}&nbsp;Shuttle Expenses</h5>", unsafe_allow_html=True)
        with st.form("shuttle_expenses"):#, clear_on_submit=True):
            st.markdown(f"<h6>Add Shuttle Expense</hh>", unsafe_allow_html=True)
            shuttle_paid_by = st.selectbox("paid_by", options=all_players)
            shared_by = st.multiselect("shared by", options=all_players)
            shuttle_amount = st.number_input("amount")
            comments = st.text_input("comments")
            shuttle_expense_add = st.form_submit_button("Add")
            if shuttle_expense_add:
                utils.add_shuttle_expense_data([f'{datetime.now().date()}', shuttle_paid_by, shuttle_amount, ', '.join(shared_by), comments])
                # utils.add_settlement_data([f'{datetime.now().date()}', paid_by, paid_to, amount])
