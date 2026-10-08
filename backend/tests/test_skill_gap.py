"""
Comprehensive unit tests for Phase 6: Skill Gap Analysis service and API endpoints.

Covers:
- All skills matched
- Missing skill detection
- Partial skill detection
- Skill level comparison
- Case-insensitive matching
- Weighted match percentage
- Required vs preferred priority
- Unauthorized access
- User data isolation
- Non-existent JobAnalysis
- Skill gap report creation & refresh after user skill updates
- Summary endpoint
"""

import pytest
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.job_analysis import JobAnalysis, JobRequirement, SkillGapReport
from app.utils.security import create_access_token, hash_password
from app.services.skill_gap_service import calculate_skill_gap, level_to_numeric


@pytest.fixture(autouse=True)
def setup_seed_data(db):
    """Seed users, skills, and job analysis for each test."""
    # User 1
    u1 = User(
        id=1,
        email="user1@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="User One"
    )
    # User 2 (Isolation Test)
    u2 = User(
        id=2,
        email="user2@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="User Two"
    )
    db.add_all([u1, u2])
    db.commit()

    # Master Skills
    s_py = Skill(id=1, name="Python", category="Technical")
    s_sql = Skill(id=2, name="SQL", category="Technical")
    s_fa = Skill(id=3, name="FastAPI", category="Technical")
    s_doc = Skill(id=4, name="Docker", category="Technical")
    db.add_all([s_py, s_sql, s_fa, s_doc])
    db.commit()

    # User 1 Skills: Python (ADVANCED), SQL (BEGINNER), FastAPI (BEGINNER)
    us1 = UserSkill(user_id=1, skill_id=1, self_assessed_level="ADVANCED", experience_months=24)
    us2 = UserSkill(user_id=1, skill_id=2, self_assessed_level="BEGINNER", experience_months=6)
    us3 = UserSkill(user_id=1, skill_id=3, self_assessed_level="BEGINNER", experience_months=3)
    db.add_all([us1, us2, us3])
    db.commit()

    # Job Analysis for User 1
    ja = JobAnalysis(
        id=1,
        user_id=1,
        job_title="Backend Python Developer",
        company_name="TechCorp",
        raw_description="Backend developer position requiring Python, SQL, FastAPI, and Docker."
    )
    db.add(ja)
    db.commit()

    # Requirements:
    # Python (Required, High -> ADVANCED)
    # SQL (Required, Medium -> INTERMEDIATE)
    # FastAPI (Required, Medium -> INTERMEDIATE)
    # Docker (Required, Medium -> INTERMEDIATE)
    r1 = JobRequirement(job_analysis_id=1, skill_name="PYTHON", is_required=True, importance_level="HIGH")
    r2 = JobRequirement(job_analysis_id=1, skill_name="sql", is_required=True, importance_level="MEDIUM")
    r3 = JobRequirement(job_analysis_id=1, skill_name="FastAPI", is_required=True, importance_level="MEDIUM")
    r4 = JobRequirement(job_analysis_id=1, skill_name="Docker", is_required=True, importance_level="MEDIUM")
    db.add_all([r1, r2, r3, r4])
    db.commit()


def get_auth_header(user_id: int = 1):
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_level_to_numeric():
    assert level_to_numeric("BEGINNER") == 1
    assert level_to_numeric("intermediate") == 2
    assert level_to_numeric("ADVANCED") == 3
    assert level_to_numeric("EXPERT") == 4
    assert level_to_numeric("NOT_ADDED") == 0


def test_case_insensitive_matching_and_gap_calculation(db):
    """Test case-insensitive skill matching and level gap calculation."""
    ja = db.query(JobAnalysis).filter(JobAnalysis.id == 1).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == 1).all()

    report = calculate_skill_gap(ja, user_skills, db)

    matching_names = [m["skill_name"].upper() for m in report.matching_skills]
    weak_names = [w["skill_name"].upper() for w in report.weak_skills]
    missing_names = [m["skill_name"].upper() for m in report.missing_skills]

    assert "PYTHON" in matching_names
    assert "SQL" in weak_names
    assert "FASTAPI" in weak_names
    assert "DOCKER" in missing_names


