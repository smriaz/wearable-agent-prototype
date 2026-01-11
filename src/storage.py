from __future__ import annotations
import streamlit as st
import pandas as pd


def init_state() -> None:
    if "df" not in st.session_state:
        st.session_state.df = None
    if "features" not in st.session_state:
        st.session_state.features = None
    if "escalation" not in st.session_state:
        st.session_state.escalation = None
    if "clarifying_q" not in st.session_state:
        st.session_state.clarifying_q = None
    if "clarifying_a" not in st.session_state:
        st.session_state.clarifying_a = None
    if "agent_outputs" not in st.session_state:
        st.session_state.agent_outputs = None


def set_df(df: pd.DataFrame) -> None:
    st.session_state.df = df
    # Invalidate downstream cached artifacts
    st.session_state.features = None
    st.session_state.escalation = None
    st.session_state.clarifying_q = None
    st.session_state.clarifying_a = None
    st.session_state.agent_outputs = None
