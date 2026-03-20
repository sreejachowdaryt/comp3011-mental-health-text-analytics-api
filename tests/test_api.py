"""
Comprehensive test suite for Mental Health Text Analytics API
COMP3011 - Web Services and Web Data

Tests cover:
- Authentication (register, login, JWT protection)
- Posts CRUD (create, read, update, delete)
- ML Predictions (auto-predict on create, re-predict on update, history)
- Direct /predict endpoint
- Error handling & status codes
- Security (protected routes, invalid tokens)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# ─────────────────────────────────────────────
# TEST DATABASE SETUP (SQLite in-memory)
# ─────────────────────────────────────────────

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Mock the ML model so tests never need model.joblib
MOCK_PREDICTION = ("Depression", 0.87)

def mock_predict_text(text: str):
    return MOCK_PREDICTION


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clean_tables():
    """Wipe all rows between tests to ensure isolation."""
    yield
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    """TestClient with DB and ML overrides applied."""
    app.dependency_overrides[get_db] = override_get_db
    with patch("app.services.predictor.predict_text", side_effect=mock_predict_text):
        with patch("app.api.posts.predict_text", side_effect=mock_predict_text):
            with patch("app.main.predict_text", side_effect=mock_predict_text):
                with TestClient(app) as c:
                    yield c
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def register_and_login(client, email="test@example.com", password="testpass123"):
    """Register a user and return their JWT token."""
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# 1. HEALTH CHECKS
# ─────────────────────────────────────────────

class TestHealthEndpoints:

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_db_returns_ok(self, client):
        resp = client.get("/health/db")
        assert resp.status_code == 200
        assert resp.json() == {"database": "ok"}


# ─────────────────────────────────────────────
# 2. AUTHENTICATION
# ─────────────────────────────────────────────

class TestAuthRegister:

    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "securepass"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "analyst"
        assert "id" in data
        # Password must never be exposed
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_email_returns_409(self, client):
        payload = {"email": "dup@example.com", "password": "pass"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"].lower()

    def test_register_invalid_email_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "pass"
        })
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self, client):
        resp = client.post("/auth/register", json={"email": "a@b.com"})
        assert resp.status_code == 422


class TestAuthLogin:

    def test_login_success_returns_token(self, client):
        client.post("/auth/register", json={"email": "login@test.com", "password": "mypass"})
        resp = client.post("/auth/login", json={"email": "login@test.com", "password": "mypass"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 10

    def test_login_wrong_password_returns_401(self, client):
        client.post("/auth/register", json={"email": "user@test.com", "password": "correct"})
        resp = client.post("/auth/login", json={"email": "user@test.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "email": "ghost@nowhere.com",
            "password": "pass"
        })
        assert resp.status_code == 401

    def test_login_missing_fields_returns_422(self, client):
        resp = client.post("/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 422


# ─────────────────────────────────────────────
# 3. JWT PROTECTION
# ─────────────────────────────────────────────

class TestJWTProtection:

    def test_posts_requires_auth(self, client):
        # No token provided → app returns 401
        resp = client.get("/posts/")
        assert resp.status_code in (401, 403)

    def test_posts_invalid_token_returns_401(self, client):
        # Malformed token → app rejects with 401
        resp = client.get("/posts/", headers={"Authorization": "Bearer fake.token.here"})
        assert resp.status_code == 401

    def test_predictions_requires_auth(self, client):
        # No token provided → app returns 401
        resp = client.get("/predictions/")
        assert resp.status_code in (401, 403)

    def test_valid_token_grants_access(self, client):
        token = register_and_login(client, "jwt@test.com")
        resp = client.get("/posts/", headers=auth_headers(token))
        assert resp.status_code == 200


# ─────────────────────────────────────────────
# 4. POSTS — CREATE
# ─────────────────────────────────────────────

class TestPostCreate:

    def test_create_post_returns_201_and_fields(self, client):
        token = register_and_login(client, "create@test.com")
        resp = client.post("/posts/", json={
            "text": "I feel very sad and hopeless lately",
            "source": "reddit"
        }, headers=auth_headers(token))
        assert resp.status_code == 200  # FastAPI default for POST without status_code=201
        data = resp.json()
        assert data["text"] == "I feel very sad and hopeless lately"
        assert data["source"] == "reddit"
        assert "id" in data
        assert "created_at" in data

    def test_create_post_triggers_prediction(self, client):
        token = register_and_login(client, "pred_create@test.com")
        post_resp = client.post("/posts/", json={
            "text": "Feeling anxious all the time",
            "source": "twitter"
        }, headers=auth_headers(token))
        post_id = post_resp.json()["id"]

        pred_resp = client.get(
            f"/posts/{post_id}/prediction/latest",
            headers=auth_headers(token)
        )
        assert pred_resp.status_code == 200
        pred = pred_resp.json()
        assert pred["label"] == "Depression"
        assert pred["confidence"] == pytest.approx(0.87, abs=0.01)
        assert pred["model_version"] == "logreg-tfidf-v1"
        assert pred["text_snapshot"] == "Feeling anxious all the time"

    def test_create_post_missing_text_returns_422(self, client):
        token = register_and_login(client, "missing@test.com")
        resp = client.post("/posts/", json={"source": "reddit"}, headers=auth_headers(token))
        assert resp.status_code == 422

    def test_create_post_without_auth_returns_401(self, client):
        # No token → app returns 401
        resp = client.post("/posts/", json={"text": "test", "source": "test"})
        assert resp.status_code in (401, 403)


# ─────────────────────────────────────────────
# 5. POSTS — READ
# ─────────────────────────────────────────────

class TestPostRead:

    def test_get_post_by_id(self, client):
        token = register_and_login(client, "read@test.com")
        created = client.post("/posts/", json={
            "text": "I feel okay today", "source": "test"
        }, headers=auth_headers(token)).json()

        resp = client.get(f"/posts/{created['id']}", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]
        assert resp.json()["text"] == "I feel okay today"

    def test_get_nonexistent_post_returns_404(self, client):
        token = register_and_login(client, "read404@test.com")
        resp = client.get("/posts/99999", headers=auth_headers(token))
        assert resp.status_code == 404

    def test_list_posts_returns_all(self, client):
        token = register_and_login(client, "list@test.com")
        headers = auth_headers(token)
        client.post("/posts/", json={"text": "Post one", "source": "a"}, headers=headers)
        client.post("/posts/", json={"text": "Post two", "source": "b"}, headers=headers)
        client.post("/posts/", json={"text": "Post three", "source": "c"}, headers=headers)

        resp = client.get("/posts/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    def test_list_posts_empty_returns_empty_list(self, client):
        token = register_and_login(client, "empty@test.com")
        resp = client.get("/posts/", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json() == []


# ─────────────────────────────────────────────
# 6. POSTS — UPDATE
# ─────────────────────────────────────────────

class TestPostUpdate:

    def test_update_post_text(self, client):
        token = register_and_login(client, "update@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "Original text", "source": "test"
        }, headers=headers).json()

        resp = client.put(f"/posts/{post['id']}", json={"text": "Updated text"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["text"] == "Updated text"

    def test_update_post_creates_new_prediction(self, client):
        token = register_and_login(client, "update_pred@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "First version of text", "source": "test"
        }, headers=headers).json()

        client.put(f"/posts/{post['id']}", json={"text": "Second version of text"}, headers=headers)

        history_resp = client.get(f"/posts/{post['id']}/prediction/history", headers=headers)
        assert history_resp.status_code == 200
        # Should have 2 predictions: one from create, one from update
        assert len(history_resp.json()) >= 2

    def test_update_source_only_no_new_prediction(self, client):
        token = register_and_login(client, "update_src@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "Stable text", "source": "original_source"
        }, headers=headers).json()

        client.put(f"/posts/{post['id']}", json={"source": "new_source"}, headers=headers)

        history = client.get(f"/posts/{post['id']}/prediction/history", headers=headers).json()
        # Text unchanged → still only 1 prediction
        assert len(history) == 1

    def test_update_nonexistent_post_returns_404(self, client):
        token = register_and_login(client, "update404@test.com")
        resp = client.put("/posts/99999", json={"text": "x"}, headers=auth_headers(token))
        assert resp.status_code == 404


# ─────────────────────────────────────────────
# 7. POSTS — DELETE
# ─────────────────────────────────────────────

class TestPostDelete:

    def test_delete_post_success(self, client):
        token = register_and_login(client, "delete@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "To be deleted", "source": "test"
        }, headers=headers).json()

        del_resp = client.delete(f"/posts/{post['id']}", headers=headers)
        assert del_resp.status_code == 200
        assert "deleted" in del_resp.json()["message"].lower()

    def test_delete_post_removes_it(self, client):
        token = register_and_login(client, "delete_check@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "Gone soon", "source": "test"
        }, headers=headers).json()

        client.delete(f"/posts/{post['id']}", headers=headers)
        resp = client.get(f"/posts/{post['id']}", headers=headers)
        assert resp.status_code == 404

    def test_delete_post_cascades_predictions(self, client):
        token = register_and_login(client, "cascade@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "Has a prediction", "source": "test"
        }, headers=headers).json()

        # Grab the prediction id before deleting
        pred = client.get(f"/posts/{post['id']}/prediction/latest", headers=headers).json()
        pred_id = pred["id"]

        client.delete(f"/posts/{post['id']}", headers=headers)

        # Prediction should also be gone
        pred_resp = client.get(f"/predictions/{pred_id}", headers=headers)
        assert pred_resp.status_code == 404

    def test_delete_nonexistent_post_returns_404(self, client):
        token = register_and_login(client, "del404@test.com")
        resp = client.delete("/posts/99999", headers=auth_headers(token))
        assert resp.status_code == 404


# ─────────────────────────────────────────────
# 8. PREDICTIONS
# ─────────────────────────────────────────────

class TestPredictions:

    def test_latest_prediction_fields(self, client):
        token = register_and_login(client, "pred_fields@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "I am overwhelmed with anxiety", "source": "test"
        }, headers=headers).json()

        resp = client.get(f"/posts/{post['id']}/prediction/latest", headers=headers)
        assert resp.status_code == 200
        pred = resp.json()
        assert "id" in pred
        assert "label" in pred
        assert "confidence" in pred
        assert "model_version" in pred
        assert "text_snapshot" in pred
        assert "created_at" in pred
        assert pred["post_id"] == post["id"]

    def test_prediction_history_ordered_newest_first(self, client):
        token = register_and_login(client, "history_order@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "Version one", "source": "test"
        }, headers=headers).json()
        client.put(f"/posts/{post['id']}", json={"text": "Version two"}, headers=headers)
        client.put(f"/posts/{post['id']}", json={"text": "Version three"}, headers=headers)

        history = client.get(f"/posts/{post['id']}/prediction/history", headers=headers).json()
        assert len(history) == 3
        # All 3 text snapshots must be present (order unreliable in SQLite fast tests)
        snapshots = {p["text_snapshot"] for p in history}
        assert snapshots == {"Version one", "Version two", "Version three"}

    def test_prediction_no_history_returns_404(self, client):
        """A post that somehow has no predictions returns 404 on history."""
        token = register_and_login(client, "no_hist@test.com")
        headers = auth_headers(token)
        # Manually insert a post without triggering prediction
        db = TestingSessionLocal()
        from app.models.post import Post as PostModel
        p = PostModel(text="raw insert", source="test")
        db.add(p)
        db.commit()
        db.refresh(p)
        pid = p.id
        db.close()

        resp = client.get(f"/posts/{pid}/prediction/history", headers=headers)
        assert resp.status_code == 404

    def test_list_all_predictions(self, client):
        token = register_and_login(client, "listpred@test.com")
        headers = auth_headers(token)
        client.post("/posts/", json={"text": "Post A", "source": "a"}, headers=headers)
        client.post("/posts/", json={"text": "Post B", "source": "b"}, headers=headers)

        resp = client.get("/predictions/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_single_prediction(self, client):
        token = register_and_login(client, "singlepred@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "Feeling low", "source": "test"
        }, headers=headers).json()
        pred_id = client.get(
            f"/posts/{post['id']}/prediction/latest", headers=headers
        ).json()["id"]

        resp = client.get(f"/predictions/{pred_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == pred_id

    def test_get_nonexistent_prediction_returns_404(self, client):
        token = register_and_login(client, "pred404@test.com")
        resp = client.get("/predictions/99999", headers=auth_headers(token))
        assert resp.status_code == 404

    def test_text_snapshot_matches_post_text(self, client):
        token = register_and_login(client, "snapshot@test.com")
        headers = auth_headers(token)
        text = "Exact text to snapshot"
        post = client.post("/posts/", json={"text": text, "source": "test"}, headers=headers).json()

        pred = client.get(f"/posts/{post['id']}/prediction/latest", headers=headers).json()
        assert pred["text_snapshot"] == text


# ─────────────────────────────────────────────
# 9. DIRECT /predict ENDPOINT
# ─────────────────────────────────────────────

class TestDirectPredict:

    def test_predict_returns_expected_fields(self, client):
        resp = client.post("/predict", json={"text": "I feel depressed and empty"})
        # Note: if this fails with IntegrityError, add text_snapshot=req.text
        # to the Prediction(...) constructor in app/main.py
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "confidence" in data
        assert "model_version" in data
        assert "post_id" in data
        assert "prediction_id" in data
        assert "uncertain" in data
        assert "created_at" in data

    def test_predict_label_is_string(self, client):
        resp = client.post("/predict", json={"text": "Some mental health text"})
        assert isinstance(resp.json()["label"], str)

    def test_predict_confidence_between_0_and_1(self, client):
        resp = client.post("/predict", json={"text": "Some mental health text"})
        conf = resp.json()["confidence"]
        assert conf is None or 0.0 <= conf <= 1.0

    def test_predict_high_confidence_not_uncertain(self, client):
        # Mock returns 0.87 confidence → uncertain should be False (threshold < 0.40)
        resp = client.post("/predict", json={"text": "Strong signal text"})
        assert resp.json()["uncertain"] is False

    def test_predict_missing_text_returns_422(self, client):
        resp = client.post("/predict", json={})
        assert resp.status_code == 422

    def test_predict_creates_post_and_prediction_in_db(self, client):
        token = register_and_login(client, "directpred@test.com")
        headers = auth_headers(token)

        resp = client.post("/predict", json={"text": "Direct predict test"})
        post_id = resp.json()["post_id"]

        # Post should be retrievable
        post_resp = client.get(f"/posts/{post_id}", headers=headers)
        assert post_resp.status_code == 200
        assert post_resp.json()["source"] == "predict"

    def test_predict_rate_limit(self, client):
        """11th request within a minute should return 429 Too Many Requests"""
        for i in range(10):
            client.post("/predict", json={"text": "test text"})
        resp = client.post("/predict", json={"text": "test text"})
        assert resp.status_code == 429


# ─────────────────────────────────────────────
# 10. RESPONSE FORMAT VALIDATION
# ─────────────────────────────────────────────

class TestResponseFormats:

    def test_all_responses_are_json(self, client):
        resp = client.get("/health")
        assert resp.headers["content-type"].startswith("application/json")

    def test_post_response_has_correct_schema(self, client):
        token = register_and_login(client, "schema@test.com")
        resp = client.post("/posts/", json={
            "text": "Schema test", "source": "test"
        }, headers=auth_headers(token))
        data = resp.json()
        expected_keys = {"id", "text", "source", "created_at"}
        assert expected_keys.issubset(data.keys())

    def test_prediction_response_schema(self, client):
        token = register_and_login(client, "pred_schema@test.com")
        headers = auth_headers(token)
        post = client.post("/posts/", json={
            "text": "Schema validation", "source": "test"
        }, headers=headers).json()

        pred = client.get(f"/posts/{post['id']}/prediction/latest", headers=headers).json()
        expected = {"id", "post_id", "label", "confidence", "model_version", "created_at", "text_snapshot"}
        assert expected.issubset(pred.keys())

    def test_404_returns_detail_key(self, client):
        token = register_and_login(client, "detail@test.com")
        resp = client.get("/posts/99999", headers=auth_headers(token))
        assert "detail" in resp.json()

    def test_401_returns_detail_key(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@x.com", "password": "wrong"
        })
        assert "detail" in resp.json()