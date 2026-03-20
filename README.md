# Mental Health Text Analytics API

> A secure, database-driven RESTful API for detecting mental health indicators from user-generated text using machine learning.

**COMP3011 — Web Services and Web Data | University of Leeds | 2025/26**

---

## Project Overview

This API classifies user-generated text into three mental health categories - **Depression**, **Anxiety**, and **Normal** — using a Logistic Regression + TF-IDF machine learning pipeline. The system provides authenticated users with full CRUD operations on text posts, automatic ML predictions on submission, complete prediction history with audit trails, and aggregate analytics.

### Key Features

- **JWT Authentication** - secure registration and login with bcrypt password hashing
- **Full CRUD on Posts** - create, read, update, delete text submissions
- **Automatic ML Prediction** - every post triggers inference on creation
- **Re-prediction on Update** - text changes generate a new prediction while preserving history
- **Prediction Audit Trail** - `text_snapshot` field records exact text used at inference time
- **Cascade Deletion** - deleting a post removes all associated predictions
- **Uncertainty Flagging** - predictions below 40% confidence are flagged as uncertain
- **Rate Limiting** - `/predict` limited to 10 requests/minute per IP (HTTP 429 on excess)
- **Model Versioning** - every prediction stores `model_version` for future model tracking
- **Analytics Endpoint** - aggregated label distribution and confidence statistics
- **Frontend Dashboard** - full HTML/CSS/JS interface served by FastAPI
- **Health Monitoring** - `/health` and `/health/db` endpoints for operational checks

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL 17 |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT (python-jose) |
| Password Hashing | bcrypt (passlib) |
| ML Model | Logistic Regression + TF-IDF (scikit-learn) |
| Rate Limiting | SlowAPI |
| API Docs | Swagger UI / OpenAPI |
| Testing | pytest (49 tests) |
| Deployment | Render |

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/health` | System liveness check | No |
| GET | `/health/db` | Database connectivity check | No |
| POST | `/auth/register` | Register a new user account | No |
| POST | `/auth/login` | Login and receive JWT token | No |
| GET | `/posts/` | List all posts | Yes |
| POST | `/posts/` | Create post + auto ML prediction | Yes |
| GET | `/posts/{post_id}` | Retrieve a single post by ID | Yes |
| PUT | `/posts/{post_id}` | Update post text + re-predict | Yes |
| DELETE | `/posts/{post_id}` | Delete post and cascade predictions | Yes |
| GET | `/posts/{post_id}/prediction/latest` | Get latest prediction for post | Yes |
| GET | `/posts/{post_id}/prediction/history` | Full prediction history for post | Yes |
| GET | `/predictions/` | List all latest predictions | Yes |
| GET | `/predictions/{prediction_id}` | Get single prediction by ID | Yes |
| POST | `/predict` | Direct ML inference (rate limited) | No |
| GET | `/analytics` | Aggregated prediction analytics | No |

---

## Database Design

```
User
├── id (PK)
├── email (unique)
├── password_hash
├── role
└── created_at

Post
├── id (PK)
├── text
├── source
├── created_at
└── user_id (FK → User.id)

Prediction
├── id (PK)
├── post_id (FK → Post.id, CASCADE DELETE)
├── label
├── confidence
├── model_version
├── text_snapshot
└── created_at
```

---

## System Architecture

```
Client → FastAPI Application → PostgreSQL Database
                             ↳ Authentication Layer (JWT)
                             ↳ Posts Service (CRUD)
                             ↳ Prediction Service (ML Model)
                             ↳ Analytics Service
```

### Project Structure

```
app/
├── api/
│   ├── auth.py          # Register & login routes
│   ├── posts.py         # CRUD routes + prediction triggers
│   └── predictions.py   # Prediction list & detail routes
├── core/
│   ├── config.py        # Environment variable loading
│   ├── deps.py          # JWT dependency injection
│   └── security.py      # Password hashing & token creation
├── db/
│   ├── base.py          # SQLAlchemy declarative base
│   ├── deps.py          # Database session dependency
│   └── session.py       # Engine & session factory
├── ml/
│   └── model.joblib     # Trained ML pipeline
├── models/
│   ├── user.py          # User ORM model
│   ├── post.py          # Post ORM model
│   └── prediction.py    # Prediction ORM model
├── schemas/
│   ├── auth.py          # Auth request/response schemas
│   ├── post.py          # Post request/response schemas
│   └── prediction.py    # Prediction response schemas
├── services/
│   └── predictor.py     # ML model loading & inference
└── main.py              # FastAPI app, routes, rate limiter
data/
└── training_data.csv    # Kaggle mental health corpus
static/
├── index.html           # Frontend dashboard
├── css/styles.css
└── js/
    ├── api.js
    ├── auth.js
    ├── dashboard.js
    ├── posts.js
    └── predictions.js
