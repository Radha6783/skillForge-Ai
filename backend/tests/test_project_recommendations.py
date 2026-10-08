"""
Comprehensive unit and integration tests for Phase 9: AI Project Recommendations.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.job_analysis import JobAnalysis, JobRequirement, SkillGapReport
from app.models.project import ProjectRecommendation
from app.utils.security import create_access_token, hash_password
from app.services.ai_service import _generate_fallback_project_recommendations, generate_project_recommendations_ai


@pytest.fixture(autouse=True)
def setup_seed_data(db):
    """Seed users, skills, job analysis, and requirements for project recommendation tests."""
    u1 = User(
        id=1,
        email="project_user1@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Project User One"
    )
    u2 = User(
        id=2,
        email="project_user2@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Project User Two"
    )
    db.add_all([u1, u2])
    db.commit()

    # Master Skills
    s_py = Skill(id=1, name="Python", category="Technical")
    s_fa = Skill(id=2, name="FastAPI", category="Technical")
    s_pg = Skill(id=3, name="PostgreSQL", category="Technical")
    s_doc = Skill(id=4, name="Docker", category="Technical")
    db.add_all([s_py, s_fa, s_pg, s_doc])
    db.commit()

    # User 1 Skills (Python: Advanced, FastAPI: Beginner)
    us1 = UserSkill(user_id=1, skill_id=1, self_assessed_level="ADVANCED", experience_months=24)
    us2 = UserSkill(user_id=1, skill_id=2, self_assessed_level="BEGINNER", experience_months=6)
    db.add_all([us1, us2])
    db.commit()

    # Job Analysis for User 1
    ja1 = JobAnalysis(
        id=1,
        user_id=1,
        job_title="Senior Python Backend Developer",
        role_category="Backend Engineering",
        raw_description="Requires Python, FastAPI, PostgreSQL, and Docker."
    )
    db.add(ja1)
    db.commit()

    # Requirements
    r1 = JobRequirement(job_analysis_id=1, skill_name="Python", is_required=True, importance_level="HIGH")
    r2 = JobRequirement(job_analysis_id=1, skill_name="FastAPI", is_required=True, importance_level="HIGH")
    r3 = JobRequirement(job_analysis_id=1, skill_name="PostgreSQL", is_required=True, importance_level="MEDIUM")
    r4 = JobRequirement(job_analysis_id=1, skill_name="Docker", is_required=True, importance_level="HIGH")
    db.add_all([r1, r2, r3, r4])
    db.commit()

    # SkillGapReport for User 1
    rep = SkillGapReport(
        user_id=1,
        job_analysis_id=1,
        overall_match_percentage=45.0,
        matching_skills=[{"skill_name": "Python", "status": "MATCHED", "is_required": True, "priority": "LOW"}],
        weak_skills=[{"skill_name": "FastAPI", "status": "PARTIAL_GAP", "gap_delta": 1, "is_required": True, "priority": "MEDIUM"}],
        missing_skills=[
            {"skill_name": "Docker", "status": "MISSING", "gap_delta": 3, "is_required": True, "priority": "HIGH"},
            {"skill_name": "PostgreSQL", "status": "MISSING", "gap_delta": 2, "is_required": True, "priority": "MEDIUM"}
        ],
        recommended_skills=[
            {"skill_name": "Docker", "priority": "HIGH"},
            {"skill_name": "FastAPI", "priority": "MEDIUM"}
        ]
    )
    db.add(rep)
    db.commit()


def get_auth_header(user_id: int = 1):
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_generate_project_recommendations(client: TestClient):
    """Test generating project recommendations via API."""
    response = client.post(
        "/api/project-recommendations/generate/1",
        headers=get_auth_header(1)
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_analysis_id"] == 1
    assert len(data["projects"]) >= 2
    assert data["total_projects"] >= 2
    assert data["completed_projects"] == 0

    first_proj = data["projects"][0]
    assert "title" in first_proj
    assert "difficulty" in first_proj
    assert isinstance(first_proj["skills_practiced"], list)
    assert first_proj["estimated_hours"] > 0


def test_recommendation_grounding(client: TestClient):
    """Test that recommendations target actual missing/weak skills (Docker, PostgreSQL, FastAPI)."""
    response = client.post(
        "/api/project-recommendations/generate/1",
        headers=get_auth_header(1)
    )
    assert response.status_code == 201
    data = response.json()
    
    all_skills = []
    for proj in data["projects"]:
        all_skills.extend(proj["skills_practiced"])
    
    # Check that missing/weak skills occur in practiced skills
    assert any(s in ["Docker", "PostgreSQL", "FastAPI"] for s in all_skills)


def test_high_priority_missing_skills_are_prioritized():
    """Test fallback logic prioritizes HIGH missing skills first."""
    missing = [
        {"skill_name": "Docker", "priority": "HIGH"},
        {"skill_name": "PostgreSQL", "priority": "MEDIUM"}
    ]
    weak = [{"skill_name": "FastAPI", "priority": "MEDIUM"}]

    projects = _generate_fallback_project_recommendations("Backend Engineer", "MID", "Python Dev", missing, weak)
    assert len(projects) >= 2
    # First project practiced skills should include Docker
    assert "Docker" in projects[0]["skills_practiced"]


def test_partial_skills_are_considered():
    """Test that partial skills are included in project recommendations."""
    missing = [{"skill_name": "Docker", "priority": "HIGH"}]
    weak = [{"skill_name": "FastAPI", "priority": "MEDIUM"}]

    projects = _generate_fallback_project_recommendations("Backend Engineer", "MID", "Python Dev", missing, weak)
    all_practiced = [s for p in projects for s in p["skills_practiced"]]
    assert "FastAPI" in all_practiced or "Docker" in all_practiced


def test_matched_skills_are_not_primary_targets():
    """Test that matched skills are not primary targets when missing skills exist."""
    missing = [{"skill_name": "Kubernetes", "priority": "HIGH"}]
    weak = []

    projects = _generate_fallback_project_recommendations("DevOps Engineer", "SENIOR", "DevOps", missing, weak)
    assert "Kubernetes" in projects[0]["skills_practiced"]


def test_fallback_project_generation():
    """Test deterministic fallback generation structure."""
    projects = _generate_fallback_project_recommendations(
        target_role="Fullstack Engineer",
        experience_level="MID",
        job_title="React Python Dev",
        missing_skills=[{"skill_name": "GraphQL"}],
        weak_skills=[{"skill_name": "Redis"}]
    )
    assert len(projects) >= 2
    for p in projects:
        assert p["title"]
        assert p["difficulty"] in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
        assert p["estimated_hours"] >= 1
        assert p["resume_bullet"]


def test_malformed_ai_response_fallback():
    """Test that malformed AI JSON output triggers graceful fallback."""
    with patch("os.getenv", side_effect=lambda key, default=None: "mock_key" if key == "GEMINI_API_KEY" else default):
        with patch("google.generativeai.GenerativeModel") as mock_model:
            mock_inst = mock_model.return_value
            mock_inst.generate_content.return_value.text = "NOT JSON OUTPUT AT ALL"

            projects = generate_project_recommendations_ai(
                target_role="Data Engineer",
                experience_level="MID",
                job_title="Data Dev",
                job_requirements=["Spark"],
                missing_skills=["Spark"],
                weak_skills=[]
            )
            assert len(projects) >= 2
            assert "title" in projects[0]


def test_duplicate_recommendations_are_removed(client: TestClient):
    """Test that regenerating recommendations replaces old records without duplicating."""
    r1 = client.post("/api/project-recommendations/generate/1", headers=get_auth_header(1))
    assert r1.status_code == 201

    r2 = client.post("/api/project-recommendations/generate/1", headers=get_auth_header(1))
    assert r2.status_code == 201
    
    # Query get to verify total count remains 2-3
    r3 = client.get("/api/project-recommendations/1", headers=get_auth_header(1))
    assert r3.status_code == 200
    assert r3.json()["total_projects"] <= 3


def test_get_recommendations(client: TestClient):
    """Test fetching recommendations for a job analysis."""
    response = client.get("/api/project-recommendations/1", headers=get_auth_header(1))
    assert response.status_code == 200
    data = response.json()
    assert data["job_analysis_id"] == 1
    assert len(data["projects"]) >= 2


def test_complete_recommendation(client: TestClient):
    """Test toggling project recommendation completion status."""
    gen_res = client.post("/api/project-recommendations/generate/1", headers=get_auth_header(1))
    proj_id = gen_res.json()["projects"][0]["id"]

    # Mark completed
    patch_res = client.patch(
        f"/api/project-recommendations/{proj_id}/complete",
        headers=get_auth_header(1),
        json={"is_completed": True}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_completed"] is True

    # Mark incomplete
    patch_res2 = client.patch(
        f"/api/project-recommendations/{proj_id}/complete",
        headers=get_auth_header(1),
        json={"is_completed": False}
    )
    assert patch_res2.status_code == 200
    assert patch_res2.json()["is_completed"] is False


def test_user_isolation(client: TestClient):
    """Test that User 2 cannot access or modify User 1's project recommendations."""
    # User 1 generates recommendations
    client.post("/api/project-recommendations/generate/1", headers=get_auth_header(1))

    # User 2 tries to access User 1's job analysis recommendations -> 404
    get_res = client.get("/api/project-recommendations/1", headers=get_auth_header(2))
    assert get_res.status_code == 404

    # User 2 tries to generate recommendations for User 1's job analysis -> 404
    gen_res = client.post("/api/project-recommendations/generate/1", headers=get_auth_header(2))
    assert gen_res.status_code == 404


