"""
Nigeria Weather Forecast Dashboard
Kwara State University - PSO Feature Selection + Random Forest Weather Forecasting

Search any state -> see its 14-day forecast, historical trends, and model
performance, all pulled from the pipeline's precomputed tables and per-state
weather history.
"""
import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------
# PATHS
# ----------------------------------------------------------------
ROOT = Path(__file__).parent
DATA = ROOT / "data"
TABLES = DATA / "tables"
BY_STATE = DATA / "by_state"

SEASON_MONTHS = {
    "Harmattan (Dec-Feb)": [12, 1, 2],
    "Dry/Hot (Mar-May)": [3, 4, 5],
    "Rainy Peak (Jun-Aug)": [6, 7, 8],
    "Late Rains (Sep-Nov)": [9, 10, 11],
}

# ----------------------------------------------------------------
# DATA LOADING (cached so the site stays fast)
# ----------------------------------------------------------------
@st.cache_data
def load_meta():
    with open(DATA / "states_meta.json") as f:
        return pd.DataFrame(json.load(f))


@st.cache_data
def load_table(name):
    return pd.read_csv(TABLES / name)


@st.cache_data
def load_state_history(state_key):
    df = pd.read_csv(BY_STATE / f"{state_key}.csv", parse_dates=["DATE"])
    return df.sort_values("DATE")


@st.cache_data
def parse_forecast_row(state_name):
    t11 = load_table("table11_future_forecasts.csv")
    row = t11[t11["State"] == state_name]
    if row.empty:
        return None
    row = row.iloc[0]

    day_pat = re.compile(r"^Day(\d+)_(.+)_mm$")
    days = []
    for col in t11.columns:
        m = day_pat.match(col)
        if not m:
            continue
        day_n, label = int(m.group(1)), m.group(2)
        rain_col = f"Day{day_n}_Rain"
        days.append({
            "day": day_n,
            "label": label,
            "mm": float(row[col]),
            "rain": row[rain_col] if rain_col in row else "No",
        })
    days = sorted(days, key=lambda d: d["day"])
    return {
        "days": days,
        "week1_avg": row.get("Week1_Avg_mm"),
        "week1_total": row.get("Week1_Total_mm"),
        "week1_rain_days": row.get("Week1_RainDays"),
        "week2_avg": row.get("Week2_Avg_mm"),
        "week2_total": row.get("Week2_Total_mm"),
        "week2_rain_days": row.get("Week2_RainDays"),
        "peak_time": row.get("Hourly_Peak_Time"),
        "peak_mm": row.get("Hourly_Peak_mm"),
    }


# ----------------------------------------------------------------
# PAGE CONFIG / STYLE
# ----------------------------------------------------------------
st.set_page_config(
    page_title="Nigeria Weather Forecast",
    page_icon="🌦️",
    layout="wide",
)

