import os
import streamlit as st

from src.storage import init_state
from src.ui import render_header
from src.prompts import SYSTEM_BASE
from src.llm import generate_text  


init_state()
render_header("4) Chat")

demo_mode = st.session_state.get("demo_mode", False)
model = st.session_state.get("selected_model", "gpt-4.1-mini")

# Basic checks
if os.environ.get("OPENAI_API_KEY") is None:
    st.warning("OPENAI_API_KEY not set. Add it in Streamlit Cloud → App → Settings → Secrets.")
    st.stop()

df = st.session_state.get("df")
features = st.session_state.get("features")
escalation = st.session_state.get("escalation")

with st.sidebar:
    st.markdown("### Chat Tools")
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

    if not demo_mode:
        with st.expander("Context (debug)"):
            st.write("Features loaded:", features is not None)
            st.write("Escalation loaded:", escalation is not None)

# Initialize chat state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

st.subheader("Agent chat")

# Provide gentle guidance
if df is None:
    st.info("Tip: Load data first in **1) Data** to enable context-aware responses.")
elif features is None or escalation is None:
    st.info("Tip: Visit **2) Trends & Quality** and **3) Agent Summary** to compute features/escalation.")

# Render history
for m in st.session_state.chat_messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input
user_msg = st.chat_input("Ask about trends, data quality, or what the summaries mean...")

if user_msg:
    # Save user message
    st.session_state.chat_messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Build a bounded context prompt (keep it short & safe)
    context_bits = []
    if features is not None:
        context_bits.append(f"FEATURES_SUMMARY:\n{features}")
    if escalation is not None:
        context_bits.append(f"ESCALATION:\n{escalation}")

    context_text = "\n\n".join(context_bits) if context_bits else "No wearable context available."

    prompt = (
        "You are a helpful assistant for a wearable-data prototype. "
        "Do not provide diagnosis or treatment. "
        "Explain patterns, uncertainty, and next steps that involve human review.\n\n"
        f"{context_text}\n\n"
        f"USER QUESTION:\n{user_msg}\n"
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_msg = generate_text(prompt, SYSTEM_BASE, model=model)
            st.markdown(assistant_msg)

    st.session_state.chat_messages.append({"role": "assistant", "content": assistant_msg})
