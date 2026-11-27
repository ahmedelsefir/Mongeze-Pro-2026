# Use the slim Python base image; dependencies are installed from the repository manifest.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

# FastAPI health/API endpoint for the Space; Telegram polling runs alongside it.
EXPOSE 7860

# Space routes its HTTP health checks to port 7860. Keep the bot in the
# foreground so container restarts are supervised by the Space runtime.
CMD ["sh", "-c", "uvicorn bot:app --host 0.0.0.0 --port ${PORT:-7860} & exec python bot.py"]
