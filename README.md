# SkillForge AI 🚀
### AI-Powered Career Skill Gap Analyzer, Learning Roadmap & Interview Simulator

SkillForge AI is a modern full-stack application designed to help software engineering students evaluate their readiness for target roles (Software Engineer, Backend Developer, Data Engineer, ML Engineer, etc.). It analyzes job descriptions, pinpoints technical skill gaps, generates custom week-by-week learning roadmaps, recommends targeted portfolio projects, and conducts interactive AI technical interviews.

---

## 🛠️ Technology Stack

- **Frontend**: React.js (Vite), JavaScript, React Router, Axios, Recharts, Lucide Icons, Vanilla CSS3 (Custom Design System with Glassmorphism)
- **Backend**: Python, FastAPI, Pydantic v2, Uvicorn, RESTful API
- **Database** *(Phase 2+)*: PostgreSQL & SQLAlchemy ORM
- **Authentication** *(Phase 3+)*: JWT tokens with Passlib & Bcrypt password hashing
- **AI Integration** *(Phase 5+)*: Pluggable Backend AI Service Layer (Configurable LLM provider)

---

## 📁 Project Folder Structure

```
SkillForge-AI/
├── frontend/                  # React + Vite Client Application
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page views
│   │   ├── layouts/           # Layout wrappers
│   │   ├── services/          # API client and service calls (axios)
│   │   ├── hooks/             # Custom React hooks
│   │   ├── context/           # React Context state management
│   │   └── utils/             # Helper utilities & formatters
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── backend/                   # FastAPI Server Application
│   ├── app/
│   │   ├── main.py            # FastAPI entry point & CORS configuration
│   │   ├── database.py        # Database connection stub (Phase 2)
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── schemas/           # Pydantic data validation schemas
│   │   ├── routers/           # API route modules (health, auth, etc.)
│   │   ├── services/          # Core business logic & AI service wrapper
│   │   ├── dependencies/      # FastAPI dependency injection
│   │   └── utils/             # Security & helper scripts
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment template
│
├── README.md
├── .gitignore
└── docker-compose.yml
```

---

## ⚙️ Phase 1 Setup & Development Instructions

### 1. Launch Backend (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Activate Virtual Environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Run Uvicorn Development Server
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Swagger Interactive Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/health`

### 2. Launch Frontend (React + Vite)

```bash
# Open a second terminal and navigate to frontend directory
cd frontend

# Start Vite Development Server
npm run dev
```
- Local URL: `http://localhost:5173`

---

## 🧪 Testing React → FastAPI Connection

1. Open `http://localhost:5173` in your browser.
2. Click the **"Test FastAPI Backend Health"** button on the home page.
3. Verify that the live backend status response (`status: healthy`, message, timestamp, version) is fetched and displayed inside the green response card.

---

## 📋 Implementation Roadmap

- [x] **Phase 1**: Project Structure, Vite+React, FastAPI setup, CORS, Health Check API & Verification UI.
- [x] **Phase 2**: PostgreSQL & SQLAlchemy database setup & ORM models with Alembic migrations.
- [x] **Phase 3**: User registration, login, JWT authentication & protected routes with bcrypt security.
- [x] **Phase 4**: User profile & technical skill inventory CRUD management.
- [x] **Phase 5**: Job Description Analyzer via AI service layer (Gemini + fallback parser).
- [x] **Phase 6**: Skill Gap Analysis engine comparing user skills vs job requirements.
- [x] **Phase 7**: Career Readiness Score calculation algorithm (4-pillar composite scoring).
- [x] **Phase 8**: Personalized AI Learning Roadmap generator with week-by-week progress tracking.
- [x] **Phase 9**: Project Recommendation Engine for hands-on capstone portfolio building.
- [x] **Phase 10**: AI Technical Interview Simulator & evaluation system with real-time feedback.
- [x] **Phase 11**: Executive Analytics Dashboard & Recharts visualizations.
- [x] **Phase 12**: Design polish, dark-mode glassmorphic CSS design system, responsive UI.
- [x] **Phase 13**: Automated Pytest & Integration testing (72/72 tests passing).
- [x] **Phase 14**: Dockerization & Deployment readiness (multi-stage Dockerfile, docker-compose, nginx).
