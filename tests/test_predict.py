from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_predict_returns_label():
    r = client.post("/predict", json={"text": "I feel hopeless and exhausted every day"})
    assert r.status_code == 200
    data = r.json()
    assert "label" in data
    assert data["label"] in ["depression", "anxiety", "normal"]  # adjust to your labels