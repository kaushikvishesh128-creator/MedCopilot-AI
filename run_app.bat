@echo off 
echo Starting MedCopilot AI... 
call "C:\Users\vishesh\anaconda3\Scripts\activate.bat" 
pip install -r requirements.txt 
streamlit run app.py 
pause
