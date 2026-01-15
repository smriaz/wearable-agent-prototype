# src/ui.py
import streamlit as st

def _chip(label: str, value: str, ok: bool | None = None) -> None:
    """
    Small helper to render a compact 'status chip' without relying on new Streamlit components.
    ok: True -> green-ish, False -> red-ish, None -> neutral
    """
    if ok is True:
        st.success(f"**{label}:** {value}")
    elif ok is False:
        st.error(f"**{label}:** {value}")
    else:
        st.info(f"**{label}:** {value}")

def ensure_model_state() -> None:
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gpt-4.1-mini"


def render_sidebar_controls() -> None:
    """
    Sidebar controls that are safe to show on every page.
    Keep minimal to avoid conflict with page-specific sidebars.
    """
    ensure_demo_mode_state()
    ensure_model_state()

    with st.sidebar:
        st.markdown("### Prototype Controls")

        st.session_state.demo_mode = st.toggle(
            "Demo mode (clean screenshots)",
            value=st.session_state.demo_mode,
            help="Hides raw tables and reduces visual clutter for demos/screenshots.",
        )

        st.session_state.selected_model = st.selectbox(
            "LLM model",
            ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
            index=["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"].index(st.session_state.selected_model)
            if st.session_state.selected_model in ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"]
            else 0,
            help="Selected once for the session; used by agent summary and chat.",
        )

def render_header(page_title: str) -> None:
    """
    Render a consistent header + status chips.
    Call this at the top of each page after init_state().
    """
    render_sidebar_controls()

    st.title(page_title)

    df = st.session_state.get("df", None)
    features = st.session_state.get("features", None)
    escalation = st.session_state.get("escalation", None)
    model = st.session_state.get("selected_model", None)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        _chip("Data", "loaded" if df is not None else "missing", ok=(df is not None))
    with c2:
        _chip("Features", "ready" if features is not None else "pending", ok=(features is not None))
    with c3:
        _chip("Escalation", "ready" if escalation is not None else "pending", ok=(escalation is not None))
    with c4:
        _chip("Model", model if model else "not set", ok=None)

    st.divider()
