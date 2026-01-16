import os
from datetime import datetime
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
from src.ui import render_header


# =========================================================
# Helpers for export & prompts
# =========================================================

def _clinician_note_filename(features: dict) -> str:
    w = features.get("window", {})
    return f"clinician_note_{w.get('start','start')}_to_{w.get('end','end')}.txt"


def _format_clinician_note_with_meta(note: str, features: dict, meta: dict) -> str:
    header = [
        "=== Agent-Generated Clinician Summary ===",
        f"Generated at (UTC): {meta.get('generated_at', 'unknown')}",
        f"Model: {meta.get('model', 'unknown')}",
        f"Time window: {features['window']['start']} → {features['window']['end']}",
        "",
    ]
    return "\n".join(header) + note


def _clinician_note_html(note_text: str) -> str:
    escaped = (
        note_text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
    return f"""
    <html>
      <head>
        <meta charset="utf-8">
        <title>Clinician Note</title>
      </head>
      <body style="font-family: Arial, sans-serif; line-height: 1.4;">
        <pre>{escaped}</pre>
      </body>
    </html>
    """


def _build_concise_clinician_prompt(features: dict, escalation: dict, user_context: str | None) -> str:
    base = build_clinician_note_prompt(features, escalation, user_context)
    return (
        base
        + "\n\n"
        + "Additional instruction: Produce a CONCISE version (max 100 words). "
          "Preserve key facts, data coverage, and follow-up guidance. "
          "Do not add new interpretation."
    )


# =========================================================
# Page logic
# =========================================================

init_state()
render_header("3) Agent Summary")

demo_mode = st.session_state.get("demo_mode", False)
model = st.session_state.get("selected_model", "gpt-4.1-mini")

df = st.session_state.get("df")
if df is None:
    st.warning("Load data first in the Data page.")
    st.stop()

# ---- Compute features (deterministic) ----
if st.session_state.get("features") is None:
    try:
        st.session_state.features = compute_features(df)
    except Exception as e:
        st.error(str(e))
        st.stop()

features = st.session_state.features

# ---- Escalation (rule-based, non-LLM) ----
if st.session_state.get("escalation") is None:
    st.session_state.escalation = determine_escalation(features)

escalation = st.session_state.escalation

# ---- API key check ----
if os.environ.get("OPENAI_API_KEY") is None:
    st.warning("OPENAI_API_KEY not set. Add it in Streamlit Cloud → App → Settings → Secrets.")
    st.stop()

# =========================================================
# Layout: Left = deterministic, Right = agent workspace
# =========================================================

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Escalation (rule-based)")
    st.write(
        f"**Level:** {escalation['level'].upper()}  \n"
        f"**Confidence:** {escalation['confidence'].upper()}"
    )

    st.write("**Rationale:**")
    for r in escalation.get("rationale", []):
        st.write(f"- {r}")

    if not demo_mode:
        with st.expander("Detected flags (debug)"):
            st.json(escalation.get("flags", {}))
    else:
        # Demo mode: keep it clean
        st.caption("Demo mode hides detailed debug outputs.")

with right:
    st.subheader("Agent workspace")

    user_context = st.text_input(
        "Optional context (travel, illness symptoms, schedule changes, etc.)",
        "",
        help="This is appended as context; it does not change rule-based escalation."
    )

    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        if st.button("Generate summaries", use_container_width=True):
            user_prompt = build_user_summary_prompt(features, escalation, user_context)
            clinician_prompt = build_clinician_note_prompt(features, escalation, user_context)

            with st.spinner("Generating user summary..."):
                user_summary = generate_text(user_prompt, SYSTEM_BASE, model=model)

            with st.spinner("Generating clinician note..."):
                clinician_note = generate_text(clinician_prompt, SYSTEM_BASE, model=model)

            st.session_state.agent_outputs = {
                "user_summary": user_summary,
                "clinician_note": clinician_note,
                "version": "full",
                "meta": {
                    "model": model,
                    "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                },
            }

    with action_col2:
        if st.button("Ask clarifying question", use_container_width=True):
            q_prompt = build_clarifying_question_prompt(features, escalation)
            with st.spinner("Generating clarifying question..."):
                st.session_state.clarifying_q = generate_text(q_prompt, SYSTEM_BASE, model=model).strip()
            st.session_state.clarifying_a = None

    # Tabs for outputs
    tabs = st.tabs(["User summary", "Clinician note", "Export", "Clarify & update"])

    # -------------------------
    # Tab 1: User summary
    # -------------------------
    with tabs[0]:
        if st.session_state.get("agent_outputs"):
            st.write(st.session_state.agent_outputs.get("user_summary", ""))
            if st.session_state.agent_outputs.get("user_summary_updated"):
                st.markdown("---")
                st.write("**Updated user summary**")
                st.write(st.session_state.agent_outputs["user_summary_updated"])
        else:
            st.info("Generate summaries to view outputs.")

    # -------------------------
    # Tab 2: Clinician note
    # -------------------------
    with tabs[1]:
        if st.session_state.get("agent_outputs"):
            st.caption(f"Version: {st.session_state.agent_outputs.get('version', 'full')}")
            clinician_note = st.session_state.agent_outputs.get("clinician_note", "")
            st.write(clinician_note)

            # concise regeneration
            if st.button("♻️ Re-generate clinician note (concise)"):
                concise_prompt = _build_concise_clinician_prompt(features, escalation, user_context)
                with st.spinner("Re-generating concise clinician note..."):
                    concise_note = generate_text(concise_prompt, SYSTEM_BASE, model=model)

                st.session_state.agent_outputs["clinician_note"] = concise_note
                st.session_state.agent_outputs["version"] = "concise"
                st.session_state.agent_outputs["meta"] = {
                    "model": model,
                    "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                }
                st.success("Clinician note updated (concise).")
        else:
            st.info("Generate summaries to view outputs.")

    # -------------------------
    # Tab 3: Export
    # -------------------------
    with tabs[2]:
        if st.session_state.get("agent_outputs"):
            clinician_note = st.session_state.agent_outputs.get("clinician_note", "")
            meta = st.session_state.agent_outputs.get("meta", {})
            export_text = _format_clinician_note_with_meta(clinician_note, features, meta)

            with st.expander("Provenance"):
                st.write(f"**Generated at (UTC):** {meta.get('generated_at', 'unknown')}")
                st.write(f"**Model:** {meta.get('model', 'unknown')}")
                st.write(f"**Window:** {features['window']['start']} → {features['window']['end']}")
                st.write(f"**Escalation:** {escalation['level'].upper()} / {escalation['confidence'].upper()}")

            st.download_button(
                "⬇️ Download clinician note (.txt)",
                export_text,
                file_name=_clinician_note_filename(features),
                mime="text/plain",
                use_container_width=True,
            )

            html_export = _clinician_note_html(export_text)
            st.download_button(
                "⬇️ Download (print-ready HTML → PDF)",
                html_export,
                file_name=_clinician_note_filename(features).replace(".txt", ".html"),
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.info("Generate summaries first to enable exports.")

    # -------------------------
    # Tab 4: Clarify & update
    # -------------------------
    with tabs[3]:
        if st.session_state.get("clarifying_q"):
            st.info(st.session_state.clarifying_q)

            answer = st.text_area(
                "Your answer",
                value=st.session_state.get("clarifying_a") or "",
                height=90,
            )

            if st.button("Update summary using my answer"):
                st.session_state.clarifying_a = answer

                upd_prompt = build_update_summary_prompt(
                    features,
                    escalation,
                    st.session_state.clarifying_q,
                    answer,
                )

                with st.spinner("Updating summary..."):
                    updated = generate_text(upd_prompt, SYSTEM_BASE, model=model)

                if not st.session_state.get("agent_outputs"):
                    st.session_state.agent_outputs = {}
                st.session_state.agent_outputs["user_summary_updated"] = updated
                st.success("User summary updated.")
        else:
            st.info("Click “Ask clarifying question” to run the agentic step.")
