# Wearable Agent Prototype (Streamlit)

A small demo of a **bounded, uncertainty-aware agentic layer** on top of wearable-like daily signals.
- Feature extraction + data quality
- Rule-based escalation (LLM does not decide)
- LLM-generated user summary + clinician note
- One-step "agentic" clarifying question loop

## Run on Streamlit Community Cloud
1. Fork or use this repo.
2. Go to Streamlit Community Cloud and deploy the repo.
3. Add a secret:
   - Key: `OPENAI_API_KEY`
   - Value: your OpenAI API key

## Data format
CSV columns:
- `date`
- `steps`
- `resting_hr`
- `sleep_hours`
- `sleep_efficiency`
- `hrv_proxy`
- `wear_time_hours`
- optional: `notes`
