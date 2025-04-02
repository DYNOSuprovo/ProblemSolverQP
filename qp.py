import streamlit as st
import os
import google.generativeai as genai
import pathlib
from dotenv import load_dotenv
import time # Import time for potential delays/checks if needed

# Load API key from environment variables or Streamlit secrets
load_dotenv()
# Use st.secrets first if available, then fallback to os.getenv
api_key = st.secrets.get("API_KEY") or os.getenv("GOOGLE_API_KEY")


if not api_key:
    st.error("API Key not found. Please set it in environment variables or Streamlit secrets (key should be 'API_KEY').")
else:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Error configuring Generative AI: {e}")
        st.stop() # Stop execution if configuration fails

    # Streamlit UI
    st.title("AI Question Paper Solver")
    st.write("Upload a PDF question paper, and the AI will solve it with explanations.")

    # Upload PDF file
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        temp_pdf_path = pathlib.Path("temp_uploaded_paper.pdf")
        try:
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getvalue()) # Use getvalue() for uploaded file bytes

            # --- File Upload to Gemini ---
            st.info("Uploading PDF to Google...")
            try:
                # It's often better to upload the file *before* the main generation
                # This gives a chance to handle upload errors separately.
                question_paper_file = genai.upload_file(path=temp_pdf_path,
                                                        display_name=uploaded_file.name)
                st.success(f"'{uploaded_file.name}' uploaded successfully!")

                # Wait for the file to be processed. Optional but can help.
                # print(f"Uploaded file '{question_paper_file.display_name}' as: {question_paper_file.uri}")
                # while question_paper_file.state.name == "PROCESSING":
                #     st.info("Waiting for file processing...")
                #     time.sleep(5) # Check every 5 seconds
                #     question_paper_file = genai.get_file(question_paper_file.name) # Update file state

                # if question_paper_file.state.name == "FAILED":
                #      st.error("PDF file processing failed.")
                #      st.stop()


            except Exception as e:
                st.error(f"Error uploading file to Google: {e}")
                st.stop() # Stop if upload fails


            # --- Prompt and Model Generation ---
            # Refined Prompt (minor tweaks for clarity)
            prompt = """You are an expert teacher tasked with solving a question paper.
Analyze the provided PDF document, which contains a question paper.
Your goal is to provide clear, accurate, and well-explained solutions to ALL questions presented in the paper.
- Answer each question sequentially.
- Provide detailed step-by-step explanations for your reasoning, as a teacher would explain to a student.
- If a question involves programming (e.g., C, SQL, OS concepts), provide functional code snippets where appropriate, along with explanations of the code logic.
- Prioritize accuracy and completeness for every single question. Do not skip any.
- Format your response clearly, perhaps using Markdown for headings, code blocks, and lists.
Take the necessary time to ensure high-quality answers."""

            # Configure the model
            # Ensure you are using a model that supports file input (like gemini-1.5-pro)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest", # Use the latest 1.5 pro model
                # Optional: Adjust safety settings if you suspect false positives,
                # but be cautious as this can allow harmful content.
                # safety_settings=[...]
                generation_config={"temperature": 0.5} # Adjust temperature if needed
            )

            st.subheader("AI-Generated Solution:")
            with st.spinner("Generating solutions... This may take some time depending on the paper length."):
                try:
                    # Use stream=True
                    response_stream = model.generate_content(
                        [prompt, question_paper_file], # Pass the uploaded file object
                        stream=True,
                        # Optional: Request a higher timeout if needed, though streaming mitigates this
                        # request_options={'timeout': 600} # e.g., 10 minutes
                    )

                    # Use st.write_stream to display the response chunks
                    st.write_stream(response_stream)

                    # --- Crucial: Check for Blocked Response AFTER streaming ---
                    # Although st.write_stream handles the display, the underlying stream object
                    # might still contain information about why it finished, especially if blocked.
                    # We need to consume the stream fully to get the final status if st.write_stream
                    # doesn't expose it directly or if an error happened mid-stream.

                    final_response_text = ""
                    finish_reason = None
                    prompt_feedback = None
                    try:
                        # Re-iterate (or capture from st.write_stream if possible) to get final details
                        # Note: st.write_stream consumes the iterator. We might need a different approach
                        # to capture the *final* chunk's metadata if st.write_stream doesn't provide it.
                        # For now, let's assume if it finished streaming without error, it likely wasn't blocked.
                        # If it *does* get blocked mid-stream, an error might occur above.

                        # A more robust way might be to manually iterate and yield/write:
                        # def stream_generator():
                        #    full_text = ""
                        #    final_chunk = None
                        #    try:
                        #        for chunk in response_stream:
                        #            if chunk.text:
                        #                 yield chunk.text
                        #                 full_text += chunk.text
                        #            final_chunk = chunk # Keep track of the last chunk
                        #    except Exception as stream_error:
                        #         st.error(f"Error during streaming: {stream_error}")
                        #         # Potentially inspect final_chunk or response_stream properties here if available
                        #    # After loop, check final status (conceptual)
                        #    # finish_reason = response_stream.finish_reason # This syntax might vary
                        #    # prompt_feedback = response_stream.prompt_feedback # This syntax might vary
                        #    # if finish_reason == "BLOCK": st.warning("Response potentially blocked.")

                        # st.write_stream(stream_generator())

                        st.success("Solution generation complete.") # Display if streaming finishes

                    except Exception as e:
                         st.error(f"An error occurred while processing the response stream: {e}")
                         # Attempt to get feedback even on error
                         try:
                             # This might fail if the response object isn't fully formed
                             st.warning(f"Prompt Feedback: {response_stream.prompt_feedback}")
                             # You might need to inspect the candidate level for finish reason/safety
                             # if response_stream.candidates:
                             #    st.warning(f"Finish Reason: {response_stream.candidates[0].finish_reason}")
                             #    st.warning(f"Safety Ratings: {response_stream.candidates[0].safety_ratings}")
                         except Exception as feedback_error:
                             st.warning(f"Could not retrieve final feedback details: {feedback_error}")


                except Exception as e:
                    st.error(f"Error generating content: {e}")
                    # Attempt to access prompt feedback if the error object contains it
                    # (This depends on the specific exception type from the SDK)
                    if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
                         st.warning(f"Prompt Feedback: {e.response.prompt_feedback}")
                    else:
                         st.warning("Could not retrieve prompt feedback after error.")

        finally:
            # Clean up the temporary file
            if temp_pdf_path.exists():
                os.remove(temp_pdf_path)
            # Clean up the file uploaded to Gemini API (optional, good practice)
            # Need to store question_paper_file variable outside the try block
            # Or handle this differently. For simplicity, skipping delete here,
            # but in production, you might want to manage uploaded files.
            # if 'question_paper_file' in locals() and question_paper_file:
            #     try:
            #         genai.delete_file(question_paper_file.name)
            #         print(f"Deleted file {question_paper_file.name} from Gemini.")
            #     except Exception as delete_error:
            #         print(f"Could not delete file {question_paper_file.name}: {delete_error}")
