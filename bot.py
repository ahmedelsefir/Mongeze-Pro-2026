"""FastAPI backend for the Mongez AI assistant."""

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai

MODEL_NAME = "gemini-2.5-flash"

app = FastAPI(title="Mongez AI", version="1.0.0")


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a simple health/welcome response."""
    return {"message": "Welcome to Mongez AI"}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    """Generate a response using Gemini 2.5 Flash."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="The Gemini API is not configured. Set the GEMINI_API_KEY environment variable.",
        )

    try:
        client = genai.Client(api_key=api_key)
        result = client.models.generate_content(
            model=MODEL_NAME,
            contents=request.prompt,
        )
        answer = result.text
        if not answer:
            raise ValueError("Gemini returned an empty response")
        return {"response": answer}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The Gemini API request failed.",
        ) from exc
