import streamlit as st

st.set_page_config(
    page_title="Wearable Agent Prototype",
    page_icon="⌚",
    layout="wide",
)

st.title("⌚ Wearable Agent Prototype")
st.write(
    """
This prototype demonstrates a **bounded, uncertainty-aware agentic layer** on top of wearable-like time series.
Use the pages in the sidebar:

- **Data**: upload CSV or generate simulated data
- **Trends & Quality**: view trends and data coverage
- **Agent Summary**: rule-based escalation + LLM summaries + clarifying question loop
- **Chat**: ask questions grounded in computed features
"""
)

with st.expander("CSV format expected"):
    st.code(
        """date,steps,resting_hr,sleep_hours,sleep_efficiency,hrv_proxy,wear_time_hours,notes
2026-01-01,8200,57,7.2,0.88,52,18,""
2026-01-02,7600,58,6.9,0.86,49,17,"late dinner"
""",
        language="text",
    )
