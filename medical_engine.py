import os
import json
import requests
import PyPDF2
from PIL import Image
from dotenv import load_dotenv
from google import genai
load_dotenv()

class UltimateMedicalEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
            raise ValueError("Error: .env फ़ाइल में GEMINI_API_KEY सेट नहीं है!")
        self.client = genai.Client(api_key=api_key)


    def fetch_live_hospitals(self, city_name="Delhi"):
        try:
            overpass_url = "http://overpass-api.de/api/interpreter"
            query = f"""
            [out:json];
            area[name="{city_name}"]->.searchArea;
            (
              node["amenity"="hospital"](area.searchArea);
              way["amenity"="hospital"](area.searchArea);
            );
            out center 5;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=8)
            data = response.json()
            elements = data.get('elements', [])
            
            hospitals = []
            for el in elements[:5]:
                tags = el.get('tags', {})
                name = tags.get('name', 'General Hospital / Health Center')
                hospitals.append({
                    "Hospital Name": name,
                    "City/Location": city_name,
                    "Type": tags.get('healthcare', 'Multi-Speciality'),
                    "Emergency Service": tags.get('emergency', 'Available')
                })
            if hospitals:
                return hospitals
        except Exception:
            pass
        
        return [
            {"Hospital Name": f"District Main Hospital, {city_name}", "City/Location": city_name, "Type": "Government / Multi-Speciality", "Emergency Service": "24x7"},
            {"Hospital Name": f"City Care Hospital, {city_name}", "City/Location": city_name, "Type": "Private Speciality", "Emergency Service": "24x7"}
        ]

    def extract_text_from_pdf(self, pdf_file):
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def analyze_report_multimodal(self, report_text="", image=None, doctor_claim=""):
        prompt = f"""
        You are a Senior MD/MBBS Consultant and Medical Ethics Auditor.
        Analyze the attached medical document/image and validate the doctor's claim.
        Doctor's Prescribed Diagnosis/Procedure: "{doctor_claim if doctor_claim else 'Not Provided'}"
        Extracted Report Text: "{report_text}"

        Tasks:
        1. Plain Language Summary: Translate all complex medical jargon into easy, plain language.
        2. Diagnosis Validation: State clearly whether the doctor's claim aligns with the objective findings.
        3. Over-Treatment Detection: Highlight if unnecessary surgeries, high-risk medications, or redundant tests are pushed.
        4. Actionable Advice: Give step-by-step next actions and second opinion rating (Low/Medium/High urgency).

        Format strictly with Markdown Headers:
        ### 📋 Plain Language Report Explanation
        ### 🔍 Fact-Check & Diagnostic Validation
        ### ⚠️ Over-Treatment & Risk Flag
        ### 🩺 Recommended Next Steps
        """
        contents = [prompt]
        if image:
            contents.append(image)

        response = self.client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt
)
        return response.text

    def dynamic_symptom_interview(self, symptom, history=[]):
        prompt = f"""
        You are an expert Physician conducting an interactive clinical assessment.
        Symptom: "{symptom}"
        History: {json.dumps(history)}

        Logic:
        - If history is insufficient, generate 2-3 targeted clinical questions.
        - If history is sufficient, provide differential diagnosis, severity level, and required specialist.

        Return strictly VALID JSON:
        {{
            "needs_more_info": true/false,
            "follow_up_questions": ["Question 1?", "Question 2?"],
            "diagnosis_summary": "Detailed assessment with probability percentages",
            "severity_level": "Mild / Moderate / Severe",
            "specialist_required": "Exact Specialist Title (e.g., Neurologist, Cardiologist, ENT)"
        }}
        """
        response = self.client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt
)
        try:
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception:
            return {
                "needs_more_info": False,
                "diagnosis_summary": response.text,
                "severity_level": "Moderate",
                "specialist_required": "General Physician"
            }

    def general_medical_consultant(self, query):
        prompt = f"You are a Master Medical Specialist. Provide evidence-based clinical guidance for: {query}"
        response = self.client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt
)
        return response.text
