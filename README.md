# Mongez AI

منجز مساعد عربي بواجهات Telegram وFastAPI وStreamlit. منطق المحادثة المركزي في `agent.py`، والأدوات والتخزين المحلي في `tools.py`.

## التثبيت والتشغيل محلياً

يتطلب Python 3.10 أو أحدث:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

ملف `.env.example` للتوثيق فقط؛ لا يُحمّل تلقائياً. عيّن المتغيرات في بيئة التشغيل أو حمّلها بأداة إدارة أسرار مناسبة:

- `TELEGRAM_TOKEN`: مطلوب لتشغيل بوت Telegram.
- `OWNER_TELEGRAM_IDS`: موصى به؛ معرّف Telegram الرقمي للمالك، ويمكن فصل عدة معرّفات بفواصل. يظل اسم المستخدم القديم `ahmedelsefir` أو `ahmedmostafa` مدعوماً للتوافق، لكن المعرّف الرقمي أكثر أماناً.

```bash
export TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
export OWNER_TELEGRAM_IDS="123456789"
python bot.py
```

تشغيل API بوت Telegram محلياً (بدلاً من تشغيل البوت polling):

```bash
uvicorn bot:app --host 127.0.0.1 --port 8000
```

المسارات: `GET /` و`POST /chat`. واجهة `/chat` عامة وتعمل دائماً في وضع الأعمال؛ لا توجد مصادقة مالك عبر HTTP.

## النشر على Hugging Face Spaces (Docker)

1. أنشئ Space جديداً واختر **Docker** SDK، ثم ارفع ملفات المستودع بما فيها `Dockerfile` و`requirements.txt`.
2. من صفحة Space افتح **Settings → Variables and secrets** وأضف:
   - `TELEGRAM_TOKEN` كـ **Secret**، بقيمة token الذي أنشأه BotFather. لا تضعه في الكود أو README.
   - `OWNER_TELEGRAM_IDS` كـ **Variable** (أو Secret إن رغبت)، بقيمة المعرّف الرقمي لحساب المالك، مثل `123456789`. يمكن وضع عدة معرّفات مفصولة بفواصل.
3. احفظ الإعدادات وأعد تشغيل Space أو انتظر إعادة البناء. Dockerfile يستخدم `python:3.11-slim` ويثبت الحزم باستخدام `pip install -r requirements.txt`.
4. الحاوية تشغّل بوت Telegram عبر polling، وتشغّل بجانبه تطبيق FastAPI من `bot.py:app` على `0.0.0.0:7860` لتلبية فحص HTTP الخاص بـ Space. إعداد `PORT` مدعوم؛ إن لم يُحدد يُستخدم `7860`. لا حاجة إلى إدخال `TELEGRAM_TOKEN` في إعدادات Dockerfile.
5. تحقق من أن Space في حالة **Running**، ثم أرسل `/start` للبوت في Telegram. مسار `GET /` هو فحص صحة بسيط؛ و`POST /chat` متاح أيضاً لكنه عام ومقصور على وضع الأعمال.

هذا النشر يستخدم `bot.py` فقط للبوت وواجهة API الخاصة به. لا يشغّل `streamlit run app.py` ولا يشغّل Webhook البريد في `app.py`، ولذلك لا يوجد تعارض بينها وبين Streamlit أو FastAPI الآخر. عند تشغيل webhook البريد محلياً، استخدم منفذاً منفصلاً:

```bash
uvicorn app:app --host 127.0.0.1 --port 8001
```

وتشغيل Streamlit محلياً:

```bash
streamlit run app.py
```

واجهة Streamlit تستخدم `data.csv` وتدرب النموذج المحلي عند غياب `mongez_model.pkl`. شاشة `main.py` القديمة تستخدم مكتبة `google-generativeai` اختيارياً؛ لا يحتاج بوت Telegram إلى `GEMINI_API_KEY`.

## حدود الصلاحيات والبيانات

- ميزات المالك الشخصية (حفظ/بحث الذاكرة، المهام، التلخيص، مساعدة الكود والبريد) متاحة في Telegram للمالك فقط. المستخدمون الآخرون يحصلون على ردود شركة رؤية الخير وخدمات المهندسين فقط.
- مساعدة البريد تحضّر اقتراحات للمراجعة؛ لا يتصل الوكيل بـ Gmail ولا يرسل أو يحذف البريد تلقائياً.
- الذاكرة في `memory.json`، والمهام في `tasks.txt`، وطلبات الخدمات في `orders.txt` بجانب ملفات المشروع. تخزين Space المحلي قد لا يكون دائماً بين عمليات إعادة البناء؛ استخدم تخزيناً دائماً أو قاعدة بيانات خارجية إذا كانت المحافظة على هذه البيانات مطلوبة.
- الطلبات العامة تُسجل في `orders.txt` و`memory.json`. لا تضع بيانات حساسة في محادثة أو ذاكرة مشتركة.
- فحص الكود تشخيص محلي محدود ولا ينفذ الكود. الإصلاح الدقيق لأخطاء التشغيل يحتاج رسالة الخطأ والسياق؛ لا يوجد نموذج LLM ضمن الوكيل المركزي حالياً.

## ملاحظات البناء والأمان

- أبقينا مسارات `agent.py`, `bot.py`, `tools.py`, `app.py`, و`main.py` المعروفة، ولم نغيّر قاعدة البيانات القديمة `mongez_v4.db`.
- المتطلبات تغطي جميع الواجهات الموجودة. لذلك Docker يثبت أيضاً بعض الحزم الأثقل مثل Streamlit وscikit-learn، رغم أن بوت Telegram وحده لا يستخدمهما؛ `python:3.11-slim` يخفف صورة الأساس لكن الحجم النهائي يتأثر بـ `requirements.txt`.
- لا يُعد `python bot.py` بدون `TELEGRAM_TOKEN`؛ يظهر خطأ واضح عند غيابه. لا حاجة إلى `GEMINI_API_KEY` لتشغيل البوت.
- قبل إتاحة FastAPI للعامة، أضف مصادقة وتحديد معدل الاستخدام. مسارا `/chat` و`/gmail-webhook` لا يثبتان هوية المالك.
- استخدم `OWNER_TELEGRAM_IDS` بمعرّف Telegram الرقمي؛ الاعتماد على اسم المستخدم وحده أقل أماناً. كما أن تخزين JSON والطلبات نصياً مناسب للتشغيل الفردي فقط وليس للكتابة المتزامنة الكثيفة.
