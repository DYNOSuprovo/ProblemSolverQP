import streamlit as st
import os
import google.generativeai as genai
import pathlib
from dotenv import load_dotenv
import time # Import time for potential delays/checks if needed

# --- Configuration ---

# Load API key from environment variables or Streamlit secrets
load_dotenv()
# Use st.secrets first if available, then fallback to os.getenv
# Ensure your secret key in Streamlit is named "API_KEY"
api_key = st.secrets.get("API_KEY") or os.getenv("GOOGLE_API_KEY")

# --- Streamlit UI Setup ---
st.set_page_config(layout="wide") # Optional: Use wider layout
st.title("AI Question Paper Solver")
st.write("Upload a PDF question paper, and the AI will attempt to solve it with explanations.")
st.markdown("---") # Add a visual separator

# --- API Key Check and Configuration ---
if not api_key:
    st.error("Google API Key not found. Please set it in environment variables (GOOGLE_API_KEY) or Streamlit secrets (API_KEY).")
    st.stop() # Stop execution if no key
else:
    try:
        genai.configure(api_key=api_key)
        st.success("Google Generative AI configured successfully.")
    except Exception as e:
        st.error(f"Error configuring Google Generative AI: {e}")
        st.stop() # Stop execution if configuration fails

# --- File Upload ---
uploaded_file = st.file_uploader(
    "Choose a PDF file containing the question paper:",
    type=["pdf"],
    help="Upload the PDF document you want the AI to analyze and solve."
)

