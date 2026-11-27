# Mongez AI

منجز مساعد عربي محلي بواجهات Telegram وFastAPI وStreamlit. منطق المحادثة المركزي في `agent.py`، والأدوات والتخزين المحلي في `tools.py`.

## التثبيت والتشغيل

يتطلب Python 3.10 أو أحدث:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

انسخ `.env.example` إلى `.env` واضبط المتغيرات في بيئتك (ملف `.env` لا يُحمّل تلقائياً):

- `TELEGRAM_TOKEN`: مطلوب فقط لتشغيل بوت Telegram.
- `OWNER_TELEGRAM_IDS`: موصى به؛ معرّف Telegram الرقمي للمالك، ويمكن فصل عدة معرّفات بفواصل. يظل اسم المستخدم القديم `ahmedelsefir` أو `ahmedmostafa` مدعوماً للتوافق، لكن المعرّف الرقمي أكثر أماناً.

تشغيل البوت:

```bash
export TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
export OWNER_TELEGRAM_IDS="123456789"
python bot.py
```

تشغيل API بوت Telegram:

```bash
uvicorn bot:app --host 127.0.0.1 --port 8000
```

المسارات: `GET /` و`POST /chat`، وتعمل واجهة `/chat` دائماً في وضع الأعمال العام؛ لا توجد مصادقة مالك عبر HTTP.

تشغيل Webhook البريد في `app.py`:

```bash
uvicorn app:app --host 127.0.0.1 --port 8001
```

يرسل `POST /gmail-webhook` حقول `from` و`subject` و`snippet`. يعالج التطبيق البيانات المرسلة فقط ولا يتصل بـ Gmail ولا يرسل أي بريد. الأمر `/ايميل` في Telegram يطلب تفاصيل الرسالة لإعداد مسودة للمراجعة. لا توجد وظيفة إرسال تلقائي.

تشغيل واجهة الخدمات Streamlit:

```bash
streamlit run app.py
```

تستخدم الواجهة `data.csv` وتدرب النموذج المحلي عند غياب `mongez_model.pkl`. شاشة `main.py` القديمة تستخدم أيضاً مكتبة `google-generativeai` اختيارياً؛ لا يحتاج بوت Telegram أو منطق `MongezAgent` إلى مفتاح Gemini.

## حدود الصلاحيات والبيانات

- ميزات المالك الشخصية (حفظ/بحث الذاكرة، المهام، التلخيص، ومساعدة الكود والبريد) متاحة في Telegram للمالك فقط. المستخدمون الآخرون يحصلون على ردود شركة رؤية الخير وخدمات المهندسين فقط.
- الذاكرة في `memory.json`، والمهام في `tasks.txt`، وطلبات الخدمات في `orders.txt` بجانب ملفات المشروع. ملفات البيانات تنشأ عند أول كتابة؛ احمِ صلاحياتها وخذ نسخاً احتياطية.
- الطلبات العامة تُسجل في `orders.txt` و`memory.json`. لا تضع بيانات حساسة في محادثة أو ذاكرة مشتركة.
- فحص الكود تشخيص محلي محدود ولا ينفذ الكود. الإصلاح الدقيق لأخطاء التشغيل يحتاج رسالة الخطأ والسياق؛ لا يوجد نموذج LLM ضمن الوكيل المركزي حالياً.

## ملاحظات التوافق والبناء

- أبقينا `agent.py`, `bot.py`, `tools.py`, `app.py`, و`main.py` كواجهات/مسارات معروفة، ووحّدنا استخدام `MongezAgent` وملفات التخزين حول `tools.py` دون ترحيل أو تعديل `mongez_v4.db`.
- المتطلبات الآن مقتصرة على الحزم المستوردة فعلياً. `pandas` و`firebase-admin` و`honeybadger` و`google-genai` لم تعد مطلوبة من الكود الحالي. أبقينا `google-generativeai` لتوافق `main.py` و`assistant.py` القديمين.
- يلزم إعداد `TELEGRAM_TOKEN` قبل `python bot.py`؛ عدم إعداده يؤدي إلى خطأ مقصود وواضح. لا حاجة إلى `GEMINI_API_KEY` لتشغيل البوت.
- يجب حماية FastAPI من الإنترنت أو إضافة مصادقة/تحديد معدل الاستخدام قبل نشره. واجهة Gmail webhook عامة حالياً، ولا تُرسل البريد لكنها تُرجع نصاً مبنياً على بيانات الطلب.
- خزّن المعرّف الرقمي للمالك عبر `OWNER_TELEGRAM_IDS`؛ الاعتماد على اسم المستخدم وحده أقل أماناً. كما أن تخزين JSON والطلبات نصياً مناسب للتشغيل الفردي فقط وليس للكتابة المتزامنة الكثيفة.
