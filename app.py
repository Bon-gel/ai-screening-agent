# Importing Necessary Libraries
import streamlit as st
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError
import os
import time
import random

st.set_page_config(page_title="Enterprise AI Screening Agent", page_icon="🛡️", layout="wide")

# Initialize Gemini Client with caching for optimal lifecycle management
@st.cache_resource
def get_gemini_client(api_key: str):
    return genai.Client(api_key=api_key)

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 Missing Gemini API Key. Please configure it in your Streamlit Secrets.")
    st.stop()

client = get_gemini_client(api_key)

# Define strict Pydantic Schema for structured enterprise output
class EvaluationReport(BaseModel):
    candidate_or_code_name: str = Field(description="Name of the file, candidate, or script analyzed.")
    overall_score: int = Field(description="Score from 0 to 100 based on quality and compliance.")
    status: str = Field(description="Must be 'Approved', 'Review Required', or 'Rejected'")
    key_strengths: list[str] = Field(description="List of top 3 technical or structural strengths identified.")
    weaknesses_or_bugs: list[str] = Field(description="List of detected vulnerabilities, gaps, or bugs.")
    actionable_recommendations: list[str] = Field(description="Step-by-step guidance to fix or improve the submission.")

st.title("🛡️ Enterprise AI-Powered Screening Agent")
st.caption("Automated Code Review & Resume Evaluation Engine via Gemini Structured Outputs")

# Sidebar options
with st.sidebar:
    st.header("⚙️ Evaluation Parameters")
    target_type = st.selectbox("Select Target Type", ["resume", "code"])
    st.info("This agent uses Pydantic schema validation to guarantee clean, machine-readable JSON reports from Gemini.")

# Text input area with character count tracking
user_content = st.text_area(
    f"Paste the raw text of the {target_type} to evaluate below:",
    height=250,
    placeholder=f"Paste raw {target_type} data here..."
)

# Input length validation check
MAX_CHARS = 15000

if st.button("Run AI Evaluation 🚀", type="primary"):
    if not user_content.strip():
        st.warning("Please provide input text to analyze.")
    elif len(user_content) > MAX_CHARS:
        st.error(f"⚠️ Input is too long ({len(user_content)} characters). Please keep submissions under {MAX_CHARS} characters to prevent context overflow.")
    else:
        with st.spinner("Analyzing submission against enterprise benchmarks..."):
            max_retries = 3
            success = False
            response = None
            
            for attempt in range(max_retries):
                try:
                    prompt = (
                        f"You are a rigorous Principal Tech Lead and Enterprise Recruiter. "
                        f"Analyze the following {target_type} with extreme scrutiny:\n\n"
                        f"\"\"\"\n{user_content}\n\"\"\""
                    )

                    # Using standard production model with robust configuration
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=EvaluationReport,
                            temperature=0.2
                        ),
                    )
                    success = True
                    break
                except APIError as api_err:
                    if api_err.code == 503 and attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                        time.sleep(sleep_time)
                        continue
                    else:
                        st.error(f"API Error Encountered: {api_err}")
                        break
                except Exception as e:
                    st.error(f"Unexpected Processing Exception: {e}")
                    break

            if success and response:
                try:
                    # Parsed response matching the Pydantic model
                    report = response.parsed

                    # Render dashboard report visually
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="Target Analyzed", value=report.candidate_or_code_name)
                        st.metric(label="Overall Score", value=f"{report.overall_score} / 100")
                    with col2:
                        status_color = "🟢" if report.status == "Approved" else "🟡" if report.status == "Review Required" else "🔴"
                        st.markdown(f"### Status: {status_color} **{report.status}**")

                    st.divider()

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.subheader("💡 Key Strengths")
                        for strength in report.key_strengths:
                            st.markdown(f"- ✅ {strength}")

                    with col_b:
                        st.subheader("⚠️ Weaknesses / Bugs")
                        for weakness in report.weaknesses_or_bugs:
                            st.markdown(f"- ❌ {weakness}")

                    st.subheader("🛠️ Actionable Recommendations")
                    for rec in report.actionable_recommendations:
                        st.markdown(f"1. {rec}")

                except Exception as render_err:
                    st.error(f"Dashboard Rendering Exception: {render_err}")
