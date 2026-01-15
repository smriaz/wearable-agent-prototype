from src.ui import render_header


import streamlit as st
import pandas as pd

from src.storage import init_state, set_df
from src.simulate import SimConfig, generate_simulated_user
from src.features import load_and_validate


init_state()
render_header("1) Data")

st.title("1) Data")
st.write("Upload a CSV or generate simulated wearable-style data.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload CSV")
    uploaded = st.file_uploader("Choose a CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        try:
            df2 = load_and_validate(df)
            set_df(df2)
            st.success(f"Loaded {len(df2)} rows.")
            st.dataframe(df2.tail(10), use_container_width=True)
        except Exception as e:
            st.error(str(e))

with col2:
    st.subheader("Simulate data")
    days = st.slider("Days", 14, 90, 30, 1)
    seed = st.number_input("Random seed", 1, 9999, 7, 1)
    profile = st.selectbox("Profile", ["normal", "flu_like", "stressed", "missing_wear"])
    if st.button("Generate simulated user"):
        df = generate_simulated_user(SimConfig(days=days, seed=seed, profile=profile))
        df2 = load_and_validate(df)
        set_df(df2)
        st.success(f"Generated {len(df2)} rows ({profile}).")
        st.dataframe(df2.tail(10), use_container_width=True)

st.divider()
if st.session_state.df is None:
    st.info("No dataset loaded yet. Use the uploader or simulator above.")
else:
    st.subheader("Current dataset snapshot")
    st.dataframe(st.session_state.df.head(10), use_container_width=True)
