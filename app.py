# Importing Necessary Libraries
import streamlit as st
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import os
import time
from pypdf import PdfReader
from docx import Document

st.set_page_config(page_title="Enterprise AI Screening Agent", page_icon="🛡️", layout="wide")

# Initialize Gemini Client using Streamlit secrets or environment variables
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 Missing Gemini API Key. Please configure it in your Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

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

# File Uploader for PDF, DOCX, and TXT files
uploaded_file = st.file_uploader(
    f"Upload the {target_type} file (PDF, DOCX, or TXT):", 
    type=["pdf", "docx", "txt"]
)

user_content = ""

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_extension == "txt":
            user_content = uploaded_file.read().decode("utf-8")
        elif file_extension == "pdf":
            reader = PdfReader(uploaded_file)
            user_content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif file_extension == "docx":
            doc = Document(uploaded_file)
            user_content = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])
        st.success(f"Successfully loaded: **{uploaded_file.name}**")
    except Exception as e:
        st.error(f"Error parsing file: {e}")

# Fallback text area if no file is uploaded
if not user_content:
    user_content = st.text_area(
        f"Or paste the raw text of the {target_type} to evaluate below:",
        height=250,
        placeholder=f"Paste raw {target_type} data here..."
    )

if st.button("Run AI Evaluation 🚀", type="primary"):
    if not user_content.strip():
        st.warning("Please upload a file or provide input text to analyze.")
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

                    # Switched to gemini-3.5-flash-lite for maximum stability and lower traffic saturation
                    response = client.models.generate_content(
                        model='gemini-3.5-flash-lite',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=EvaluationReport,
                            temperature=0.2
                        ),
                    )
                    success = True
                    break # Exit retry loop if successful
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(2) # Wait 2 seconds before retrying
                        continue
                    else:
                        raise e

            if success and response:
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
