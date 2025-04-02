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

        prompt = """You will be given a question paper. Analyze it and solve all questions with proper explanations like a teacher. You may need to generate code for programming-related questions (C, MySQL, OS, etc.). If code is required, give a proper solution to and explanation take as much time as you want but givw the answer take your time find the solution and give the answer
        and you must answer all the question each and every question dont worry about the time focus on accuracy and give the soluton"""

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
