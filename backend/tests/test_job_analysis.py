"""
Unit tests for Job Analyzer AI service and API endpoints.
"""

import pytest
from app.models import User
from app.utils.security import create_access_token, hash_password
from app.services.ai_service import analyze_job_description, _extract_fallback_analysis


@pytest.fixture(autouse=True)
def setup_user(db):
    """Seed test user in database for each test."""
    test_user = User(
        id=1,
        email="job_tester@example.com",
        hashed_password=hash_password("TestPassword123!"),
        full_name="Job Test User"
    )
    db.add(test_user)
    db.commit()


def get_auth_header(user_id: int = 1):
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_ai_fallback_extractor():
    """Test heuristic fallback job analysis extraction."""
    sample_jd = """
    Senior Python Developer at TechCorp.
    We are looking for a Senior Software Engineer to build scalable APIs and backend services.
    Requirements:
    - 5+ years of experience with Python, FastAPI, and Django.
    - Strong database skills with PostgreSQL and Redis.
    - Cloud experience with AWS and Docker.
    - Excellent communication skills and teamwork.
    - Bachelor's degree in Computer Science.
    """

    res = _extract_fallback_analysis(sample_jd, job_title_hint="Senior Python Developer")
    assert res.job_title == "Senior Python Developer"
    assert "Python" in res.programming_languages or "Python" in res.required_skills
    assert "PostgreSQL" in res.databases or "PostgreSQL" in res.required_skills or "PostgreSQL" in res.keywords
    assert len(res.required_skills) > 0


def test_analyze_job_endpoint(client):
    """Test POST /api/job-analysis/analyze endpoint."""
    headers = get_auth_header()
    payload = {
        "job_title": "Full Stack React Developer",
        "company_name": "Acme Inc.",
        "job_description": "We are seeking a Full Stack Developer experienced with React, TypeScript, Node.js, and PostgreSQL. Must have 3+ years of experience building modern web applications, Docker experience, and solid teamwork skills."
    }

    response = client.post("/api/job-analysis/analyze", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["job_title"] == "Full Stack React Developer"
    assert data["company_name"] == "Acme Inc."
    assert "id" in data
    assert len(data["requirements"]) > 0


def test_get_analysis_history(client):
    """Test GET /api/job-analysis/history endpoint."""
    headers = get_auth_header()
    
    # Analyze a job first
    payload = {
        "job_title": "DevOps Engineer",
        "job_description": "Looking for a Cloud DevOps Engineer with Kubernetes, AWS, Terraform, Docker, and CI/CD pipelines expertise. Minimum 4 years experience required."
    }
    client.post("/api/job-analysis/analyze", json=payload, headers=headers)

    response = client.get("/api/job-analysis/history", headers=headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1
    assert history[0]["job_title"] == "DevOps Engineer"


def test_get_analysis_detail_and_delete(client):
    """Test GET /api/job-analysis/{id} and DELETE /api/job-analysis/{id}."""
    headers = get_auth_header()
    
    # Create analysis
    payload = {
        "job_title": "Data Scientist",
        "job_description": "We need a Data Scientist proficient in Python, SQL, Machine Learning, TensorFlow, and Pandas. Master degree preferred with 2+ years experience."
    }
    create_res = client.post("/api/job-analysis/analyze", json=payload, headers=headers)
    analysis_id = create_res.json()["id"]

    # Fetch detail
    detail_res = client.get(f"/api/job-analysis/{analysis_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == analysis_id

    # Delete
    del_res = client.delete(f"/api/job-analysis/{analysis_id}", headers=headers)
    assert del_res.status_code == 200

    # Fetch again should return 404
    get_again = client.get(f"/api/job-analysis/{analysis_id}", headers=headers)
    assert get_again.status_code == 404
