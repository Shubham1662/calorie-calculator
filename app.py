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

    food_name = st.selectbox(
        "Food (type to search)",
        options=foods["food_name"].tolist(),
        index=None,
        placeholder="e.g. Masala Dosa",
        key="log_food",
    )

    if food_name is not None:
        food = foods.loc[foods["food_name"] == food_name].iloc[0]
        units = calculations.unit_options(food["serving_unit"])

        col_unit, col_qty = st.columns(2)
        unit = col_unit.selectbox("Unit", units, key=f"unit_{food_name}")

        # Quantity defaults tuned per unit: grams count in 10s from the
        # food's own serving weight; pieces start at one native serving.
        if unit == "gram":
            qty_args = dict(min_value=1.0, max_value=2000.0, step=10.0,
                            value=float(food["serving_weight_g"]))
        elif unit == "number":
            qty_args = dict(min_value=0.5, max_value=50.0, step=0.5,
                            value=calculations.pieces_per_serving(food["serving_unit"]))
        else:  # bowl / cup / glass / plate / tbsp / tsp
            qty_args = dict(min_value=0.25, max_value=20.0, step=0.25, value=1.0)
        quantity = col_qty.number_input(f"How much ({unit})",
                                        key=f"qty_{food_name}_{unit}", **qty_args)

        kcal = calculations.calories_for_unit(
            food["calories_per_serving"], food["serving_weight_g"],
            food["serving_unit"], unit, quantity)
        per_unit = calculations.calories_for_unit(
            food["calories_per_serving"], food["serving_weight_g"],
            food["serving_unit"], unit, 1)
        basis = "1 piece" if unit == "number" else f"1 {unit}"
        st.caption(f"≈ **{kcal:.0f} kcal** · {food_name}: {per_unit:.0f} kcal per "
                   f"{basis} (native serving: {food['serving_unit']}, "
                   f"~{food['serving_weight_g']:g} g)")

        if st.button("➕ Add food", type="primary"):
            log_unit = "piece" if unit == "number" else unit
            data_store.append_log_entry(day, food_name, quantity, log_unit, kcal)
            st.toast(f"Added {food_name} — {kcal:.0f} kcal")
            st.session_state.pop("log_food", None)
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
        amount = (f"{row['quantity']:g} g" if row["serving_unit"] == "gram"
                  else f"{row['quantity']:g} × {row['serving_unit']}")
        col_text.markdown(
            f"**{row['food_name']}** · {amount} · **{row['calories']:.0f} kcal**"
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
        new_weight = st.number_input("Weight of one serving (grams)", min_value=1,
                                     max_value=2000, value=100,
                                     help="Used to convert between grams, bowls and cups.")
        food_submitted = st.form_submit_button("💾 Save food", type="primary")

    if food_submitted:
        if not new_name.strip() or not new_unit.strip():
            st.warning("Food name and serving unit are required.")
        elif data_store.add_food(new_name, new_category, new_group, new_unit,
                                 new_kcal, new_weight):
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
            "serving_weight_g": "Weight (g)",
        }),
        hide_index=True, width="stretch", height=400,
    )
