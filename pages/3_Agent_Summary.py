from src.ui import render_header

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

st.title("3) Agent Summary (bounded + agentic)")

df = st.session_state.df
if df is None:
    st.warning("Load data first in the Data page.")
    st.stop()

# ---- Compute features ----
if st.session_state.features is None:
    try:
        st.session_state.features = compute_features(df)
    except Exception as e:
        st.error(str(e))
        st.stop()

features = st.session_state.features

# ---- Rule-based escalation ----
if st.session_state.escalation is None:
    st.session_state.escalation = determine_escalation(features)

escalation = st.session_state.escalation

st.subheader("Rule-based escalation (LLM does NOT decide this)")
st.write(
    f"**Level:** {escalation['level'].upper()} &nbsp;|&nbsp; "
    f"**Confidence:** {escalation['confidence'].upper()}"
)

st.write("**Rationale:**")
for r in escalation["rationale"]:
    st.write(f"- {r}")

with st.expander("Detected flags"):
    st.json(escalation["flags"])

st.divider()
st.subheader("LLM-generated summaries")

# ---- API key check ----
if os.environ.get("OPENAI_API_KEY") is None:
    st.warning("OPENAI_API_KEY not set. Add it in Streamlit Cloud → App → Settings → Secrets.")
    st.stop()

model = st.selectbox(
    "Model",
    ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
    index=0,
)

user_context = st.text_input(
    "Optional context (travel, illness symptoms, schedule changes, etc.)",
    "",
)

col1, col2 = st.columns(2)

# ---- Initial generation ----
with col1:
    if st.button("Generate initial summaries"):
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

# ---- Clarifying question ----
with col2:
    if st.button("Ask clarifying question (agentic step)"):
        q_prompt = build_clarifying_question_prompt(features, escalation)
        with st.spinner("Generating clarifying question..."):
            st.session_state.clarifying_q = generate_text(
                q_prompt, SYSTEM_BASE, model=model
            ).strip()
        st.session_state.clarifying_a = None

# =========================================================
# Display outputs + exports
# =========================================================

if st.session_state.agent_outputs:
    st.write("### User summary")
    st.write(st.session_state.agent_outputs["user_summary"])

    st.write(f"### Clinician note (version: {st.session_state.agent_outputs['version']})")
    clinician_note = st.session_state.agent_outputs["clinician_note"]
    st.write(clinician_note)

    # ---- Concise re-generation ----
    if st.button("♻️ Re-generate clinician note (concise)"):
        concise_prompt = _build_concise_clinician_prompt(
            features, escalation, user_context
        )
        with st.spinner("Re-generating concise clinician note..."):
            concise_note = generate_text(concise_prompt, SYSTEM_BASE, model=model)

        st.session_state.agent_outputs["clinician_note"] = concise_note
        st.session_state.agent_outputs["version"] = "concise"
        st.session_state.agent_outputs["meta"] = {
            "model": model,
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        st.success("Clinician note updated (concise).")

    # ---- Exports ----
    meta = st.session_state.agent_outputs["meta"]
    export_text = _format_clinician_note_with_meta(
        clinician_note, features, meta
    )

    st.download_button(
        "⬇️ Download clinician note (.txt)",
        export_text,
        file_name=_clinician_note_filename(features),
        mime="text/plain",
    )

    html_export = _clinician_note_html(export_text)
    st.download_button(
        "⬇️ Download clinician note (print-ready HTML → PDF)",
        html_export,
        file_name=_clinician_note_filename(features).replace(".txt", ".html"),
        mime="text/html",
    )

# =========================================================
# Agentic clarification loop
# =========================================================

st.divider()
st.subheader("Clarifying question loop")

if st.session_state.clarifying_q:
    st.info(st.session_state.clarifying_q)

    answer = st.text_area(
        "Your answer",
        value=st.session_state.clarifying_a or "",
        height=80,
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

        st.session_state.agent_outputs["user_summary_updated"] = updated

if (
    st.session_state.agent_outputs
    and "user_summary_updated" in st.session_state.agent_outputs
):
    st.write("### Updated user summary")
    st.write(st.session_state.agent_outputs["user_summary_updated"])
