"""Calorie Calculator — single-user Streamlit app for tracking Indian food intake."""

from datetime import date

import streamlit as st

from src import analytics, calculations, data_store

st.set_page_config(
    page_title="Calorie Calculator",
    page_icon="🍛",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Larger tap targets and tighter spacing for phone screens
st.markdown(
    """
    <style>
      .stButton > button, .stFormSubmitButton > button { width: 100%; min-height: 2.8rem; }
      div[data-testid="stMetric"] { text-align: center; }
      div[data-testid="stMetricValue"] { font-size: 1.5rem; }
      .block-container { padding-top: 2.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🍛 Calorie Calculator")

foods = data_store.load_foods()
log = data_store.load_log()

with st.sidebar:
    st.header("⚙️ Settings")
    target = st.number_input(
        "Daily calorie target (kcal)",
        min_value=800, max_value=6000, step=50,
        value=data_store.get_daily_target(),
    )
    if target != data_store.get_daily_target():
        data_store.set_daily_target(target)

tab_log, tab_trends, tab_foods = st.tabs(["🍽️ Log", "📈 Trends", "➕ Foods"])

# ---------------------------------------------------------------- Log tab
with tab_log:
    selected_date = st.date_input("Date", value=date.today(), max_value=date.today())
    day = selected_date.isoformat()

    with st.form("add_entry", clear_on_submit=True):
        food_name = st.selectbox(
            "Food (type to search)",
            options=foods["food_name"].tolist(),
            index=None,
            placeholder="e.g. Masala Dosa",
        )
        quantity = st.number_input("Quantity (servings)", min_value=0.25,
                                   max_value=20.0, value=1.0, step=0.25)
        submitted = st.form_submit_button("➕ Add food", type="primary")

    if submitted:
        if food_name is None:
            st.warning("Pick a food first.")
        else:
            food = foods.loc[foods["food_name"] == food_name].iloc[0]
            kcal = calculations.calories_for(food["calories_per_serving"], quantity)
            data_store.append_log_entry(day, food_name, quantity,
                                        food["serving_unit"], kcal)
            st.toast(f"Added {food_name} — {kcal:.0f} kcal")
            st.rerun()

    consumed = calculations.total_for_date(log, day)
    left = calculations.remaining(target, consumed)
    c1, c2, c3 = st.columns(3)
    c1.metric("Consumed", f"{consumed:.0f}")
    c2.metric("Target", f"{target}")
    c3.metric("Remaining", f"{left:.0f}",
              delta=f"{-left:.0f} over" if left < 0 else None,
              delta_color="inverse")
    if left < 0:
        st.error(f"⚠️ {-left:.0f} kcal over your daily target.")

    entries = calculations.entries_for_date(log, day)
    st.subheader(f"Entries — {selected_date.strftime('%d %b %Y')}")
    if entries.empty:
        st.caption("Nothing logged yet for this day.")
    for idx, row in entries.iterrows():
        col_text, col_btn = st.columns([5, 1])
        col_text.markdown(
            f"**{row['food_name']}** · {row['quantity']:g} × {row['serving_unit']} "
            f"· **{row['calories']:.0f} kcal**"
        )
        if col_btn.button("🗑️", key=f"del_{idx}", help="Delete entry"):
            data_store.delete_log_entry(idx)
            st.rerun()

# ------------------------------------------------------------- Trends tab
with tab_trends:
    st.subheader("Last 14 days")
    totals = analytics.daily_totals_14d(log)
    logged_days = totals[totals["calories"] > 0]
    if logged_days.empty:
        st.info("Log a few days of food to see your trend here.")
    else:
        st.altair_chart(analytics.trend_chart(totals, target), width="stretch")
        a1, a2, a3 = st.columns(3)
        a1.metric("Daily average", f"{logged_days['calories'].mean():.0f}")
        a2.metric("Days over target",
                  f"{int((logged_days['calories'] > target).sum())}")
        a3.metric("Days logged", f"{len(logged_days)}")
        with st.expander("View as table"):
            st.dataframe(
                totals[["day", "calories"]].rename(
                    columns={"day": "Day", "calories": "kcal"}),
                hide_index=True, width="stretch",
            )

# -------------------------------------------------------------- Foods tab
with tab_foods:
    st.subheader("Add a new food")
    with st.form("add_food", clear_on_submit=True):
        new_name = st.text_input("Food name")
        new_category = st.radio("Category", ["Veg", "Non-Veg"], horizontal=True)
        new_group = st.selectbox(
            "Group", ["Staple", "Breakfast", "Curry", "Snack", "Sweet",
                      "Dairy", "Beverage", "Fruit", "Other"])
        new_unit = st.text_input("Serving unit", placeholder="e.g. 1 cup / 2 pieces / 100 g")
        new_kcal = st.number_input("Calories per serving", min_value=1,
                                   max_value=2000, value=100)
        food_submitted = st.form_submit_button("💾 Save food", type="primary")

    if food_submitted:
        if not new_name.strip() or not new_unit.strip():
            st.warning("Food name and serving unit are required.")
        elif data_store.add_food(new_name, new_category, new_group, new_unit, new_kcal):
            st.success(f"Saved {new_name.strip()} ({new_kcal} kcal per {new_unit.strip()}).")
            st.rerun()
        else:
            st.warning("That food already exists in the database.")

    st.subheader(f"Food database ({len(foods)} items)")
    search = st.text_input("Search foods", placeholder="Filter by name…")
    view = foods
    if search.strip():
        view = foods[foods["food_name"].str.contains(search.strip(), case=False)]
    st.dataframe(
        view.rename(columns={
            "food_name": "Food", "category": "Category", "food_group": "Group",
            "serving_unit": "Serving", "calories_per_serving": "kcal",
        }),
        hide_index=True, width="stretch", height=400,
    )
