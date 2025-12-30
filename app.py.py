import streamlit as st
import os
import time
import tempfile
import cv2
from PIL import Image
import yt_dlp
import google.generativeai as genai

# -------------------------------------------------
# ⚙️ הגדרות עמוד
# -------------------------------------------------
st.set_page_config(
    page_title="🏀 ניתוח שיפוט כדורסל – Hybrid AI",
    layout="wide"
)

st.title("🏀 ניתוח שיפוט כדורסל מקצועי (Hybrid AI)")
st.markdown(
    """
    🔹 ניתוח דו־שלבי: וידאו → פריימים → Gemini  
    🔹 יציב, נתמך API, ומותאם להדרכת שופטים (FIBA)
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
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# בדיקה סופית - אם עדיין אין מפתח, נעצור ונציג הודעה ידידותית
if not GEMINI_API_KEY:
    st.error("❌ לא נמצא API Key עבור Gemini.")
    st.info("אנא וודא שהגדרת את GEMINI_API_KEY בקובץ `.streamlit/secrets.toml` או כמשתנה סביבה.")
    st.stop()

# הגדרת ה-Library עם המפתח שנמצא
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------------------------------
# 📝 Prompt שיפוטי
# -------------------------------------------------
PROMPT = """
אתה מדריך שופטי כדורסל לפי חוקת FIBA.

לפניך סדרת תמונות (Frames) מאירוע משחק, עם ציון timestamp לכל תמונה.

נתח את האירוע:
1. מיקום ומכניקת השופטים (Lead / Center / Trail)
2. אחריות Primary / Secondary
3. הערכת ההחלטה (CC / CNC / IC / INC)
4. דגשים מקצועיים לשיפור

התייחס במפורש ל-timestamps.
השב בעברית מקצועית ותמציתית.
"""

# -------------------------------------------------
# 🎞️ חילוץ פריימים מהווידאו
# -------------------------------------------------
def extract_frames(video_path, interval_sec=1.5, max_frames=8):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    frames = []
    count = 0
    frame_index = 0

    while cap.isOpened() and len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_index / fps

        if timestamp >= count * interval_sec:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            frames.append((img, timestamp))
            count += 1

        frame_index += 1

    cap.release()
    return frames

# -------------------------------------------------
# 🧠 ניתוח Gemini (Images + Text)
# -------------------------------------------------
def analyze_frames_with_gemini(frames):
    model = genai.GenerativeModel("models/gemini-1.5-pro")

    content = [PROMPT]

    for img, ts in frames:
        content.append(f"Timestamp: {ts:05.2f} seconds")
        content.append(img)

    response = model.generate_content(content)
    return response.text

# -------------------------------------------------
# 🎬 בחירת מקור וידאו
# -------------------------------------------------
st.subheader("🎬 מקור וידאו")

source = st.radio(
    "בחר מקור:",
    ["העלאה מקומית", "קישור YouTube"],
    horizontal=True
)

video_path = None
temp_files = []

# -------------------------------------------------
# 📁 העלאה מקומית
# -------------------------------------------------
if source == "העלאה מקומית":
    uploaded = st.file_uploader("העלה וידאו (MP4 / MOV)", type=["mp4", "mov"])
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.read())
            video_path = tmp.name
            temp_files.append(video_path)
        st.video(video_path)

# -------------------------------------------------
# 🎥 YouTube (אופציונלי)
# -------------------------------------------------
if source == "קישור YouTube":
    url = st.text_input("קישור YouTube")
    if url and st.button("הורד"):
        with st.spinner("מוריד מיוטיוב..."):
            tmpdir = tempfile.gettempdir()
            out = os.path.join(tmpdir, f"yt_{int(time.time())}")
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": out + ".%(ext)s",
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)

        if os.path.exists(video_path) and os.path.getsize(video_path) > 1024:
            temp_files.append(video_path)
            st.video(video_path)
        else:
            st.error("❌ YouTube חסם את ההורדה – השתמש בהעלאה מקומית")
            video_path = None

# -------------------------------------------------
# 🏀 הפעלת ניתוח
# -------------------------------------------------
if video_path and st.button("🏀 נתח אירוע"):
    with st.spinner("🎞️ מחלץ פריימים..."):
        frames = extract_frames(video_path)

    if not frames:
        st.error("❌ לא ניתן לחלץ פריימים מהווידאו")
    else:
        st.subheader("🖼️ פריימים שנשלחו לניתוח")
        for img, ts in frames:
            st.image(img, caption=f"{ts:05.2f} sec", width=200)

        with st.spinner("🧠 מנתח שיפוטית עם Gemini..."):
            result = analyze_frames_with_gemini(frames)

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
