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

    st.title("DYNO AI Question Paper Solver")
    st.write("Upload a PDF question paper, and the AI wextract text")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        
        filepath = pathlib.Path("temp.pdf")

        prompt = """NO NEED TO SOLVE THE QUESTION JUST GIVE THE EXTRACTED text FROM file
NO SOLUTION JUST THE text
JUST JIVE THE TEXT FROM THE file IN A USER READABLE FORMAT
you mayget some picture related question try you best to give those in best format by using arrow circle if you can this you might get in automata and formala language or dbmse"""

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
