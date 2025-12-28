import streamlit as st
import os
import time
import tempfile
import yt_dlp
import google.generativeai as genai

# הגדרות דף
st.set_page_config(page_title="ניתוח שיפוט כדורסל - Gemini", page_icon="🏀", layout="wide")

# API Key
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("חסר API Key של Google Gemini. הוסף אותו ב-Secrets של Streamlit.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

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


def analyze_basketball_clip(video_path: str, model_name: str):
    try:
        with st.spinner(f"מעלה את הסרטון ל-Gemini..."):
            uploaded_file = genai.upload_file(path=video_path, mime_type="video/mp4")

            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                raise ValueError("עיבוד הווידאו נכשל בשרתי Gemini.")

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


st.title("🏀 ניתוח שיפוט כדורסל")

source = st.radio("מקור הווידאו", ["YouTube URL", "העלאה מקומית"])
video_path = None

if source == "YouTube URL":
    url = st.text_input("הזן קישור YouTube")
    if url and st.button("הורד ונתח"):
        try:
            with st.spinner("מוריד מיוטיוב..."):
                # יצירת שם קובץ זמני ייחודי
                temp_dir = tempfile.gettempdir()
                video_path = os.path.join(temp_dir, f"video_{int(time.time())}.mp4")

                ydl_opts = {
                    # מחפש mp4 מוכן, אם אין - לוקח את הכי טוב שיש ומקווה שהוא קובץ אחד
                    'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                    'outtmpl': video_path,
                    'quiet': True,
                    'no_warnings': True,
                    # הוספת Headers כדי להיראות כמו דפדפן אמיתי
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    # לפעמים הסיומת משתנה בהורדה, נעדכן את הנתיב
                    actual_filename = ydl.prepare_filename(info)
                    if os.path.exists(actual_filename):
                        video_path = actual_filename

            if video_path and os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                st.video(video_path)
                st.success("הורדה הושלמה!")
            else:
                st.error("הקובץ ירד ריק. נסה להעלות את הקובץ ידנית או לבחור סרטון אחר.")
                video_path = None
        except Exception as e:
            st.error(f"שגיאה בהורדה: {str(e)}")
            video_path = None

elif source == "העלאה מקומית":
    uploaded = st.file_uploader("העלה קובץ", type=["mp4", "mov"])
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.getvalue())
            video_path = tmp.name
        st.video(video_path)

model_choice = st.selectbox("בחר מודל", ["gemini-1.5-flash", "gemini-1.5-pro"])

if video_path and st.button("נתח כעת"):
    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        result = analyze_basketball_clip(video_path, model_choice)
        if result:
            st.markdown(result)
    else:
        st.error("לא נמצא קובץ וידאו תקין לניתוח.")

# ניקוי
if video_path and os.path.exists(video_path):
    try:
        # השארתי את הניקוי לסוף הריצה
        pass
    except:
        pass