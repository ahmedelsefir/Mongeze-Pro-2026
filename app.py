"""Streamlit UI and FastAPI Gmail-trigger endpoint for Mongez AI."""

from pathlib import Path
from typing import Any

import joblib
import streamlit as st
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from agent import MongezAgent

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "mongez_model.pkl"
app = FastAPI(title="Mongez AI Gmail webhook", version="2.0.0")


class GmailWebhook(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sender: str = Field(alias="from", max_length=500)
    subject: str = Field(max_length=1000)
    snippet: str = Field(default="", max_length=5000)


@app.post("/gmail-webhook")
def gmail_webhook(email: GmailWebhook) -> dict[str, str]:
    """Create a review-only response from supplied fields; never access/send email."""
    prompt = (
        f"ساعدني في صياغة رد على بريد. From: {email.sender}. "
        f"Subject: {email.subject}. Message: {email.snippet}"
    )
    return {"reply": MongezAgent().check_gmail() + "\n\n" + prompt}


@st.cache_resource
def load_brain() -> dict[str, Any]:
    """Load the local model, training it from data.csv the first time if needed."""
    if not MODEL_PATH.exists():
        from train import train_model

        train_model()
    return joblib.load(MODEL_PATH)


def answer_question(question: str, brain: dict[str, Any] | None = None) -> str | None:
    """Return a dataset-grounded answer, or None when the question is out of scope."""
    text = (question or "").strip()
    if not text:
        return None
    brain = brain or load_brain()
    classifier = brain["classifier"]
    probabilities = classifier.predict_proba([text])[0]
    best_index = probabilities.argmax()
    confidence = float(probabilities[best_index])
    if confidence < brain.get("min_confidence", 0.30):
        return None
    intent = classifier.classes_[best_index]
    return brain["answers"].get(intent)


if __name__ == "__main__":
    st.set_page_config(page_title="مُنجز - خدمات المهندسين", page_icon="🛠️")
    st.title("🛠️ مُنجز | مساعد خدمات المهندس أحمد مصطفى")
    st.caption("إجابات محلية من نموذج مُدرّب على data.csv — الخدمات في المهندسين فقط.")
    question = st.chat_input("اسأل عن تركيب الكاميرات أو صيانة DVR أو الشبكات أو الدش والشاشات")
    if question:
        try:
            reply = answer_question(question)
            if reply:
                st.chat_message("user").write(question)
                st.chat_message("assistant").write(reply)
            else:
                st.info("السؤال خارج نطاق البيانات المتاحة. اسأل عن الخدمات المذكورة أو عن منطقة المهندسين.")
        except Exception as error:
            st.error(f"تعذر تحميل النموذج المحلي: {error}")
