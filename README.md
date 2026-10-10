# ai-screening-agent
# 🛡️ Enterprise AI-Powered Code Review & Resume Screening Agent

A production-grade, type-safe automated evaluation engine built with **Python**, **Streamlit**, and the **Google GenAI SDK (`gemini-3.5-flash`)**. This agent enforces strict schema validation using **Pydantic** to deliver deterministic, machine-readable JSON evaluation reports for technical code reviews and candidate resume screenings.

---

## 🌟 Key Features
1. **Native Structured Outputs:** Utilizes Gemini's native schema enforcement (`response_mime_type="application/json"`) mapped directly to Pydantic models to guarantee valid JSON formatting.
2. **Rigorous Persona Prompting:** Configured with low-temperature settings (`temperature=0.2`) and strict system instructions acting as a Principal Tech Lead.
3. **Comprehensive Metrics Reporting:** Automatically categorizes scores, pass/fail status, key technical strengths, structural vulnerabilities, and actionable recommendations.

---

## 🚀 Cloud Deployment & Usage
This application is designed for zero-dependency cloud execution via Streamlit Cloud, integrating secure environment secrets for API key management.
