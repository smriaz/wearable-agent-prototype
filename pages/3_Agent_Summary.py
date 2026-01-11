import os
import streamlit as st

from src.storage import init_state
from src.features import compute_features
from src.rules import determine_escalation
from src.prompts import (
    SYSTEM_BASE,
    build_user_summary_prompt,
    build_clinician_note_prompt,
    build_clarifying_question_prompt,
    build_update_summary_prompt,
)
from src.llm import generate_text


init_state()

st.title("3) Agent Summary (bounded + agentic)")

df = st.session_state.df
if df is None:
    st.warning("Load data first in the Data page.")
    st.stop()

# Ensure features + escalation exist
if st.session_state.features is None:
    try:
        st.session_state.features = compute_features(df)
    except Exception as e:
        st.error(str(e))
        st.stop()

features = st.session_state.features

if st.session_state.escalation is None:
    st.session_state.escalation = determine_escalation(features)

escalation = st.session_state.escalation

st.subheader("Rule-based escalation (LLM does not decide this)")
st.write(f"**Level:** {escalation['level'].upper()} | **Confidence:** {escalation['confidence'].upper()}")
st.write("**Rationale:**")
for r in escalation["rationale"]:
    st.write(f"- {r}")

with st.expander("Flags"):
    st.json(escalation["flags"])

st.divider()
st.subheader("LLM summaries")

key_missing = os.environ.get("OPENAI_API_KEY") is None
if key_missing:
    st.warning("OPENAI_API_KEY not set. In Streamlit Cloud, add it under App → Settings → Secrets.")
    st.stop()

model = st.selectbox("Model", ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"], index=0)
user_context = st.text_input("Optional context (travel, illness symptoms, schedule changes, etc.)", "")

colA, colB = st.columns(2)

with colA:
    if st.button("Generate initial summaries"):
        user_prompt = build_user_summary_prompt(features, escalation, user_context)
        clin_prompt = build_clinician_note_prompt(features, escalation, user_context)

        with st.spinner("Generating user summary..."):
            user_sum = generate_text(user_prompt, SYSTEM_BASE, model=model)

        with st.spinner("Generating clinician note..."):
            clin_sum = generate_text(clin_prompt, SYSTEM_BASE, model=model)

        st.session_state.agent_outputs = {
            "user_summary": user_sum,
            "clinician_note": clin_sum,
        }

with colB:
    if st.button("Ask clarifying question (agentic step)"):
        q_prompt = build_clarifying_question_prompt(features, escalation)
        with st.spinner("Generating clarifying question..."):
            q = generate_text(q_prompt, SYSTEM_BASE, model=model).strip()
        st.session_state.clarifying_q = q
        st.session_state.clarifying_a = None

if st.session_state.agent_outputs:
    st.write("### User summary")
    st.write(st.session_state.agent_outputs["user_summary"])
    st.write("### Clinician note")
    st.write(st.session_state.agent_outputs["clinician_note"])

st.divider()
st.subheader("Clarifying question loop")

if st.session_state.clarifying_q:
    st.info(st.session_state.clarifying_q)
    answer = st.text_area("Your answer", value=st.session_state.clarifying_a or "", height=80)
    if st.button("Update summary using my answer"):
        st.session_state.clarifying_a = answer

        upd_prompt = build_update_summary_prompt(
            features, escalation, st.session_state.clarifying_q, answer
        )
        with st.spinner("Updating summary..."):
            upd = generate_text(upd_prompt, SYSTEM_BASE, model=model)

        # Overwrite/append user summary with updated one
        if st.session_state.agent_outputs is None:
            st.session_state.agent_outputs = {}
        st.session_state.agent_outputs["user_summary_updated"] = upd

if st.session_state.agent_outputs and "user_summary_updated" in st.session_state.agent_outputs:
    st.write("### Updated user summary")
    st.write(st.session_state.agent_outputs["user_summary_updated"])