RAIN_COLOR = "#1565C0"
DRY_COLOR = "#B0BEC5"

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    [data-testid="stMetricValue"] {font-size: 1.6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------
# LOAD CORE DATA
# ----------------------------------------------------------------
meta = load_meta()
table10 = load_table("table10_country_state_forecasts.csv")
available_states = sorted(meta["state"].tolist())
ALL_PROJECT_STATES_COUNT = 37  # 36 states + FCT, per config.py

# ----------------------------------------------------------------
# SIDEBAR - STATE SEARCH
# ----------------------------------------------------------------
with st.sidebar:
    st.title("🌦️ Weather Forecast")
    st.caption("PSO + Random Forest model · NASA POWER data · 2000-2026")

    selected_state = st.selectbox(
        "Search / select a state",
        options=available_states,
        index=available_states.index("Kwara") if "Kwara" in available_states else 0,
    )

    missing_count = ALL_PROJECT_STATES_COUNT - len(available_states)
    if missing_count > 0:
        st.warning(
            f"Data is currently available for {len(available_states)} of "
            f"{ALL_PROJECT_STATES_COUNT} states/FCT. {missing_count} states "
            "are missing from the downloaded dataset and will appear once "
            "re-downloaded and the pipeline is re-run."
        )

    st.divider()
    st.caption(
        "Built from the Kwara State University PSO-RF weather forecasting "
        "pipeline. Forecasts predict next-day precipitation (mm)."
    )

state_row10 = table10[table10["State"] == selected_state].iloc[0]
state_meta = meta[meta["state"] == selected_state].iloc[0]
forecast = parse_forecast_row(selected_state)
history = load_state_history(state_meta["state_key"])

# ----------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------
st.title(f"{selected_state} State")
st.caption(f"Capital: {state_meta['capital']}  ·  "
           f"{state_meta['lat']:.3f}°, {state_meta['lon']:.3f}°  ·  "
           f"Records: {state_meta['date_min']} to {state_meta['date_max']}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Next-Day Forecast", f"{state_row10['Next_Day_Forecast_mm']:.2f} mm")
c2.metric("Rain Likely Tomorrow", state_row10["Rain_Likely"])
c3.metric("Model R²", f"{state_row10['R2']:.3f}")
c4.metric("Model MAE", f"{state_row10['MAE']:.2f} mm")

st.divider()

# ----------------------------------------------------------------
# TABS
# ----------------------------------------------------------------
tab_forecast, tab_history, tab_model, tab_map, tab_about = st.tabs(
    ["14-Day Forecast", "Historical Trends", "Model Performance", "Country Map", "About"]
)

# ---------------- TAB 1: FORECAST ----------------
with tab_forecast:
    if forecast is None:
        st.info("No forecast table entry found for this state.")
    else:
        days_df = pd.DataFrame(forecast["days"])
        colors = [RAIN_COLOR if r == "YES" else DRY_COLOR for r in days_df["rain"]]

        fig = go.Figure()
        fig.add_bar(
            x=days_df["label"], y=days_df["mm"],
            marker_color=colors,
            text=[f"{v:.1f} mm" for v in days_df["mm"]],
            textposition="outside",
            name="Forecast",
        )
        fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                       annotation_text="Rain threshold (1.0 mm)")
        fig.update_layout(
            title=f"14-Day Precipitation Forecast — {selected_state}",
            yaxis_title="Precipitation (mm/day)",
            xaxis_title=None,
            showlegend=False,
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        w1, w2 = st.columns(2)
        with w1:
            st.subheader("This week (Days 1-7)")
            st.metric("Average", f"{forecast['week1_avg']:.2f} mm/day")
            st.metric("Total", f"{forecast['week1_total']:.2f} mm")
            st.metric("Rainy days", f"{int(forecast['week1_rain_days'])} / 7")
        with w2:
            st.subheader("Next week (Days 8-14)")
            st.metric("Average", f"{forecast['week2_avg']:.2f} mm/day")
            st.metric("Total", f"{forecast['week2_total']:.2f} mm")
            st.metric("Rainy days", f"{int(forecast['week2_rain_days'])} / 7")

        st.caption(
            f"Estimated peak rainfall hour today: **{forecast['peak_time']}** "
            f"({forecast['peak_mm']:.3f} mm). NASA POWER only provides daily "
            "data — hourly values are estimated using a West Africa "
            "climatological rainfall-timing pattern, not directly measured."
        )

# ---------------- TAB 2: HISTORICAL TRENDS ----------------
with tab_history:
    hist = history.copy()

    st.subheader(f"Yearly precipitation trend — {selected_state}")
    yearly = hist.groupby("YEAR", as_index=False)["precipitation"].mean()
    fig_y = px.line(yearly, x="YEAR", y="precipitation", markers=True)
    fig_y.update_layout(yaxis_title="Avg precipitation (mm/day)", xaxis_title="Year", height=350)
    st.plotly_chart(fig_y, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Average monthly precipitation")
        monthly = hist.groupby("MONTH", as_index=False)["precipitation"].mean()
        month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly["Month"] = monthly["MONTH"].apply(lambda m: month_names[m - 1])
        fig_m = px.bar(monthly, x="Month", y="precipitation",
                        category_orders={"Month": month_names})
        fig_m.update_layout(yaxis_title="Avg precipitation (mm/day)", xaxis_title=None, height=350)
        st.plotly_chart(fig_m, use_container_width=True)

    with col_b:
        st.subheader("Seasonal distribution")
        def season_of(m):
            for name, months in SEASON_MONTHS.items():
                if m in months:
                    return name
            return "Unknown"
        hist["season"] = hist["MONTH"].apply(season_of)
        fig_s = px.box(hist, x="season", y="precipitation",
                        category_orders={"season": list(SEASON_MONTHS.keys())})
        fig_s.update_layout(yaxis_title="Precipitation (mm/day)", xaxis_title=None, height=350)
        st.plotly_chart(fig_s, use_container_width=True)

    st.subheader("Last 90 days")
    recent = hist.tail(90)
    fig_r = go.Figure()
    fig_r.add_scatter(x=recent["DATE"], y=recent["precipitation"], name="Precipitation (mm)",
                       line=dict(color=RAIN_COLOR))
    fig_r.add_scatter(x=recent["DATE"], y=recent["temp_mean"], name="Mean Temp (°C)",
                       yaxis="y2", line=dict(color="#E65100"))
    fig_r.update_layout(
        height=350,
        yaxis=dict(title="Precipitation (mm)"),
        yaxis2=dict(title="Temp (°C)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_r, use_container_width=True)

    st.subheader("Summary statistics (full record)")
    stat_cols = ["temp_mean", "temp_min", "temp_max", "humidity", "precipitation",
                 "wind_speed", "cloud_cover", "pressure"]
    st.dataframe(hist[stat_cols].describe().T.round(2), use_container_width=True)

# ---------------- TAB 3: MODEL PERFORMANCE ----------------
with tab_model:
    st.subheader(f"How well the model predicts {selected_state}")
    m1, m2, m3 = st.columns(3)
    m1.metric("R² score", f"{state_row10['R2']:.4f}")
    m2.metric("MAE", f"{state_row10['MAE']:.4f} mm")
    m3.metric("RMSE", f"{state_row10['RMSE']:.4f} mm")
    st.caption(
        "R² close to 1.0 means the model explains most of the day-to-day "
        "variation; values near 0 (or negative) mean precipitation in this "
        "state is harder to predict from the current feature set. The "
        "model's hyperparameters were tuned on Kwara State (the project's "
        "primary training state) and then re-fit per state — see the "
        "**About** tab for full methodology."
    )

    st.divider()
    st.subheader("How states compare")
    fig_cmp = px.bar(
        table10.sort_values("R2"), x="R2", y="State", orientation="h",
        color=table10.sort_values("R2")["State"] == selected_state,
        color_discrete_map={True: "#FF5722", False: "#90A4AE"},
        height=700,
    )
    fig_cmp.update_layout(showlegend=False, xaxis_title="R² score", yaxis_title=None,
                           title=f"{selected_state} highlighted vs. all available states")
    st.plotly_chart(fig_cmp, use_container_width=True)

    st.divider()
    st.subheader("Overall model vs. baselines (trained on Kwara State)")
    t7 = load_table("table7_model_comparison.csv")
    st.dataframe(t7, use_container_width=True, hide_index=True)

    t9 = load_table("table9_seasonal_performance.csv")
    st.subheader("Seasonal performance (Kwara model)")
    st.dataframe(t9, use_container_width=True, hide_index=True)

# ---------------- TAB 4: MAP ----------------
with tab_map:
    st.subheader("Next-day forecast across all available states")
    map_df = table10.copy()
    map_df["is_selected"] = map_df["State"] == selected_state
    fig_map = px.scatter(
        map_df, x="Longitude", y="Latitude",
        color="Next_Day_Forecast_mm", size=map_df["is_selected"].map({True: 28, False: 14}),
        hover_name="State",
        hover_data={"Capital": True, "R2": ":.3f", "Next_Day_Forecast_mm": ":.2f",
                    "Longitude": False, "Latitude": False, "is_selected": False},
        color_continuous_scale="YlOrRd",
        text=map_df["State"].where(map_df["is_selected"], ""),
    )
    fig_map.update_traces(textposition="top center")
    fig_map.update_layout(height=650, xaxis_title="Longitude", yaxis_title="Latitude")
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption("Marker color = predicted precipitation tomorrow. The selected state is enlarged and labeled.")

# ---------------- TAB 5: ABOUT ----------------
with tab_about:
    st.subheader("About this project")
    st.markdown(
        """
This dashboard is built on the **Weather Forecasting Using PSO Feature Selection
and Random Forest** project (Kwara State University, Faculty of ICT, Department
of Computer Science). It combines Particle Swarm Optimisation for feature
selection and hyperparameter tuning with a Random Forest regressor to predict
next-day precipitation, using historical data from NASA POWER (2000-2026).

**Pipeline summary**
1. Data collection — NASA POWER API, daily data, all states
2. Preprocessing — missing-value imputation, lag-1 features
3. PSO feature selection — best subset of 20 candidate features
4. PSO hyperparameter tuning — `n_estimators` and `max_depth` for the Random Forest
5. Training — PSO-RF trained on 2000-2022, tested on 2023-2026 (primary state: Kwara)
6. Per-state forecasting — the tuned model is re-fit to each state's own history
7. 14-day recursive forecasting + hourly distribution using a West Africa
   climatological rainfall pattern
        """
    )

    st.subheader("Literature comparison")
    t8 = load_table("table8_literature_comparison.csv")
    st.dataframe(t8, use_container_width=True, hide_index=True)

    st.subheader("Tuned hyperparameters")
    t6 = load_table("table6_hyperparameters.csv")
    st.dataframe(t6, use_container_width=True, hide_index=True)

    if missing_count > 0:
        st.warning(
            f"**Data coverage note:** {len(available_states)} of "
            f"{ALL_PROJECT_STATES_COUNT} states/FCT currently have weather "
            "data. The remaining states were not present in the downloaded "
            "dataset (likely an interrupted or failed NASA POWER download "
            "for those states). Re-run `download_country_weather_data.py` "
            "and the pipeline for those states, then replace the files in "
            "the `data/` folder of this site to add them."
        )
