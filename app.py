import streamlit as st
import os
import time
import tempfile
from pytubefix import YouTube
import google.generativeai as genai

# הגדרות
st.set_page_config(page_title="ניתוח שיפוט כדורסל - Gemini", page_icon="🏀", layout="wide")

# API Key - השתמש ב-secrets ב-Streamlit Cloud
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("חסר API Key של Google Gemini. הוסף אותו ב-Secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# פרומפט מקצועי
PROMPT = """
נתח את סרטון הכדורסל המצורף בתור מדריך שופטי כדורסל FIBA.
התייחס בפירוט ל:
1. מיקומי שופטים ומכניקה (Lead/Center/Trail)
2. Primary/Secondary אחריות
3. הערכת החלטה (CC, CNC, IC, INC)
4. דגשים מקצועיים
ציין טיימסטאמפים מדויקים (MM:SS) לכל אירוע.
השב בעברית מקצועית.
"""

def analyze_basketball_clip(video_path: str, model_name: str = "gemini-2.5-flash"):
    try:
        with st.spinner("מעלה ל-Gemini..."):
            uploaded_file = genai.upload_file(path=video_path, mime_type="video/mp4")
            for _ in range(60):
                if uploaded_file.state.name == "ACTIVE":
                    break
                time.sleep(5)
                uploaded_file = genai.get_file(uploaded_file.name)
            else:
                raise TimeoutError("העלאה לקחה יותר מדי זמן")

        with st.spinner("מנתח..."):
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([uploaded_file, PROMPT])
            return response.text

    except Exception as e:
        st.error(f"שגיאה: {str(e)}")
        return None
    finally:
        if 'uploaded_file' in locals():
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass

# ממשק
st.title("🏀 ניתוח שיפוט כדורסל")
source = st.radio("מקור", ["YouTube URL", "העלאה מקומית"])

video_path = None

if source == "YouTube URL":
    url = st.text_input("קישור YouTube")
    if url and st.button("הורד + נתח"):
        with st.spinner("מוריד..."):
            import yt_dlp

            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(tempfile.gettempdir(), 'clip.mp4'),
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            video_path = os.path.join(tempfile.gettempdir(), 'clip.mp4')
        st.success("הורד!")

elif source == "העלאה מקומית":
    uploaded = st.file_uploader("העלה mp4", type="mp4")
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.getvalue())
            video_path = tmp.name
        st.video(uploaded)

model = st.selectbox("מודל", ["gemini-2.5-flash", "gemini-2.5-pro"])

if video_path and st.button("נתח 🏀"):
    result = analyze_basketball_clip(video_path, model)
    if result:
        st.markdown(result)
    if os.path.exists(video_path):
        os.unlink(video_path)

st.caption("Gemini API | Streamlit Cloud | 2025")