# --- Main Processing Logic ---
if uploaded_file is not None:
    st.info(f"Processing uploaded file: '{uploaded_file.name}' ({uploaded_file.size / 1024:.2f} KB)")

    # Save the uploaded file temporarily
    temp_dir = pathlib.Path("temp_files")
    temp_dir.mkdir(exist_ok=True) # Ensure the temp directory exists
    temp_pdf_path = temp_dir / f"temp_{uploaded_file.name}"
    question_paper_file = None # Initialize variable

    try:
        # Write uploaded content to the temporary file
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getvalue()) # Use getvalue() for uploaded file bytes

        # --- File Upload to Gemini API ---
        upload_spinner = st.spinner("Uploading PDF to Google Cloud...")
        with upload_spinner:
            try:
                # Upload the file to Gemini API
                question_paper_file = genai.upload_file(
                    path=temp_pdf_path,
                    display_name=uploaded_file.name,
                    # Optional: Mime type can be specified if needed, but usually inferred
                    # mime_type="application/pdf"
                )
                st.success(f"'{uploaded_file.name}' uploaded successfully to Google Cloud!")

                # Optional: Wait for file processing (can add robustness for complex PDFs)
                # print(f"Uploaded file '{question_paper_file.display_name}' as: {question_paper_file.uri}")
                # while question_paper_file.state.name == "PROCESSING":
                #     st.info("Waiting for Google to process the file...")
                #     time.sleep(5) # Check every 5 seconds
                #     question_paper_file = genai.get_file(question_paper_file.name) # Update file state
                #
                # if question_paper_file.state.name == "FAILED":
                #      st.error("Google failed to process the PDF file.")
                #      # Clean up local file before stopping
                #      if temp_pdf_path.exists():
                #          os.remove(temp_pdf_path)
                #      st.stop()
                # elif question_paper_file.state.name == "ACTIVE":
                #     st.info("File processing complete.")

            except Exception as e:
                st.error(f"Error uploading file to Google Cloud: {e}")
                # Clean up local file before stopping
                if temp_pdf_path.exists():
                    os.remove(temp_pdf_path)
                st.stop() # Stop if upload fails

        # --- Prompt Definition ---
        prompt = """You are an expert AI Teaching Assistant. Your task is to meticulously analyze the provided PDF document, which contains an academic question paper.

Follow these instructions precisely:
1.  **Identify All Questions:** Go through the document and identify every single question asked.
2.  **Sequential Answering:** Answer the questions in the order they appear in the document. Clearly label each answer (e.g., "Answer to Q1(a):", "Solution for Section B, Question 3:").
3.  **Detailed Explanations:** For each question, provide a comprehensive, step-by-step explanation of the solution. Think like a teacher explaining the concept and the steps to a student. Show your reasoning.
4.  **Code Generation (If Applicable):** If a question requires writing code (e.g., C, C++, Python, SQL, OS commands), provide well-commented, functional code snippets. Explain the logic behind the code.
5.  **Accuracy and Completeness:** Prioritize correctness and ensure every part of every question is addressed. Do not skip any questions or sub-parts.
6.  **Clarity and Formatting:** Use Markdown for clear formatting (headings, bold text, bullet points, code blocks) to make the solution easy to read and understand.
7.  **Thoroughness:** Take the necessary time to generate high-quality, detailed answers. Accuracy is more important than speed.

Begin solving the questions from the provided PDF now."""

        # --- Model Configuration ---
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest", # Use a powerful model capable of handling PDF input and complex instructions
                generation_config={"temperature": 0.6}, # Adjust temperature for creativity vs predictability
                # Optional: Configure safety settings if needed (use defaults unless issues arise)
                # safety_settings=[...]
            )
        except Exception as e:
            st.error(f"Error creating Generative Model: {e}")
             # Clean up local file before stopping
            if temp_pdf_path.exists():
                os.remove(temp_pdf_path)
            # Attempt to delete the cloud file if it was uploaded
            if question_paper_file:
                try:
                    genai.delete_file(question_paper_file.name)
                except Exception: pass # Ignore delete error if model creation failed
            st.stop()

        # --- Content Generation (Streaming) ---
        st.markdown("---") # Separator
        st.subheader("AI-Generated Solution:")
        solution_placeholder = st.empty() # Create a placeholder for the streaming output
        solution_placeholder.info("Generating solutions... This may take some time depending on the paper's length and complexity.")

        try:
            # Start generation with stream=True
            response_stream = model.generate_content(
                [prompt, question_paper_file], # Pass the prompt and the Gemini file object
                stream=True,
                # Optional: Increase timeout for very long tasks, though streaming helps
                # request_options={'timeout': 600} # e.g., 10 minutes
            )

            # --- Helper generator function to yield text ---
            def stream_text_generator(stream):
                """Yields text chunks from the Gemini stream, handling potential errors."""
                full_response_text = ""
                try:
                    for chunk in stream:
                        if chunk.text:
                            # print(f"Received chunk: {chunk.text[:50]}...") # Debugging print
                            full_response_text += chunk.text
                            yield chunk.text
                            time.sleep(0.01) # Small delay for smoother streaming effect
                        # You could potentially check chunk.prompt_feedback or safety_ratings here if needed per chunk
                except Exception as e:
                    st.error(f"Error while streaming response: {e}")
                    # Attempt to get feedback even on streaming error
                    try:
                        st.warning(f"Prompt Feedback (if available): {stream.prompt_feedback}")
                    except Exception:
                        st.warning("Could not retrieve prompt feedback after streaming error.")
                # Once done, you could log the full response if needed
                # print("Streaming finished.")
                # st.session_state['full_response'] = full_response_text # Store if needed

            # --- Use the helper generator with st.write_stream ---
            # Display the streamed text in the placeholder
            solution_placeholder.write_stream(stream_text_generator(response_stream))

            # --- Final Status Check (Optional) ---
            # Accessing final feedback *after* the stream is fully consumed
            # might be unreliable. Error handling within the generator is often better.
            # We'll assume success if the stream completed without errors caught above.
            st.success("Solution generation process finished.")
            # You could try accessing feedback here, but it might fail if the object state is lost:
            # try:
            #     st.info(f"Final Prompt Feedback: {response_stream.prompt_feedback}")
            #     if response_stream.candidates:
            #         st.info(f"Final Finish Reason: {response_stream.candidates[0].finish_reason}")
            # except Exception as e:
            #     st.warning(f"Could not retrieve final stream details: {e}")


        except Exception as e:
            solution_placeholder.empty() # Clear the placeholder on error
            st.error(f"Error during content generation: {e}")
            # Attempt to access prompt feedback if the error object contains it
            # (This depends on the specific exception type from the SDK)
            if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
                 st.warning(f"Prompt Feedback from Error: {e.response.prompt_feedback}")
            else:
                 st.warning("Could not retrieve prompt feedback after generation error.")

    finally:
        # --- Cleanup ---
        # Clean up the temporary local file
        if temp_pdf_path.exists():
            try:
                os.remove(temp_pdf_path)
                # print(f"Removed temporary file: {temp_pdf_path}") # Debugging print
            except Exception as e:
                st.warning(f"Could not remove temporary file {temp_pdf_path}: {e}")

        # Clean up the file uploaded to Gemini API (Good Practice)
        if question_paper_file:
            try:
                delete_spinner = st.spinner(f"Deleting '{question_paper_file.display_name}' from Google Cloud...")
                with delete_spinner:
                    genai.delete_file(question_paper_file.name)
                    st.info(f"Deleted temporary file '{question_paper_file.display_name}' from Google Cloud.")
            except Exception as e:
                st.warning(f"Could not delete file '{question_paper_file.name}' from Google Cloud: {e}. Manual cleanup might be needed.")

else:
    st.info("Please upload a PDF file to start.")

st.markdown("---")
st.write("Disclaimer: AI-generated solutions may contain errors. Always verify the answers.")
