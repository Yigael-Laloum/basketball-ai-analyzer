import streamlit as st
import os
import time
import tempfile
import yt_dlp
import google.generativeai as genai

# הגדרות דף
st.set_page_config(page_title="ניתוח שיפוט כדורסל - Gemini", page_icon="🏀", layout="wide")

# API Key - הגדרה דרך Secrets או משתנה סביבה
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("חסר API Key של Google Gemini. הוסף אותו ב-Secrets של Streamlit.")
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


def analyze_basketball_clip(video_path: str, model_name: str):
    try:
        with st.spinner(f"מעלה את הסרטון ל-Gemini ({model_name})..."):
            uploaded_file = genai.upload_file(path=video_path, mime_type="video/mp4")

            # המתנה לעיבוד הקובץ בשרתי גוגל
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                raise ValueError("עיבוד הווידאו ב-Gemini נכשל.")

        with st.spinner("מנתח את המהלך..."):
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([uploaded_file, PROMPT])
            return response.text

    except Exception as e:
        st.error(f"שגיאה בניתוח: {str(e)}")
        return None
    finally:
        # ניקוי הקובץ מהשרת של גוגל בסיום
        if 'uploaded_file' in locals():
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass


# ממשק משתמש
st.title("🏀 ניתוח שיפוט כדורסל עם Gemini")
st.markdown("העלה וידאו או הזן קישור YouTube לקבלת ניתוח מקצועי לפי חוקת FIBA.")

source = st.radio("מקור הווידאו", ["YouTube URL", "העלאה מקומית"])

video_path = None

if source == "YouTube URL":
    url = st.text_input("הזן קישור YouTube (למשל: https://www.youtube.com/watch?v=...)")
    if url and st.button("הורד ונתח"):
        try:
            with st.spinner("מוריד מיוטיוב (מחפש פורמט מתאים ללא FFmpeg)..."):
                # יצירת נתיב זמני
                temp_dir = tempfile.gettempdir()
                video_path = os.path.join(temp_dir, 'yt_clip.mp4')

                ydl_opts = {
                    # 'best[ext=mp4]' מבטיח הורדת קובץ אחד שכולל וידאו ואודיו יחד ללא צורך ב-FFmpeg
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': video_path,
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            if os.path.exists(video_path):
                st.video(video_path)
                st.success("הווידאו הורד בהצלחה!")
        except Exception as e:
            st.error(f"שגיאה בהורדה: {str(e)}")
            video_path = None

elif source == "העלאה מקומית":
    uploaded = st.file_uploader("העלה וידאו (mp4)", type=["mp4", "mov", "avi"])
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.getvalue())
            video_path = tmp.name
        st.video(video_path)
        st.success("הקובץ הועלה בהצלחה!")

# בחירת מודל
model_choice = st.selectbox("בחר מודל Gemini", ["gemini-1.5-flash", "gemini-1.5-pro"])

# כפתור הפעלה
if video_path and st.button("התחל ניתוח מקצועי! 🔍"):
    analysis = analyze_basketball_clip(video_path, model_choice)
    if analysis:
        st.divider()
        st.subheader("📋 דוח ניתוח שיפוט")
        st.markdown(analysis)

    # ניקוי קובץ זמני מהשרת המקומי
    if video_path and os.path.exists(video_path):
        try:
            os.unlink(video_path)
        except:
            pass

st.markdown("---")
st.caption("מבוסס על Gemini API | מותאם לניתוח מכניקת שיפוט FIBA 2025")