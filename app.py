import streamlit as st

st.set_page_config(
    page_title="Wearable Agent Prototype",
    page_icon="⌚",
    layout="wide",
)

# --- Hero header ---
st.markdown("# ⌚ Wearable Agent Prototype")
st.caption(
    "A lightweight research demo."
)

st.divider()

# --- Overview + Quick cards ---
left, right = st.columns([1.35, 1], gap="large")

with left:
    st.markdown(
        """
This prototype demonstrates a **bounded, uncertainty-aware agentic layer** on top of wearable-like time series.
Use the pages in the sidebar to follow a simple workflow:
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

with right:
    st.markdown("### Quick start")
    st.markdown(
        """
1. Load a dataset in **Data** (sample/upload/simulate)  
2. Review patterns in **Trends & Quality**  
3. Generate outputs in **Agent Summary**  
4. Ask follow-ups in **Chat**
"""
    )
    st.caption("Tip: If you enabled **Demo mode** in the sidebar, tables/debug views are hidden for clean screenshots.")

st.divider()

# --- Simple “cards” for aesthetic structure (no CSS) ---
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.subheader("STEP 1 Data")
    st.caption("Upload / sample / simulate")
with c2:
    st.subheader("STEP 2 Trends")
    st.caption("Plots + coverage checks")
with c3:
    st.subheader("STEP 3 Agent")
    st.caption("Escalation + summaries")
with c4:
    st.subheader("STEP 4 Chat")
    st.caption("Questions grounded in features")

st.caption("Open-source prototype (feedback welcome)")
