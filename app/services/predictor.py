from pathlib import Path
import joblib

MODEL_PATH = Path(__file__).resolve().parents[1] / "ml" / "model.joblib"
_model = None

def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model

def predict_text(text: str):
    model = get_model()

    label = model.predict([text])[0]

    confidence = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba([text])[0]
        confidence = float(proba.max())

    return str(label), confidence