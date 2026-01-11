from __future__ import annotations
import json


SYSTEM_BASE = """You are a careful health data assistant.
You are NOT a medical device and you do NOT diagnose or give treatment instructions.
You must be conservative, uncertainty-aware, and explicit about data limitations.
You only use the provided JSON features; do not invent measurements.

Safety rules:
- Do not diagnose conditions.
- Do not recommend medications.
- If escalation is "high", advise the user to consider contacting a clinician or local health service, especially if symptoms are present.
- Always include a short "Data confidence" note grounded in coverage.
"""


def _json_block(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def build_user_summary_prompt(features: dict, escalation: dict, user_context: str | None) -> str:
    ctx = user_context.strip() if user_context else ""
    return f"""
Generate a friendly weekly summary for a non-expert user.

Include:
1) What changed vs baseline (2-4 bullets)
2) Possible non-medical explanations (routine, travel, stress, illness symptoms, device adherence), phrased as hypotheses
3) A conservative "What you can do next" section (sleep hygiene, hydration, rest, consistency, note symptoms)
4) Data confidence note (use coverage)
5) If escalation is medium/high: suggest monitoring and consider clinician contact if symptoms or worsening.

User context (optional, may be empty): "{ctx}"

Escalation (rule-based, do not override): {_json_block(escalation)}

Features: {_json_block(features)}
""".strip()


def build_clinician_note_prompt(features: dict, escalation: dict, user_context: str | None) -> str:
    ctx = user_context.strip() if user_context else ""
    return f"""
Write a concise clinician-facing summary (max ~180 words), structured like:

- Time window:
- Data coverage / reliability:
- Key trends vs baseline:
- Notable flags:
- Patient-reported context (if any):
- Suggested follow-up (conservative; do not diagnose; do not prescribe):

Patient context: "{ctx}"

Escalation (rule-based, do not override): {_json_block(escalation)}

Features: {_json_block(features)}
""".strip()


def build_clarifying_question_prompt(features: dict, escalation: dict) -> str:
    return f"""
You may ask AT MOST ONE clarifying question to improve interpretation.
Choose the single best question that can reduce uncertainty.

Ask a short question (one sentence), multiple choice if helpful.
If data coverage is low, prioritize questions about device wear/adherence or context.

Escalation: {_json_block(escalation)}
Features: {_json_block(features)}

Return only the question text.
""".strip()


def build_update_summary_prompt(features: dict, escalation: dict, question: str, answer: str) -> str:
    return f"""
Update the user summary given the user's answer to a clarifying question.
Be consistent with the earlier constraints: no diagnosis, no medication advice, uncertainty-aware.

Clarifying Q: "{question}"
User A: "{answer}"

Escalation (rule-based, do not override): {_json_block(escalation)}
Features: {_json_block(features)}

Output:
- Updated summary (same format as before but slightly shorter)
- One line: "How the answer changed interpretation"
""".strip()
