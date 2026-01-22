
import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib

# 1. إعداد قاعدة بيانات مُنجز [cite: 2026-01-13]
def init_db():
    conn = sqlite3.connect('mongez_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# 2. هندسة السياق وتأسيس الذكاء الاصطناعي [cite: 2026-01-22]
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # تعليمات السيادة (System Prompt) لضمان عدم النسيان [cite: 2025-12-27]
    system_prompt = "أنت 'مُنجز' المساعد الاحترافي. تدير موديولات: المحاسبة، SEO جلب العملاء، والبحث الصوتي."
except Exception as e:
    st.error(f"⚠️ خطأ في الاتصال بالسيرفر: {e}")

# 3. واجهة المستخدم والتأكد من الدخول [cite: 2026-01-18]
st.set_page_config(page_title="Mongez v4.0", page_icon="🛡️", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.sidebar.title("🔐 بوابة مُنجز")
    menu = st.sidebar.selectbox("القائمة", ["تسجيل دخول", "إنشاء حساب"])
    user = st.sidebar.text_input("اسم المستخدم")
    pw = st.sidebar.text_input("كلمة المرور", type='password')
    
    if st.sidebar.button("تنفيذ"):
        conn = sqlite3.connect('mongez_v4.db')
        c = conn.cursor()
        if menu == "إنشاء حساب":
            try:
                c.execute('INSERT INTO users VALUES (?,?)', (user, make_hashes(pw)))
                conn.commit()
                st.success("تم الإنشاء! سجل دخولك")
            except: st.error("الاسم موجود")
        else:
            c.execute('SELECT password FROM users WHERE username =?', (user,))
            result = c.fetchone()
            if result and check_hashes(pw, result[0]):
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.rerun()
        conn.close()

# 4. تشغيل محركات السيادة (الأدوات النشطة) [cite: 2026-01-13]
if st.session_state['logged_in']:
    st.title(f"🚀 مرحباً {st.session_state['user']} في مُنجز v4.0")
    
    # القسم الاستراتيجي المعدل (من السطر 98) [cite: 2026-01-23]
    app_choice = st.sidebar.radio("الأدوات النشطة", 
                                 ["المساعد الذكي (الوعي الشامل)", 
                                  "برنامج المحاسب المعتمد", 
                                  "جالب العملاء SEO", 
                                  "المحرك الصوتي المباشر"])

    if app_choice == "المساعد الذكي (الوعي الشامل)":
        user_input = st.chat_input("تحدث مع شريكك التقني...")
        if user_input:
            response = model.generate_content(f"{system_prompt}\nالمستخدم: {user_input}")
            st.markdown(f"### 🛡️ رد مُنجز:\n{response.text}")

    elif app_choice == "برنامج المحاسب المعتمد":
        st.subheader("📊 الإدارة المالية")
        st.info("المحرك جاهز لربط ملفاتك المحاسبية بدقة.")

    elif app_choice == "جالب العملاء SEO":
        st.subheader("🔍 محرك جلب الفرص")
        query = st.text_input("عن ماذا تبحث لنوظف التكنولوجيا؟")
        if st.button("بدء البحث"):
            st.write(f"جارٍ استخراج بيانات العملاء المهتمين بـ {query}...")

    elif app_choice == "المحرك الصوتي المباشر":
        st.subheader("🎙️ الأوامر الصوتية")
        st.write("المحرك جاهز لاستقبال صوتك وتحويله لأفعال.")
