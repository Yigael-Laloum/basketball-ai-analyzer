import streamlit as st
import os
import time
import tempfile
import yt_dlp
import google.generativeai as genai

# -------------------------------------------------
# ⚙️ הגדרות עמוד
# -------------------------------------------------
st.set_page_config(
    page_title="🏀 ניתוח שיפוט כדורסל – Gemini",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 ניתוח שיפוט כדורסל מקצועי (FIBA)")
st.markdown(
    """
    **הערה חשובה:**  
    העלאה מקומית היא האפשרות היציבה ביותר.  
    הורדה מ-YouTube עלולה להיחסם בשרתי ענן.
    """
)

# -------------------------------------------------
# 🔐 Gemini API
# -------------------------------------------------
GEMI# ניסיון למשוך את המפתח בצורה בטוחה
GEMINI_API_KEY = None

# 1. בדיקה אם קיים בתוך st.secrets (עבור Streamlit Cloud או secrets.toml מקומי)
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    # אם הקובץ secrets.toml בכלל לא קיים, Streamlit עלול לזרוק שגיאה - נתעלם ונמשיך ל-env
    pass

# 2. אם לא נמצא ב-secrets, ננסה למשוך ממשתני סביבה (os.getenv)
if not GEMINI_API_KEY:
<<<<<<< HEAD:app.py.py
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# בדיקה סופית - אם עדיין אין מפתח, נעצור ונציג הודעה ידידותית
if not GEMINI_API_KEY:
    st.error("❌ לא נמצא API Key עבור Gemini.")
    st.info("אנא וודא שהגדרת את GEMINI_API_KEY בקובץ `.streamlit/secrets.toml` או כמשתנה סביבה.")
=======
    st.error("❌ חסר API Key של Google Gemini")
>>>>>>> parent of 572bb50 (11):app.py
    st.stop()

# הגדרת ה-Library עם המפתח שנמצא
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------------------------------
# 📝 Prompt מקצועי
# -------------------------------------------------
PROMPT = """
נתח את סרטון הכדורסל המצורף בתור מדריך שופטי כדורסל FIBA.
התייחס בפירוט ל:
1. מיקומי שופטים ומכניקה (Lead / Center / Trail)
2. Primary / Secondary Responsibility
3. הערכת החלטות (CC / CNC / IC / INC)
4. דגשים מקצועיים

ציין טיימסטאמפים מדויקים (MM:SS).
השב בעברית מקצועית.
"""

# -------------------------------------------------
# 🧠 פונקציית ניתוח Gemini (וידאו)
# -------------------------------------------------
def analyze_video(video_path: str) -> str | None:
    uploaded_file = None
    try:
        with st.spinner("⬆️ מעלה וידאו ל-Gemini..."):
            uploaded_file = genai.upload_file(
                path=video_path,
                mime_type="video/mp4"
            )

            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                raise RuntimeError("עיבוד הווידאו נכשל ב-Gemini")

        with st.spinner("🧠 מנתח וידאו..."):
            model = genai.GenerativeModel("models/gemini-1.5-pro")
            response = model.generate_content([uploaded_file, PROMPT])
            return response.text

    except Exception as e:
        st.error(f"❌ שגיאה בניתוח: {e}")
        return None

    finally:
        if uploaded_file:
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass

# -------------------------------------------------
# 🎬 בחירת מקור וידאו
# -------------------------------------------------
st.subheader("🎬 מקור הווידאו")

source = st.radio(
    "בחר מקור:",
    ["קישור YouTube", "העלאה מקומית"],
    horizontal=True
)

video_path = None
temp_files = []

# -------------------------------------------------
# 🎥 אפשרות 1 – YouTube
# -------------------------------------------------
if source == "קישור YouTube":
    youtube_url = st.text_input("הזן קישור YouTube")

    if youtube_url and st.button("הורד וידאו"):
        try:
            with st.spinner("📥 מוריד מיוטיוב..."):
                temp_dir = tempfile.gettempdir()
                filename = f"yt_video_{int(time.time())}"
                output_path = os.path.join(temp_dir, filename)

                ydl_opts = {
                    "format": "bestvideo+bestaudio/best",
                    "merge_output_format": "mp4",
                    "outtmpl": output_path + ".%(ext)s",
                    "quiet": True,
                    "no_warnings": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    video_path = ydl.prepare_filename(info)

            # בדיקת תקינות הקובץ
            if not video_path or not os.path.exists(video_path) or os.path.getsize(video_path) < 1024:
                st.error(
                    "❌ ההורדה נכשלה.\n\n"
                    "ייתכן ש-YouTube חסם הורדה מהשרת.\n"
                    "**מומלץ להשתמש בהעלאה מקומית.**"
                )
                video_path = None
            else:
                temp_files.append(video_path)
                st.success("✅ הורדה הושלמה")
                st.video(video_path)

        except Exception as e:
            st.error(f"❌ שגיאה בהורדה: {e}")
            video_path = None

# -------------------------------------------------
# 📁 אפשרות 2 – העלאה מקומית
# -------------------------------------------------
elif source == "העלאה מקומית":
    uploaded = st.file_uploader(
        "העלה קובץ וידאו (MP4 / MOV)",
        type=["mp4", "mov"]
    )

    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.read())
            video_path = tmp.name
            temp_files.append(video_path)

        if os.path.getsize(video_path) < 1024:
            st.error("❌ הקובץ ריק או פגום")
            video_path = None
        else:
            st.success("✅ הקובץ הועלה בהצלחה")
            st.video(video_path)

# -------------------------------------------------
# 🏀 ניתוח
# -------------------------------------------------
if video_path and st.button("🏀 התחל ניתוח"):
    result = analyze_video(video_path)
    if result:
        st.divider()
        st.subheader("📋 דוח ניתוח שיפוטי")
        st.markdown(result)

# -------------------------------------------------
# 🧹 ניקוי קבצים זמניים
# -------------------------------------------------
for f in temp_files:
    try:
        if os.path.exists(f):
            os.remove(f)
    except:
        pass