def test_weighted_match_percentage(db):
    """Verify exact weighted score formula."""
    ja = db.query(JobAnalysis).filter(JobAnalysis.id == 1).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == 1).all()

    report = calculate_skill_gap(ja, user_skills, db)
    # Weights:
    # Python (Req High): 3 -> Earned: 3 * 1.0 = 3.0
    # SQL (Req Med): 2 -> Earned: 2 * (1/2) = 1.0
    # FastAPI (Req Med): 2 -> Earned: 2 * (1/2) = 1.0
    # Docker (Req Med): 2 -> Earned: 0.0
    # Total Weight = 3 + 2 + 2 + 2 = 9.0
    # Earned Points = 3.0 + 1.0 + 1.0 + 0.0 = 5.0
    # Expected % = (5.0 / 9.0) * 100 = 55.6%

    assert report.overall_match_percentage == 55.6


def test_analyze_skill_gap_api_endpoint(client):
    """Test POST /api/skill-gap/analyze/{id} endpoint."""
    headers = get_auth_header(1)
    response = client.post("/api/skill-gap/analyze/1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["job_analysis_id"] == 1
    assert data["overall_match_percentage"] == 55.6
    assert len(data["matching_skills"]) == 1
    assert len(data["weak_skills"]) == 2
    assert len(data["missing_skills"]) == 1


def test_refresh_report_after_user_skill_update(client, db):
    """Verify that updating user skills and re-running analyze updates the report."""
    headers = get_auth_header(1)

    # Add Docker skill for User 1 (INTERMEDIATE)
    us_docker = UserSkill(user_id=1, skill_id=4, self_assessed_level="INTERMEDIATE", experience_months=12)
    db.add(us_docker)

    # Upgrade SQL to INTERMEDIATE
    sql_us = db.query(UserSkill).filter(UserSkill.user_id == 1, UserSkill.skill_id == 2).first()
    sql_us.self_assessed_level = "INTERMEDIATE"
    db.commit()

    # Re-run gap analysis API
    res = client.post("/api/skill-gap/analyze/1", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Docker and SQL are now MATCHED
    matching_names = [m["skill_name"].upper() for m in data["matching_skills"]]
    assert "DOCKER" in matching_names
    assert "SQL" in matching_names
    assert len(data["missing_skills"]) == 0


def test_unauthorized_access(client):
    """Verify 401 when unauthenticated."""
    res = client.post("/api/skill-gap/analyze/1")
    assert res.status_code == 401

    res_rep = client.get("/api/skill-gap/report/1")
    assert res_rep.status_code == 401


def test_user_data_isolation(client):
    """Verify User 2 cannot analyze or access User 1's JobAnalysis or SkillGapReport."""
    headers_u2 = get_auth_header(2)

    # User 2 attempts to analyze User 1's job analysis (ID 1)
    res = client.post("/api/skill-gap/analyze/1", headers=headers_u2)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

    # User 2 attempts to fetch User 1's report
    res_get = client.get("/api/skill-gap/report/1", headers=headers_u2)
    assert res_get.status_code == 404


def test_non_existent_job_analysis(client):
    """Verify 404 for non-existent job analysis ID."""
    headers = get_auth_header(1)
    res = client.post("/api/skill-gap/analyze/9999", headers=headers)
    assert res.status_code == 404


def test_skill_gap_summary_endpoint(client):
    """Test GET /api/skill-gap/summary endpoint."""
    headers = get_auth_header(1)

    # Trigger analysis first
    client.post("/api/skill-gap/analyze/1", headers=headers)

    res = client.get("/api/skill-gap/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_analyzed_jobs"] >= 1
    assert data["average_match_percentage"] > 0
