from src.ui import render_header

import streamlit as st
import matplotlib.pyplot as plt

from src.storage import init_state
from src.features import compute_features


init_state()
render_header("2) Trends & Quality")
demo_mode = st.session_state.get("demo_mode", False)

if "tq_rerun_done" not in st.session_state:
    st.session_state.tq_rerun_done = False


df = st.session_state.get("df")
if df is None:
    st.warning("Load data first in the Data page.")
    st.stop()

# Ensure date is usable for plotting
# (Assumes your df already has a 'date' column in the correct format)
date = df["date"]

# Compute features once (cache in session_state)
if st.session_state.get("features") is None:
    try:
        st.session_state.features = compute_features(df)

        # one-time rerun so the header chips update from pending → green
        if not st.session_state.tq_rerun_done:
            st.session_state.tq_rerun_done = True
            st.rerun()

    except Exception as e:
        st.error(str(e))
        st.stop()


features = st.session_state.features

tabs = st.tabs(["Trends", "Quality", "Features"])

# =========================================================
# Trends
# =========================================================
with tabs[0]:
    st.subheader("Quick trends")

    cols = ["steps", "resting_hr", "sleep_hours", "sleep_efficiency", "hrv_proxy", "wear_time_hours"]

    for c in cols:
        if c not in df.columns:
            continue

        fig = plt.figure()
        plt.plot(date, df[c])
        plt.title(c)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)

# =========================================================
# Quality
# =========================================================
with tabs[1]:
    st.subheader("Data quality snapshot")

    c1, c2, c3 = st.columns(3)
    with c1:
        w = (features or {}).get("window", {})
        st.metric("Window", f"{w.get('start','?')} → {w.get('end','?')}")
    with c2:
        # simple availability proxy
        st.metric("Days", str(len(df)))
    with c3:
        # overall missingness across the main wearable columns
        main_cols = [c for c in ["steps", "resting_hr", "sleep_hours", "sleep_efficiency", "hrv_proxy", "wear_time_hours"] if c in df.columns]
        if main_cols:
            missing_pct = float(df[main_cols].isna().mean().mean()) * 100.0
            st.metric("Avg missingness", f"{missing_pct:.1f}%")
        else:
            st.metric("Avg missingness", "—")

    st.divider()

    # Wear time plot (if present)
    if "wear_time_hours" in df.columns:
        st.write("**Wear time (hours/day)**")
        fig = plt.figure()
        plt.plot(date, df["wear_time_hours"])
        plt.title("wear_time_hours")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)

    # Missingness by column (bar)
    st.write("**Missingness by variable**")
    cols = [c for c in ["steps", "resting_hr", "sleep_hours", "sleep_efficiency", "hrv_proxy", "wear_time_hours"] if c in df.columns]
    if cols:
        miss = df[cols].isna().mean()
        fig = plt.figure()
        plt.bar(miss.index, miss.values)
        plt.xticks(rotation=45, ha="right")
        plt.title("Missingness rate")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("No expected wearable columns found for missingness summary.")

    if not demo_mode:
        with st.expander("Raw data preview (debug)"):
            st.dataframe(df)
    else:
        st.caption("Demo mode hides raw tables.")

# =========================================================
# Features (what we feed the LLM)
# =========================================================
with tabs[2]:
    st.subheader("Computed feature summary (what we feed the LLM)")

    if demo_mode:
        st.info("Demo mode hides detailed feature JSON. Turn off demo mode to view.")
    else:
        st.json(features)
