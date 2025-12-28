import streamlit as st
import os
import time
import tempfile
import yt_dlp
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
        st.error(f"שגיאה בניתוח: {str(e)}")
        return None
    finally:
        if 'uploaded_file' in locals():
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass

# ממשק
st.title("🏀 ניתוח שיפוט כדורסל עם Gemini")
st.markdown("העלה וידאו קצר או הזן קישור YouTube, ובחר מודל.")

source = st.radio("מקור הווידאו", ["YouTube URL", "העלאה מקומית"])

video_path = None

if source == "YouTube URL":
    url = st.text_input("הזן קישור YouTube")
    if url and st.button("הורד + נתח"):
        try:
            with st.spinner("מוריד מיוטיוב..."):
                video_path = os.path.join(tempfile.gettempdir(), 'clip.mp4')

                ydl_opts = {
                    'format': 'mp4',  # פורמט mp4 מוכן (ללא צורך ב-ffmpeg)
                    'outtmpl': video_path,
                    'quiet': True,
                    'no_warnings': True,
                    'continuedl': True,
                    'retries': 10,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            st.success("הווידאו הורד!")
        except Exception as e:
            st.error(f"שגיאה בהורדה: {str(e)}")
            video_path = None

elif source == "העלאה מקומית":
    uploaded = st.file_uploader("העלה וידאו (mp4)", type=["mp4"])
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.getvalue())
            video_path = tmp.name
        st.video(uploaded)
        st.success("ווידאו הועלה!")

model = st.selectbox("בחר מודל Gemini", ["gemini-2.5-flash", "gemini-2.5-pro"])

if video_path and st.button("נתח את המשחק! 🏀"):
    result = analyze_basketball_clip(video_path, model)
    if result:
        st.subheader("דוח ניתוח מקצועי")
        st.markdown(result)

    # ניקוי קובץ
    if video_path and os.path.exists(video_path):
        try:
            os.unlink(video_path)
        except:
            pass

st.markdown("---")
st.caption("פותח על ידי Grok & Streamlit | Gemini API | 2025")
