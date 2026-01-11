from __future__ import annotations

import os
from openai import OpenAI


def _client() -> OpenAI:
    # Streamlit Cloud uses st.secrets; locally environment variable works.
    # We won't import streamlit here to keep it simple.
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def generate_text(prompt: str, system: str, model: str = "gpt-4.1-mini") -> str:
    """
    Minimal call using OpenAI Responses API via the official SDK.
    """
    client = _client()
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    # SDK returns output items; simplest is output_text convenience:
    return resp.output_text
