import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, auth, profile, skills, job_analysis, skill_gap, roadmap, interview, project, career_readiness

load_dotenv()

_app_env = os.getenv("APP_ENV", "development").lower()

# Disable interactive API docs in production to reduce attack surface.
# Swagger UI (/docs) and ReDoc (/redoc) are available in development only.
_docs_url = None if _app_env == "production" else "/docs"
_redoc_url = None if _app_env == "production" else "/redoc"

app = FastAPI(
    title="SkillForge AI API",
    description="AI-Powered Career Skill Gap Analyzer, Learning Roadmap & Interview Simulator API",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# CORS Middleware Configuration
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(skills.router)
app.include_router(job_analysis.router)
app.include_router(skill_gap.router)
app.include_router(roadmap.router)
app.include_router(interview.router)
app.include_router(project.router)
app.include_router(career_readiness.router)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "app": "SkillForge AI",
        "status": "running",
        "docs_url": "/docs"
    }
