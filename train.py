import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data.csv"
MODEL_PATH = BASE_DIR / "mongez_model.pkl"


def train_model():
    """Train the Mongez intent classifier and save the local model."""
    with DATA_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    required = {"intent", "question", "answer"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("data.csv must contain the columns: intent,question,answer")

    questions = [row["question"].strip() for row in rows]
    intents = [row["intent"].strip() for row in rows]

    clf = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    clf.fit(questions, intents)

    answers = {}
    for row in rows:
        answers.setdefault(row["intent"].strip(), row["answer"].strip())

    joblib.dump({
        "classifier": clf,
        "answers": answers,
        "min_confidence": 0.30,
    }, MODEL_PATH)
    print("Mongez model trained and saved")


if __name__ == "__main__":
    train_model()
