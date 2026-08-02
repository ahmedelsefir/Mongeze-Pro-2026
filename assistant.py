import streamlit as st
import google.generativeai as genai

# 1. التأسيس الآلي للنظام
st.set_page_config(page_title="منظومة مُنجز الذكية", layout="wide", page_icon="🚀")

# 🔍 جلب المفتاح الذكي من أي مسار داخل Secrets
api_key = None

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
elif "google" in st.secrets and "api_key" in st.secrets["google"]:
    api_key = st.secrets["google"]["api_key"]
elif "github" in st.secrets and "GEMINI_API_KEY" in st.secrets["github"]:
    api_key = st.secrets["github"]["GEMINI_API_KEY"]

try:
    if api_key:
        genai.configure(api_key=api_key)
    else:
        st.error("⚠️ مفتاح الاتصال غير موجود في Secrets!")
except Exception as e:
    st.error(f"❌ فشل الاتصال الآلي: {e}")

# 2. إدارة جلسة الدخول
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 3. بوابة العبور (الدخول المباشر للمطور)
if not st.session_state['logged_in']:
    st.title("🔐 بوابة دخول مُنجز")
    col1, col2 = st.columns(2)
    with col1:
        user = st.text_input("اسم المستخدم")
    with col2:
        pw = st.text_input("كلمة المرور", type='password')
    
    if st.button("دخول للنظام"):
        if user == "ahmedelsefir" and pw == "123":
            st.session_state['logged_in'] = True
            st.success("تم الاتصال بنجاح.. جاري التحميل")
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")
else:
    # 4. لوحة التحكم المرنة
    st.sidebar.title("🎮 لوحة التحكم")
    menu = ["🤖 المساعد الذكي", "📊 المحاسب الذكي", "⚙️ الإعدادات"]
    choice = st.sidebar.selectbox("اختر البرنامج المطلوب:", menu)

    # --- موديول المساعد الذكي ---
    if choice == "🤖 المساعد الذكي":
        st.header("🤖 عقل مُنجز (Gemini V9)")
        st.info("المساعد جاهز للعمل بـ دقة متناهية.")
        
        prompt = st.chat_input("تحدث مع مُنجز...")
        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
                
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                with st.chat_message("assistant"):
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"حدث خطأ في الاتصال بالذكاء الاصطناعي: {e}")

    # --- موديول المحاسب الذكي ---
    elif choice == "📊 المحاسب الذكي":
        st.header("📊 المحاسب الذكي")
        st.write("سيتم تفعيل معادلات (1.14) و (0.90) هنا بكل دقة.")

    # --- نظام الإعدادات والخروج ---
    elif choice == "⚙️ الإعدادات":
        if st.sidebar.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.rerun()
