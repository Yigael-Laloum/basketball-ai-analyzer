import streamlit as st
import os
import time
import tempfile
import google.generativeai as genai
import yt_dlp

# --- הגדרות אבטחה ו-API Key ---
GEMINI_API_KEY = None

# ניסיון בטוח למשוך את המפתח (מונע קריסה אם Secrets לא קיים)
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ חסר API Key של Gemini. אנא הגדר אותו ב-Secrets.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)


# --- פונקציות עזר ---

def analyze_basketball_clip(video_path: str):
    """פונקציה לשליחת הווידאו ל-Gemini לניתוח"""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')  # או flash

        with st.spinner("מעלה וידאו ל-AI ומנתח..."):
            # העלאת הקובץ ל-Gemini
            video_file = genai.upload_file(path=video_path)

            # המתנה לעיבוד הקובץ בשרתי גוגל
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

            prompt = "נתח את אירוע השיפוט בסרטון הכדורסל הזה לפי חוקת FIBA. התייחס למגע, מיקום השופט וההחלטה."
            response = model.generate_content([prompt, video_file])

            return response.text
    except Exception as e:
        return f"שגיאה בניתוח: {str(e)}"


# --- ממשק משתמש (UI) ---
st.set_page_config(page_title="Basketball Referee AI", page_icon="🏀")
st.title("🏀 ניתוח שיפוט כדורסל מקצועי")
st.markdown("מערכת ניתוח מבוססת AI לפי חוקת FIBA")

source = st.radio("מקור הווידאו", ["YouTube URL", "העלאה מקומית"])
video_path = None

if source == "YouTube URL":
    url = st.text_input("הזן קישור YouTube")
    if url and st.button("הורד ונתח"):
        try:
            with st.spinner("מוריד מיוטיוב (זה עשוי לקחת רגע)..."):
                temp_dir = tempfile.gettempdir()
                unique_id = int(time.time())
                video_path = os.path.join(temp_dir, f"yt_video_{unique_id}.mp4")

                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': video_path,
                    'quiet': True,
                    'no_warnings': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                st.video(video_path)  # הצגת הווידאו שהורד
        except Exception as e:
            st.error(f"שגיאה בהורדה: {str(e)}")

elif source == "העלאה מקומית":
    uploaded_file = st.file_upload("בחר קובץ וידאו", type=['mp4', 'mov', 'avi'])
    if uploaded_file:
        temp_dir = tempfile.gettempdir()
        video_path = os.path.join(temp_dir, uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.video(video_path)

# --- הרצת הניתוח ---
if video_path and os.path.exists(video_path):
    if st.button("התחל ניתוח AI"):
        result = analyze_basketball_clip(video_path)
        st.subheader("תוצאות הניתוח:")
        st.write(result)