tests/
└── test_api.py          # 49 pytest tests
train_model.py           # ML pipeline training script
alembic/                 # Database migration scripts
```

---

## Authentication

The API uses JWT (JSON Web Tokens) for stateless authentication.

```
1. Register  →  POST /auth/register
2. Login     →  POST /auth/login  →  returns access_token
3. Use token →  Authorization: Bearer <access_token>
```

## Using the API via Swagger UI (/docs)

The interactive API documentation is available at:
- **Local:** http://127.0.0.1:8000/docs

### Step-by-step authentication in Swagger UI

**1. Register an account**
- Open `POST /auth/register`
- Click **Try it out**
- Enter your email and password:
```json
{
  "email": "you@example.com",
  "password": "yourpassword"
}
```
- Click **Execute**

**2. Login and get your token**
- Open `POST /auth/login`
- Click **Try it out**
- Enter the same credentials and click **Execute**
- Copy the `access_token` value from the response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**3. Authorise in Swagger**
- Click the **Authorize 🔒** button at the top right of the page
- In the **Value** field type:
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
- Click **Authorize** then **Close**

**4. Use protected endpoints**
- All endpoints marked with a 🔒 padlock are now accessible
- The token is automatically included in every request
- Token expires after **60 minutes** — repeat from Step 2 to refresh

### Authentication header format
All protected endpoints require this header:
```
Authorization: Bearer <your_token>
```

---

## Machine Learning Pipeline

**Dataset:** [Sentiment Analysis for Mental Health](https://www.kaggle.com/datasets/suchintikasarkar/sentiment-analysis-for-mental-health) — Kaggle (Sarkar, 2025)

**Labels:** `Depression`, `Anxiety`, `Normal`

**Pipeline steps:**
1. Data validation (text + label columns)
2. Stratified 80/20 train-test split
3. TF-IDF vectorisation (bigrams, English stopwords)
4. Logistic Regression with balanced class weights
5. Evaluation via precision, recall, F1-score
6. Serialisation to `app/ml/model.joblib` using joblib

**Prediction lifecycle:**
```
POST /posts/  →  Store text  →  Run inference  →  Store prediction with text_snapshot
PUT /posts/{id}  →  Text changed?  →  New prediction row created (history preserved)
GET /posts/{post_id}/prediction/latest Latest Prediction  → view the latest/updated/changed prediction of the post
```

---

## Local Setup

### Prerequisites
- Python 3.12
- PostgreSQL 17
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/sreejachowdaryt/comp3011-mental-health-text-analytics-api.git
cd comp3011-mental-health-text-analytics-api
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
```

**Windows:**
```bash
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/mh_api
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 5. Run Database Migrations
```bash
alembic upgrade head
```

### 6. Run the API
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **Frontend:** http://127.0.0.1:8000

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output: **49 passed**

The test suite uses an in-memory SQLite database and mocks the ML model — no external services required.

---

## API Documentation

Full API documentation is available in PDF format in the repository:

📄 [API Documentation (PDF)](https://github.com/sreejachowdaryt/comp3011-mental-health-text-analytics-api/blob/main/docs/Mental%20Health%20Text%20Analytics%20API%20-%20API%20Doc%20(Swagger%20UI).pdf)

Interactive documentation is also available via Swagger UI at `/docs` when the API is running.

---

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 401 | Unauthorized — invalid or expired token |
| 403 | Forbidden — missing Authorization header |
| 404 | Not Found |
| 409 | Conflict — email already registered |
| 422 | Validation Error — invalid request body |
| 429 | Too Many Requests — rate limit exceeded |

---

## Version Control Strategy

The commit history demonstrates incremental, feature-based development:

- Initial project structure and database setup
- Authentication implementation (register + login)
- CRUD operations for posts
- ML model integration and prediction service
- Prediction history and text_snapshot addition
- Security — JWT protection on all post routes
- Rate limiting on inference endpoint
- Analytics endpoint
- Frontend dashboard
- Testing suite (49 tests)
- Deployment configuration

---

## Deployment

The API is deployed on **Render**.

- **Platform:** Render (Free tier)
- **Database:** Render PostgreSQL
- **Live URL:** https://comp3011-mental-health-text-analytics-api.onrender.com

The application has been successfully deployed and is live on Render. However, the deployed instance currently 
encounters an HTTP 500 (Internal Server Error), which prevents users from logging into the system. Despite 
multiple debugging attempts, this issue could not be fully resolved within the project timeframe. 

As a result, the system will be demonstrated via local execution during the presentation, where full functionality, 
including user authentication, post management, and machine learning predictions - can be showcased. 

---

## License

Developed for academic purposes — COMP3011, University of Leeds, 2025/26.