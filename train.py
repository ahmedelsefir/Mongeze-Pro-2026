import csv
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data.csv"
MODEL_PATH = BASE_DIR / "mongez_model.pkl"


def train_model():
    """Train a small Arabic service-intent model from the local CSV dataset."""
    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    required = {"question", "intent", "answer", "service_area"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"{DATA_PATH.name} must contain these columns: {', '.join(sorted(required))}")

    questions = [row["question"].strip() for row in rows]
    intents = [row["intent"].strip() for row in rows]
    if any(not question for question in questions) or len(set(intents)) < 2:
        raise ValueError("Training data needs non-empty questions from at least two intent categories.")

    # Character n-grams work well for Arabic wording variations and spelling differences.
    classifier = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced")),
    ])
    classifier.fit(questions, intents)

    answers = {}
    for row in rows:
        answers.setdefault(row["intent"].strip(), row["answer"].strip())

    payload = {
        "classifier": classifier,
        "answers": answers,
        "service_area": "المهندسين",
        "min_confidence": 0.30,
    }
    import joblib
    joblib.dump(payload, MODEL_PATH)
    return MODEL_PATH


if __name__ == "__main__":
    output_path = train_model()
    print(f"تم تدريب النموذج وحفظه في: {output_path}")
