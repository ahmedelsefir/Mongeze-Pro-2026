# Mongez AI

Mongez AI provides a Telegram assistant, a FastAPI API, and a Streamlit interface.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

No `GEMINI_API_KEY` is required. Set `TELEGRAM_TOKEN` only when running the Telegram bot:

```bash
export TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
python bot.py
```

## Gmail notifications

Zapier is only a trigger. Mongez AI Agent is the one who reads, understands, and replies. Zapier does NOT reply.

The `POST /gmail-webhook` endpoint accepts a JSON Gmail notification and returns an Agent-authored Telegram reply. For example:

```json
{
  "from": "sender@example.com",
  "subject": "Hello",
  "snippet": "A short preview of the message"
}
```

Run the FastAPI webhook with:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Send a Gmail notification to `POST /gmail-webhook`. It returns `{ "reply": "..." }` for Zapier to relay to Telegram. The endpoint processes only the supplied notification fields; it does not connect to Gmail, delete messages, or send email.

In Telegram, Ahmed can use `/ايميل` to ask Mongez AI Agent for help reviewing a message. The Agent can prepare a draft suggestion, but Ahmed must approve it; no email is sent automatically.

## Other interfaces

The Telegram bot keeps `TELEGRAM_TOKEN` as its only required runtime setting. The existing Streamlit interface can be started with `streamlit run app.py`.
