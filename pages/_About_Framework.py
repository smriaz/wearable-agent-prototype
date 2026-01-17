from pathlib import Path
import streamlit as st

from src.storage import init_state
from src.ui import render_header


init_state()
render_header("About / Framework")
demo_mode = st.session_state.get("demo_mode", False)

st.write(
    "This page provides a high-level view of the prototype framework"
)

# --- Links (you can edit these)
GITHUB_URL = "https://github.com/smriaz/wearable-agent-prototype"
STREAMLIT_URL = "https://wearable-agent-prototype.streamlit.app/"

c1, c2 = st.columns(2)
with c1:
    st.link_button("🔗 GitHub Repository", GITHUB_URL, use_container_width=True)
with c2:
    st.link_button("🔗 Live Streamlit App", STREAMLIT_URL, use_container_width=True)

st.divider()

with st.expander("Prototype disclaimer", expanded=demo_mode):
    st.write(
        "This is a research prototype intended to illustrate design principles for "
        "LLM-powered agentic systems with wearable-style data. "
        "Developed by S. M. Riazul Islam at the University of Aberdeen."
    )

st.subheader("Implementation framework")

# Framework image at: assets/framework.png
img_path = Path("assets/framework.png")
if img_path.exists():
    st.image(str(img_path), caption="Prototype implementation framework.", use_container_width=True)
else:
    st.info(
        "Framework image not found"
    )

st.write(
    "How to cite: S.M.R. Islam, “Wearable Agent Prototype: Interactive demonstration,” Streamlit
Community Cloud, 2026. [Online]"
)
