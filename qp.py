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

        prompt = """You will be given a question paper with multiple questions, including theoretical and programming-related ones (C, MySQL, OS, etc.). Your task is to analyze the entire question paper and provide answers for each and every question—without skipping any.

For theoretical questions, provide clear, structured explanations.

For programming questions, generate correct and optimized code. If the code alone is sufficient, you may skip the explanation, but otherwise, include a proper breakdown.

Do not leave any question unanswered. Even if a question is ambiguous, attempt to answer it to the best of your ability.

Accuracy is the top priority—take as much time as needed to ensure correctness.

Your response must be complete, covering 100% of the questions.

If necessary, repeat: You must answer every single question on the paper. No skipping. No omissions"""

        with st.spinner("Processing your document..."):
            # Upload the PDF file to Gemini API
            uploaded_file = genai.upload_file("temp.pdf")
            
            # Generate response
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(
                [uploaded_file, prompt]
            )

        st.subheader("AI-Generated Solution:")
        st.write(response.text)
