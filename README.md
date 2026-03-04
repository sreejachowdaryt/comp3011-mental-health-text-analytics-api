# comp3011-mental-health-text-analytics-api

A secure, database-driven RESTful API for detecting mental health indicators 
(Depression, Anxiety, Normal) from user-generated text using machine learning. 

Developed for COMP3011 - Web Services and Web Data
University of Leeds - 2025/26

---

## Project Overview 

This API allows users to:
- Register and authenticate using JWT 
- Create, update, retrive and delete posts (CRUD)
- Automatically generate ML-based mental health predictions 
- View latest and historical prediction results 
- Store prediction history with text snapshots for auditability 

The system integrates:
- FastAPI (Web Framework)
- PostgreSQL (Relational Database)
- SQLAlchemy ORM 
- JWT Authentication 
- Machine Learning model (LogReg + TF-IDF)

The system enables users to submit text and receive ML-based mental health predictons while preserving prediction history. 

---

## System Architecture

Client → FastAPI Application → PostgreSQL Database
                             ↳ Authentication Layer (JWT)
                             ↳ Posts Serivce (CRUD)
                             ↳ Prediction Service (ML Model)

Key Components:
- `auth` → User registration & login
- `posts` → CRUD operations
- `predictions` → Model results & history
- `predict` → Direct prediction endpoint
- JWT-based protected routes

### Architectural Principles

- Separation of concerns
- Service-based structure
- ORM-based database abstraction
- Stateless authentication (JWT)
- Versioned ML model tracking
- Historical prediction preservation

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT (python-jose) |
| Password Hashing | bcrypt (passlib) |
| ML Model | Logistic Regression + TF-IDF |
| API Docs | Swagger / OpenAPI |

---

## Database Design

### User 
- id (PK)
- email 
- password_hash
- role 
- created_at

### Post 
- id (PK)
- text 
- source 
- created_at 
- (FK) user_id 

### Predictions 
- id 
- post_id (FK → Post.id)
- label 
- confidence 
- model_version
- text_snapshot 
- created_at 

---

## API Design

The API follows REST conventions:

- `POST /auth/register`
- `POST /auth/login`
- `POST /posts/`
- `GET /posts/`
- `PUT /posts/{id}`
- `DELETE /posts/{id}`
- `GET /posts/{id}/prediction/latest`
- `GET /posts/{id}/prediction/history`
- `POST /predict` (direct inference endpoint)

### HTTP Standards Used

- 200 – Success
- 201 – Created
- 401 – Unauthorized
- 404 – Not Found
- 422 – Validation Error

All responses use structured JSON.

### Access to API Documentation

Full API documentation is available in PDF format:

👉 [API Documentation (PDF)](docs/api_documentation.pdf)

---

## Authentication and Security

The API uses JWT (JSON Web Tokens)

Workflow:
1. User Registers
2. User logs in  
3. Server issues signed JWT token 
4. Token required for protected routes
Use `Authorization: Bearer <token>` header for protected endpoints

Example: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

### Security Features 

- Password hashing using bcrypt
- Stateless token validation
- Expiry-based access control
- Environment-based secret configuration

---

## Machine Learning Integration 

### Model 

- Logistic Regression
- TF-IDF Vectorisation
- Version: `logreg-tfidf-v1`

### Prediction Lifecycle

1. User creates post
2. API stores post
3. Prediction service runs inference
4. Prediction stored with:
   - label
   - confidence
   - model_version
   - text_snapshot
5. If post text updates → new prediction row created

This ensures full historical traceability.

---

## Version Control Strategy 

This repository demonstrates:

- Incremental feature-based commits
- Migration tracking with Alembic
- Clear modular structure
- Separation of models, schemas, services, and API layers

Commit history reflects:

- Authentication implementation
- CRUD development
- ML integration
- Prediction history enhancement
- Security locking of endpoints
- Schema evolution (text_snapshot addition)

---

## Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2️⃣ Create Virtual Environment
```bash
python -m venv .venv
```

Activate Environment

Windows:
```bash
.venv\Scripts\activate
```

Mac/Linux:
```bash
source .venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a .env file in the root directory:

DATABASE_URL=postgresql://username:password@localhost:5432/mh_api      
JWT_SECRET_KEY=your_secret_key         
JWT_ALGORITHM=HS256      
ACCESS_TOKEN_EXPIRE_MINUTES=30      

### 5️⃣ Run Database Migrations
```bash
alembic upgrade head
```

### 6️⃣ Run the API
```bash
uvicorn app.main:app --reload
```

API will run at:

http://127.0.0.1:8000

Swagger UI:

http://127.0.0.1:8000/docs
