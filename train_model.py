'''
Why?
This is best: it saves the entire pipeline (TF-IDF + Naive Bayes), 
so you don’t need separate vectorizer files.
'''

from pathlib import Path
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score
from sklearn.linear_model import LogisticRegression

DATA_PATH = Path("data/training_data.csv")
OUT_DIR = Path("app/ml")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    df = pd.read_csv(DATA_PATH)

    # Basic validation
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must have columns: text,label")

    X = df["text"].astype(str)
    y = df["label"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None
    )

    # Pipeline = vectorizer + classifier
    pipeline = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )

    pipeline.fit(X_train, y_train)

    # Quick evaluation (for your report/README)
    y_pred = pipeline.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    # Save whole pipeline (simplest + robust)
    joblib.dump(pipeline, OUT_DIR / "model.joblib")
    print(f"Saved model to {OUT_DIR / 'model.joblib'}")

if __name__ == "__main__":
    main()