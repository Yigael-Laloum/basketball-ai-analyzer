import streamlit as st
import os
import time
import tempfile
from pytubefix import YouTube
import google.generativeai as genai

# הגדרות
st.set_page_config(page_title="ניתוח שיפוט כדורסל - Gemini", page_icon="🏀", layout="wide")

# API Key - השתמש ב-secrets ב-Streamlit Cloud
GEMINI_API_KEY = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    st.error("חסר API Key של Google Gemini. הוסף אותו ב-Secrets או כמשתנה סביבה.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# פרומפט מקצועי
PROMPT = """
נתח את סרטון הכדורסל המצורף בתור מדריך שופטי כדורסל FIBA.
התייחס בפירוט ל:
1. מיקומי שופטים ומכניקה (Lead/Center/Trail)
2. Primary/Secondary אחריות
3. הערכת החלטה (CC, CNC, IC, INC)
4. דגשים מקצועיים (מגע רך, Off-the-ball, ניהול ספסל)
ציין טיימסטאמפים מדויקים (MM:SS) לכל אירוע.
השב בעברית מקצועית בלבד.
"""

# פונקציה לניתוח (מתוקנת ל-Streamlit)
def analyze_basketball_clip(video_path: str, model_name: str = "gemini-2.5-flash"):
    try:
        with st.spinner("מעלה את הווידאו ל-Gemini..."):
            uploaded_file = genai.upload_file(path=video_path, mime_type="video/mp4")

            # המתנה לעיבוד
            for _ in range(60):  # timeout ~5 דקות
                if uploaded_file.state.name == "ACTIVE":
                    break
                if uploaded_file.state.name in ["FAILED", "ERROR"]:
                    raise RuntimeError("העלאת הווידאו נכשלה")
                time.sleep(5)
                uploaded_file = genai.get_file(uploaded_file.name)
            else:
                raise TimeoutError("העלאת הווידאו לקחה יותר מדי זמן")

        with st.spinner("מנתח את המשחק..."):
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

# ממשק Streamlit
st.title("🏀 ניתוח שיפוט כדורסל עם Gemini")
st.markdown("""
העלה וידאו קצר של משחק כדורסל או הזן קישור מיוטיוב, ובחר מודל.  
Gemini ינתח את השופטים, המכניקה וההחלטות – כמו דוח FIBA מקצועי!
""")

# בחירת מקור וידאו
source = st.radio("מקור הווידאו", ["העלאה מהמחשב", "קישור YouTube"])

video_path = None

if source == "העלאה מהמחשב":
    uploaded_file = st.file_uploader("העלה וידאו (mp4)", type=["mp4"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            video_path = tmp_file.name
        st.success("ווידאו הועלה!")
        st.video(uploaded_file)

elif source == "קישור YouTube":
    url = st.text_input("הזן קישור YouTube")
    if url and st.button("הורד ונתח"):
        try:
            with st.spinner("מוריד מיוטיוב..."):
                yt = YouTube(url)
                stream = yt.streams.get_highest_resolution()
                video_path = stream.download(output_path=tempfile.gettempdir(), filename="game_clip.mp4")
            st.success("הווידאו הורד!")
        except Exception as e:
            st.error(f"שגיאה בהורדה: {str(e)}")

# בחירת מודל
model_options = ["gemini-2.5-flash", "gemini-2.5-pro"]
selected_model = st.selectbox("בחר מודל Gemini", model_options, index=0)

if video_path and st.button("נתח את המשחק! 🏀"):
    result = analyze_basketball_clip(video_path, selected_model)
    if result:
        st.subheader("דוח ניתוח מקצועי")
        st.markdown(result)

    # ניקוי קובץ מקומי
    if video_path and os.path.exists(video_path):
        os.unlink(video_path)

st.markdown("---")
st.caption("פותח על ידי Grok & Streamlit | Gemini API | 2025")