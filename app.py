import streamlit as st
import os
import time
import tempfile
import google.generativeai as genai
import yt_dlp

# --- הגדרות דף ועיצוב RTL ---
st.set_page_config(page_title="Basketball Referee AI", page_icon="🏀")

# הזרקת CSS ליישור האתר לימין (RTL)
st.markdown(
    """
    <style>
    .stApp {
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, p, span, label, .stMarkdown {
        text-align: right !important;
        direction: rtl !important;
    }
    div[role="radiogroup"] {
        direction: rtl;
        display: flex;
        gap: 20px;
    }
    input {
        direction: rtl !important;
        text-align: right !important;
    }
    div.stButton > button {
        display: block;
        margin-right: 0;
        margin-left: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- הגדרות אבטחה ו-API Key ---
GEMINI_API_KEY = None
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
    """פונקציה לשליחת הווידאו ל-Gemini לניתוח עם תיקון לשגיאת 404"""
    try:
        # שימוש במודל Flash שהוא יציב ומהיר יותר לניתוח וידאו
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')

        with st.spinner("מעלה וידאו ל-AI ומנתח..."):
            video_file = genai.upload_file(path=video_path)

            # המתנה לעיבוד הקובץ
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                return "שגיאה: עיבוד הווידאו נכשל בשרתי גוגל."

            prompt = "נתח את אירוע השיפוט בסרטון הכדורסל הזה לפי חוקת FIBA. התייחס למגע, מיקום השופט וההחלטה. ענה בעברית בצורה מקצועית."

            # שליחת הבקשה (הקובץ ואז הפרומפט)
            response = model.generate_content([video_file, prompt])

            return response.text
    except Exception as e:
        return f"שגיאה בתהליך הניתוח: {str(e)}"


# --- ממשק משתמש (UI) ---
st.title("🏀 ניתוח שיפוט כדורסל מקצועי")
st.markdown("מערכת ניתוח מבוססת AI לפי חוקת FIBA")

source = st.radio("בחר מקור וידאו", ["YouTube URL", "העלאה מקומית"])
video_path = None

if source == "YouTube URL":
    url = st.text_input("הזן קישור YouTube")
    if url and st.button("הורד וידאו"):
        try:
            with st.spinner("מוריד מיוטיוב..."):
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

                st.session_state['video_path'] = video_path
                st.video(video_path)
        except Exception as e:
            st.error(f"שגיאה בהורדה: {str(e)}")

elif source == "העלאה מקומית":
    uploaded_file = st.file_uploader("בחר קובץ וידאו מהמחשב", type=['mp4', 'mov', 'avi'])
    if uploaded_file:
        temp_dir = tempfile.gettempdir()
        video_path = os.path.join(temp_dir, uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state['video_path'] = video_path
        st.video(video_path)

# --- הרצת הניתוח ---
# שימוש ב-session_state כדי לשמור את הנתיב גם אחרי רענון כפתור
current_video = st.session_state.get('video_path')

if current_video and os.path.exists(current_video):
    if st.button("התחל ניתוח AI 🚀"):
        result = analyze_basketball_clip(current_video)
        st.subheader("תוצאות הניתוח:")
        st.info(result)