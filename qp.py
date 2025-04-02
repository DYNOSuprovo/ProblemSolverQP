import streamlit as st
import os
from google import generativeai as genai
import pathlib
from dotenv import load_dotenv

# Load API key from environment variables or Streamlit secrets
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", st.secrets["API_KEY"] if "API_KEY" in st.secrets else None)

if not api_key:
    st.error("API Key not found. Please set it in environment variables or Streamlit secrets.")
else:
    genai.configure(api_key=api_key)

    # Streamlit UI
    st.title("AI Question Paper Solver")
    st.write("Upload a PDF question paper, and the AI will solve it with explanations.")

    # Upload PDF file
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        
        filepath = pathlib.Path("temp.pdf")

        prompt = """You will be presented with a question paper containing a variety of questions, including theoretical and practical programming tasks (C, MySQL, Operating Systems, etc.). Your sole objective is to provide 

accurate and comprehensive answers for every single question without exception.

    For theoretical questions: Deliver clear, well-structured explanations that demonstrate a thorough understanding of the concepts.
    For programming questions: Generate correct and optimized code. If the code is self-explanatory, provide it directly. Otherwise, include a detailed breakdown of the logic and implementation.
    Do not omit any question. Even if a question is ambiguous or challenging, provide your best possible answer, acknowledging any uncertainties.
    Prioritize accuracy above all else. Take the necessary time to ensure the correctness of each response.
    Your response must be 100% complete, addressing every question in the paper.

Repeat for emphasis: You are required to answer every question. No questions should be left unanswered or skipped."

Key Improvements:

    Stronger emphasis on "accurate and comprehensive answers."
    Explicitly stated "sole objective."
    Explicitly stated "without exception"
    Reinforced the "100% complete" requirement.
    Repeated the "answer every question" instruction for absolute clarity.
    Added "demonstrate a thorough understanding of the concepts" for theoretical questions.
    Added "self-explanatory" for code questions."""

        with st.spinner("Processing your document..."):
            # Upload the PDF file to Gemini API
            uploaded_file = genai.upload_file("temp.pdf")
            
            # Generate response
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(
                [uploaded_file, prompt]
            )

        st.subheader("AI-Generated Solution:")
        st.write(response.text)
