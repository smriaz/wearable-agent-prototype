import streamlit as st
import matplotlib.pyplot as plt

from src.storage import init_state
from src.features import compute_features


init_state()

st.title("2) Trends & Quality")

df = st.session_state.df
if df is None:
    st.warning("Load data first in the Data page.")
    st.stop()

st.subheader("Quick plots")
cols = ["steps", "resting_hr", "sleep_hours", "sleep_efficiency", "hrv_proxy", "wear_time_hours"]

for c in cols:
    fig = plt.figure()
    plt.plot(df["date"], df[c])
    plt.title(c)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

st.subheader("Computed feature summary (what we feed the LLM)")
try:
    features = compute_features(df)
    st.session_state.features = features
    st.json(features)
except Exception as e:
    st.error(str(e))
