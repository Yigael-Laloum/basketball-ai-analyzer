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

        with st.spinner("מנתח עם Gemini..."):
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


# --- ממשק משתמש ---
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
                # שם קובץ ייחודי כדי למנוע התנגשויות
                unique_id = int(time.time())
                save_path = os.path.join(temp_dir, f"yt_video_{unique_id}")

                ydl_opts = {
                    # נסיון להוריד את הקובץ המאוחד הכי טוב (וידאו + אודיו) בפורמט MP4
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': save_path + '.%(ext)s',
                    'quiet': True,
                    'no_warnings': True,
                    # התחזות לדפדפן כדי למנוע חסימה
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'nocheckcertificate': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_path = ydl.prepare_filename(info)

            if video_path and os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                st.video(video_path)
                st.success(f"הורדה הושלמה! גודל קובץ: {os.path.getsize(video_path) // 1024} KB")
            else:
                st.error("הקובץ ירד ריק או שלא נמצא. יוטיוב עשוי לחסום את השרת.")
                video_path = None
        except Exception as e:
            st.error(f"שגיאה בתהליך ההורדה: {str(e)}")
            video_path = None

elif source == "העלאה מקומית":
    uploaded = st.file_uploader("העלה קובץ וידאו (MP4/MOV)", type=["mp4", "mov"])
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.getvalue())
            video_path = tmp.name
        st.video(video_path)

# בחירת מודל
model_choice = st.selectbox("בחר מודל Gemini", ["gemini-1.5-flash", "gemini-1.5-pro"])

if video_path and st.button("התחל ניתוח 🏀"):
    if os.path.getsize(video_path) > 0:
        result = analyze_basketball_clip(video_path, model_choice)
        if result:
            st.divider()
            st.subheader("📋 דוח ניתוח מקצועי")
            st.markdown(result)
    else:
        st.error("הווידאו ריק, לא ניתן לנתח.")

# ניקוי קבצים ישנים בתיקייה הזמנית (אופציונלי)
if video_path and os.path.exists(video_path):
    # כאן ניתן להוסיף לוגיקה למחיקה אם רוצים לחסוך מקום בשרת
    pass