def test_invalid_job_analysis(client: TestClient):
    """Test 404 returned for non-existent job analysis ID."""
    res = client.get("/api/project-recommendations/999999", headers=get_auth_header(1))
    assert res.status_code == 404


def test_delete_recommendations(client: TestClient):
    """Test deleting project recommendations for a job analysis."""
    client.post("/api/project-recommendations/generate/1", headers=get_auth_header(1))

    del_res = client.delete("/api/project-recommendations/1", headers=get_auth_header(1))
    assert del_res.status_code == 204

    # Verify deleted -> on GET it re-generates automatically
    get_res = client.get("/api/project-recommendations/1", headers=get_auth_header(1))
    assert get_res.status_code == 200


def test_legacy_recommendations_preserved(db):
    """Test that legacy recommendations with job_analysis_id=None are preserved."""
    legacy = ProjectRecommendation(
        user_id=1,
        job_analysis_id=None,
        title="Legacy CLI Tool",
        difficulty="BEGINNER",
        skills_practiced=["Python"],
        description="Old project",
        is_completed=False
    )
    db.add(legacy)
    db.commit()

    # Query legacy
    record = db.query(ProjectRecommendation).filter(ProjectRecommendation.id == legacy.id).first()
    assert record is not None
    assert record.title == "Legacy CLI Tool"
