# Wearable Agent Prototype: Open-source Implementation
**S. M. Riazul Islam**

A lightweight research prototype demonstrating a **bounded, uncertainty-aware agentic layer**
built on top of wearable-style daily aggregate signals. The system illustrates how deterministic
processing, rule-based control, and LLM-powered interpretation can be combined in a
human-in-the-loop digital health workflow.

### Key features
- Deterministic feature extraction and data quality assessment
- Transparent, rule-based escalation (LLM does not make escalation decisions)
- LLM-generated user-facing summaries and clinician-style notes
- One-step agentic clarification loop constrained by system rules
- Interactive web interface with exportable artifacts

---

## Live demo
🔗 **Streamlit Community Cloud:**  
https://wearable-agent-prototype.streamlit.app/

---

## Deployment (Streamlit Community Cloud)
1. Fork or clone this repository.
2. Deploy the repository on Streamlit Community Cloud.
3. Add a secret in Streamlit settings:
   - **Key:** `OPENAI_API_KEY`
   - **Value:** your OpenAI API key

No local installation is required.

---

## Data handling
The prototype operates on **wearable-style daily aggregates** rather than raw sensor streams.

### Expected CSV columns
Required:
- `date`
- `steps`
- `resting_hr`
- `sleep_hours`
- `sleep_efficiency`
- `hrv_proxy`
- `wear_time_hours`

Optional:
- `notes` (free-text contextual annotation)

Sample datasets are provided in the `data/` directory, and a built-in simulator can generate
plausible longitudinal patterns for demonstration purposes.

---

## Prototype scope and limitations
This application is intended **for research and demonstration purposes only**.  
It does not provide medical diagnosis, treatment recommendations, or clinical decision-making.
All LLM outputs are constrained by system-level rules and are designed to support
interpretation and communication rather than autonomous action.

---

## How to cite
S. M. R. Islam, “Wearable Agent Prototype: Open-source Implementation,”
GitHub repository, 2026. [Online]. Available:
https://github.com/<your-username>/wearable-agent-prototype


## License
MIT License
