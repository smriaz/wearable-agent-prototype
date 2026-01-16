from src.ui import render_header

import os
import streamlit as st

from src.storage import init_state
from src.features import compute_features
from src.rules import determine_escalation
from src.prompts import SYSTEM_BASE
from src.llm import generate_text


init_state()
render_header("4) Chat")

df = st.session_state.df
if df is None:
    st.warning("Load data first in the Data page.")
    st.stop()

if st.session_state.features is None:
    st.session_state.features = compute_features(df)

features = st.session_state.features

if st.session_state.escalation is None:
    st.session_state.escalation = determine_escalation(features)

escalation = st.session_state.escalation

if os.environ.get("OPENAI_API_KEY") is None:
    st.warning("OPENAI_API_KEY not set. In Streamlit Cloud, add it under App → Settings → Secrets.")
    st.stop()

model = st.session_state.get("selected_model", "gpt-4.1-mini")


st.caption("Ask questions like: 'Why did my resting heart rate change?' or 'What does low wear time mean?'")

q = st.text_input("Your question")
if st.button("Ask"):
    prompt = f"""
You must answer grounded ONLY in this feature JSON and escalation info.
If the user asks something you cannot infer, say what additional data would be needed.

Escalation: {escalation}
Features: {features}

Question: {q}
""".strip()

    with st.spinner("Thinking..."):
        ans = generate_text(prompt, SYSTEM_BASE, model=model)
    st.write(ans)
