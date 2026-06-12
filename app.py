import streamlit as st
import os
from dotenv import load_dotenv
from sarvamai import SarvamAI
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import requests

load_dotenv()

# Configure Sarvam
sarvam_client = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY"),
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.title("Note Assistant")

# Upload audio
uploaded_file = st.file_uploader(
    "Upload Meeting Recording",
    type=["mp3", "wav", "m4a"]
)

st.divider()
st.subheader("🎤 Or Record Audio")

recorded_audio = mic_recorder(
    start_prompt="🎤 Start Recording",
    stop_prompt="⏹️ Stop Recording",
    key="recorder",
)

if recorded_audio:
    st.audio(recorded_audio["bytes"])

# Play uploaded audio
if uploaded_file:
    st.subheader("Original Audio")
    st.audio(uploaded_file)

# Only proceed if a file is uploaded
if (uploaded_file or recorded_audio) and st.button("Process Meeting Audio"):

    with st.spinner("Transcribing with Sarvam..."):

        if uploaded_file:
            audio_file = uploaded_file

        elif recorded_audio:
            import io
            audio_file = io.BytesIO(recorded_audio["bytes"])
            audio_file.name = "recording.wav"

        response = sarvam_client.speech_to_text.transcribe(
            file=audio_file,
            model="saaras:v3",
            mode="codemix"
        )

    transcript = response.transcript

    st.subheader("📝 Transcript")
    st.write(transcript)

    with st.spinner("Generating summary with Gemini..."):
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
Summarize this meeting transcript into:
1. Executive Summary
2. Action Items
3. Draft Follow-up Email

Transcript:
{transcript}
"""

        gemini_response = model.generate_content(prompt)

    st.subheader("📌 Meeting Summary")
    st.markdown(gemini_response.text)

    # Send output to n8n
    webhook_url = "https://arnavspace.app.n8n.cloud/webhook-test/7d57bfbc-0b0b-4f35-9f23-637ad7f7e794"

    payload = {
        "transcript": transcript,
        "gemini_output": gemini_response.text
    }

    st.download_button(
        "📋 Download Meeting Notes",
        gemini_response.text,
        file_name="meeting_notes.txt",
        mime="text/plain"
    )

    response = requests.post(webhook_url, json=payload)

    st.success(f"🚀 Sent to n8n! Status Code: {response.status_code}")