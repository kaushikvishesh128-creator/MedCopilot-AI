import os
import streamlit as st
import pandas as pd
from PIL import Image
from medical_engine import UltimateMedicalEngine
import io
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text
st.set_page_config(
    page_title="MedCopilot AI - Universal Health Platform",
    page_icon="🩺",
    layout="wide"
)

pwa_html = """
    <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('data:text/javascript;base64,c2VsZi5hZGRFdmVudExpc3RlbmVyKCdmZXRjaCcsIGZ1bmN0aW9uKGV2ZW50KSB7fSk7');
      });
    }
    </script>
    <link rel="manifest" href="data:application/json;base64,ewogICJuYW1lIjogIk1lZENvcGlsb3QgQUkiLAogICJzaG9ydF9uYW1lIjogIk1lZENvcGlsb3QiLAogICJzdGFydF91cmwiOiAiLyIsCiAgImRpc3BsYXkiOiAic3RhbmRhbG9uZSIsCiAgImJhY2tncm91bmRfY29sb3IiOiAiIzBGMTcyQSIsCiAgInRoZW1lX2NvbG9yIjogIiMzQjgyRjYiCn0=">
"""
st.markdown(pwa_html, unsafe_allow_html=True)

st.sidebar.title("📲 Install App")
st.sidebar.info(
    "**To Install as Mobile/Desktop App:**\n"
    "1. Open in Chrome / Safari.\n"
    "2. Tap Menu (⋮ or Share).\n"
    "3. Select **'Add to Home Screen'** / **'Install App'**."
)

@st.cache_resource
def get_engine():
    return UltimateMedicalEngine()

try:
    engine = get_engine()
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.info("Please verify that GEMINI_API_KEY is correctly set in your .env file.")
    st.stop()

st.title("🩺 MedCopilot AI: Universal Health & Second-Opinion Platform")
st.caption("Powered by Multi-Modal LLM Architecture & Dynamic Triage Agents")

tab1, tab2, tab3 = st.tabs([
    "💬 Interactive Clinical Interview",
    "📄 Report OCR & Fact-Checker",
    "🌐 Universal Medical Knowledge Engine"
])

with tab1:
    st.header("Interactive Symptom Assessment & Triage")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symptom_input = st.text_input("Enter symptom (e.g., Severe fever with joint pain for 2 days):")
    with col2:
        user_city = st.text_input("Enter Your City/Location:", value="Delhi")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.button("Start Clinical Assessment"):
        if symptom_input:
            st.session_state.chat_history.append({"user": symptom_input})
            res = engine.dynamic_symptom_interview(symptom_input, st.session_state.chat_history)

            if res.get("needs_more_info"):
                st.warning("⚠️ Clinical Follow-up Questions Required:")
                for q in res.get("follow_up_questions", []):
                    st.write(f"• {q}")
            else:
                st.success("✅ Triage Completed")
                st.write(f"**Diagnosis Assessment:** {res.get('diagnosis_summary')}")
                st.info(f"**Required Specialist:** {res.get('specialist_required')}")
                st.write(f"**Severity Level:** {res.get('severity_level')}")

                st.subheader(f"🏥 Real Recommended Specialists & Nearby Hospitals in {user_city}")
                live_hospitals = engine.fetch_live_hospitals(city_name=user_city)
                st.table(pd.DataFrame(live_hospitals))

with tab2:
    st.header("Medical Report OCR & Second-Opinion Fact-Checker")
    uploaded_file = st.file_uploader("Upload Medical Report (Image PNG/JPG or PDF):", type=["png", "jpg", "jpeg", "pdf"])
    doctor_claim = st.text_input("What did your doctor tell you/recommend? (Optional):")

    report_text = ""
    image_obj = None

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            report_text = engine.extract_text_from_pdf(uploaded_file)
            st.info("📄 PDF Text Extracted Successfully.")
        else:
            image_obj = Image.open(uploaded_file)
            st.image(image_obj, caption="Uploaded Scan/Report", width=300)

    if st.button("Analyze & Fact-Check Report"):
        if uploaded_file or doctor_claim:
            with st.spinner("Processing report via Multimodal Vision Engine..."):
                analysis = engine.analyze_report_multimodal(report_text=report_text, image=image_obj, doctor_claim=doctor_claim)
                st.markdown(analysis)
        else:
            st.error("Please upload a report file or enter details.")

with tab3:
    st.header("Universal Medical & Veterinary Knowledge Base")
    
    # 🎤 Mic recorder button
    spoken_text = speech_to_text(
        language='en', 
        start_prompt="🎤 Click to Speak", 
        stop_prompt="⏹️ Stop Recording", 
        key='tab3_speech'
    )
    
    # Text Input
    query = st.text_area(
        "Ask any medical question (Human or Animal Diseases):", 
        value=spoken_text if spoken_text else "",
        height=100
    )
    
    if st.button("Consult Knowledge Engine"):
        if query.strip():
            with st.spinner("Searching Evidence-Based Medical Knowledge..."):
                ans = engine.general_medical_consultant(query)
                st.markdown(ans)
                
                # 🔊 Text-To-Speech (Audio output)
                tts = gTTS(text=ans, lang="en")
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3")
        else:
            st.warning("Please enter or speak a question first.")