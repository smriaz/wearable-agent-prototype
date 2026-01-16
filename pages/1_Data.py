from src.ui import render_header

import streamlit as st
import pandas as pd
from pathlib import Path

from src.storage import init_state, set_df
from src.simulate import SimConfig, generate_simulated_user
from src.features import load_and_validate


init_state()
render_header("1) Data")
demo_mode = st.session_state.get("demo_mode", False)

st.write("Upload a CSV, choose a bundled sample dataset, or generate simulated wearable-style data.")

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _reset_downstream_states():
    # Keep this conservative: reset things that depend on df
    for k in ["features", "escalation", "agent_outputs", "clarifying_q", "clarifying_a", "chat_messages"]:
        if k in st.session_state:
            st.session_state.pop(k, None)

def _load_df(df: pd.DataFrame, success_msg: str):
    try:
        df2 = load_and_validate(df)
        set_df(df2)
        _reset_downstream_states()
        st.success(success_msg + f" ({len(df2)} rows).")
        if not demo_mode:
            st.dataframe(df2.tail(10), use_container_width=True)
        else:
            st.caption("Demo mode hides raw table previews.")
    except Exception as e:
        st.error(str(e))

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tabs = st.tabs(["Upload CSV", "Sample data", "Simulate"])

# -------------------------
# Tab 1: Upload
# -------------------------
with tabs[0]:
    st.subheader("Upload CSV")
    uploaded = st.file_uploader("Choose a CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        if st.button("Load uploaded CSV", use_container_width=True):
            _load_df(df, "Loaded uploaded dataset")

# -------------------------
# Tab 2: Sample data
# -------------------------
with tabs[1]:
    st.subheader("Use bundled sample data")

    data_dir = Path("data")
    sample_files = []
    if data_dir.exists():
        sample_files = sorted([p.name for p in data_dir.glob("*.csv")])

    if not sample_files:
        st.info("No sample CSVs found in `data/`. Add `sample_user.csv` and `sample_user_missing.csv` to enable this tab.")
    else:
        sample_name = st.selectbox("Select a sample dataset", sample_files)
        if st.button("Load sample dataset", use_container_width=True):
            df = pd.read_csv(data_dir / sample_name)
            _load_df(df, f"Loaded sample dataset: {sample_name}")

# -------------------------
# Tab 3: Simulate
# -------------------------
with tabs[2]:
    st.subheader("Simulate data")

    c1, c2 = st.columns(2)
    with c1:
        days = st.slider("Days", 14, 90, 30, 1)
        profile = st.selectbox("Profile", ["normal", "flu_like", "stressed", "missing_wear"])
    with c2:
        seed = st.number_input("Random seed", 1, 9999, 7, 1)

    if st.button("Generate simulated user", use_container_width=True):
        df = generate_simulated_user(SimConfig(days=days, seed=seed, profile=profile))
        _load_df(df, f"Generated simulated dataset ({profile})")

# ---------------------------------------------------------
# Current dataset snapshot (clean + demo mode aware)
# ---------------------------------------------------------
st.divider()

df_current = st.session_state.get("df")
if df_current is None:
    st.info("No dataset loaded yet. Use Upload, Sample data, or Simulate above.")
else:
    st.subheader("Current dataset")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Rows", str(len(df_current)))
    with c2:
        st.metric("Start", str(df_current["date"].min()) if "date" in df_current.columns else "—")
    with c3:
        st.metric("End", str(df_current["date"].max()) if "date" in df_current.columns else "—")

    if not demo_mode:
        st.dataframe(df_current.head(10), use_container_width=True)
    else:
        st.caption("Demo mode hides raw tables.")
