"""
Phase 10: Comprehensive Test Suite for Career Readiness Score & Advanced Dashboard.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.job_analysis import JobAnalysis, JobRequirement, SkillGapReport
from app.models.roadmap import Roadmap, RoadmapItem
from app.models.interview import InterviewSession
from app.models.project import ProjectRecommendation
from app.utils.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def setup_seed_data(db):
    """Seed test users and basic data."""
    u1 = User(
        id=1,
        email="readiness_user1@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Readiness User One"
    )
    u2 = User(
        id=2,
        email="readiness_user2@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Readiness User Two"
    )
    db.add_all([u1, u2])
    db.commit()


def get_auth_header(user_id: int = 1):
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_readiness_new_user_no_job(client: TestClient):
    """Test response when authenticated user has no analyzed jobs."""
    res = client.get("/api/career-readiness", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["has_target_job"] is False
    assert data["overall_score"] == 0.0
    assert data["job_analysis_id"] is None
    assert data["tier"] == "GETTING STARTED / HIGH GAPS"
    assert data["pillars"]["skill_readiness"]["score"] == 0.0
    assert data["pillars"]["roadmap_progress"]["score"] == 0.0
    assert data["pillars"]["interview_readiness"]["score"] == 0.0
    assert data["pillars"]["portfolio_readiness"]["score"] == 0.0


def test_readiness_target_roles_list(client: TestClient, db):
    """Test retrieving analyzed target jobs list for dropdown."""
    ja1 = JobAnalysis(id=10, user_id=1, job_title="Backend Engineer", role_category="Backend", raw_description="Backend desc")
    ja2 = JobAnalysis(id=11, user_id=1, job_title="DevOps Specialist", role_category="DevOps", raw_description="DevOps desc")
    ja_u2 = JobAnalysis(id=12, user_id=2, job_title="Frontend Developer", role_category="Frontend", raw_description="Frontend desc")
    db.add_all([ja1, ja2, ja_u2])
    db.commit()

    res = client.get("/api/career-readiness/target-roles", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    ids = [d["id"] for d in data]
    assert 10 in ids and 11 in ids
    assert 12 not in ids  # User isolation


def test_readiness_complete_user(client: TestClient, db):
    """Test perfect score user with 100% across all 4 pillars."""
    ja = JobAnalysis(id=1, user_id=1, job_title="Senior Python Architect", role_category="Backend Engineering", raw_description="Python required")
    db.add(ja)
    db.commit()

    # Pillar 1: SkillGap (100%)
    rep = SkillGapReport(
        user_id=1,
        job_analysis_id=1,
        overall_match_percentage=100.0,
        matching_skills=[{"skill_name": "Python"}],
        missing_skills=[],
        weak_skills=[]
    )
    db.add(rep)

    # Pillar 2: Roadmap (100% completed)
    rm = Roadmap(id=1, user_id=1, job_analysis_id=1, title="Mastery Plan", target_role="Backend", total_weeks=2)
    db.add(rm)
    db.commit()
    it1 = RoadmapItem(roadmap_id=1, week_number=1, topic="P1", is_completed=True)
    it2 = RoadmapItem(roadmap_id=1, week_number=2, topic="P2", is_completed=True)
    db.add_all([it1, it2])

    # Pillar 3: Interview (100 score)
    iv = InterviewSession(
        id=1,
        user_id=1,
        job_analysis_id=1,
        target_role="Backend",
        topic="Python Mastery",
        difficulty="ADVANCED",
        status="COMPLETED",
        overall_score=100.0
    )
    db.add(iv)

    # Pillar 4: Projects (100% completed)
    pj1 = ProjectRecommendation(
        user_id=1,
        job_analysis_id=1,
        title="API Gateway",
        difficulty="ADVANCED",
        skills_practiced=["Python"],
        is_completed=True
    )
    db.add(pj1)
    db.commit()

    res = client.get("/api/career-readiness/1", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["overall_score"] == 100.0
    assert data["tier"] == "JOB READY / STRONG CANDIDATE"
    assert data["pillars"]["skill_readiness"]["score"] == 100.0
    assert data["pillars"]["roadmap_progress"]["score"] == 100.0
    assert data["pillars"]["interview_readiness"]["score"] == 100.0
    assert data["pillars"]["portfolio_readiness"]["score"] == 100.0


def test_readiness_job_no_roadmap(client: TestClient, db):
    """Test readiness when JobAnalysis exists but no roadmap has been generated."""
    ja = JobAnalysis(id=2, user_id=1, job_title="Data Scientist", raw_description="Python, Pandas")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=2, overall_match_percentage=60.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)
    db.commit()

    res = client.get("/api/career-readiness/2", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["pillars"]["skill_readiness"]["score"] == 60.0
    assert data["pillars"]["roadmap_progress"]["score"] == 0.0
    assert data["pillars"]["roadmap_progress"]["status"] == "NOT_STARTED"


def test_readiness_job_no_interviews(client: TestClient, db):
    """Test readiness with no interviews completed."""
    ja = JobAnalysis(id=3, user_id=1, job_title="Cloud Engineer", raw_description="AWS, Terraform")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=3, overall_match_percentage=50.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)
    db.commit()

    res = client.get("/api/career-readiness/3", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["pillars"]["interview_readiness"]["score"] == 0.0
    assert data["pillars"]["interview_readiness"]["status"] == "NOT_STARTED"


def test_readiness_job_no_projects(client: TestClient, db):
    """Test readiness with no project recommendations generated."""
    ja = JobAnalysis(id=4, user_id=1, job_title="React Dev", raw_description="React, TS")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=4, overall_match_percentage=70.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)
    db.commit()

    res = client.get("/api/career-readiness/4", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["pillars"]["portfolio_readiness"]["score"] == 0.0
    assert data["pillars"]["portfolio_readiness"]["status"] == "NOT_STARTED"


def test_readiness_partial_roadmap(client: TestClient, db):
    """Test partial roadmap calculation (2 out of 4 completed = 50%)."""
    ja = JobAnalysis(id=5, user_id=1, job_title="Fullstack Engineer", raw_description="Fullstack")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=5, overall_match_percentage=80.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)

    rm = Roadmap(id=5, user_id=1, job_analysis_id=5, title="FS Roadmap", target_role="FS", total_weeks=4)
    db.add(rm)
    db.commit()

    it1 = RoadmapItem(roadmap_id=5, week_number=1, topic="W1", is_completed=True)
    it2 = RoadmapItem(roadmap_id=5, week_number=2, topic="W2", is_completed=True)
    it3 = RoadmapItem(roadmap_id=5, week_number=3, topic="W3", is_completed=False)
    it4 = RoadmapItem(roadmap_id=5, week_number=4, topic="W4", is_completed=False)
    db.add_all([it1, it2, it3, it4])
    db.commit()

    res = client.get("/api/career-readiness/5", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["pillars"]["roadmap_progress"]["score"] == 50.0
    assert data["pillars"]["roadmap_progress"]["status"] == "IN_PROGRESS"
    assert data["pillars"]["roadmap_progress"]["details"]["completed_items"] == 2
    assert data["pillars"]["roadmap_progress"]["details"]["total_items"] == 4


def test_readiness_partial_interviews(client: TestClient, db):
    """Test interview average calculation across multiple completed sessions."""
    ja = JobAnalysis(id=6, user_id=1, job_title="SecOps Engineer", raw_description="Security")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=6, overall_match_percentage=80.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)

    # Completed interview 1: score 70, Completed interview 2: score 90 -> avg = 80
    iv1 = InterviewSession(
        id=61,
        user_id=1,
        job_analysis_id=6,
        target_role="SecOps",
        topic="Security Assessment",
        difficulty="INTERMEDIATE",
        status="COMPLETED",
        overall_score=70.0
    )
    iv2 = InterviewSession(
        id=62,
        user_id=1,
        job_analysis_id=6,
        target_role="SecOps",
        topic="Network Security",
        difficulty="ADVANCED",
        status="COMPLETED",
        overall_score=90.0
    )
    db.add_all([iv1, iv2])
    db.commit()

    res = client.get("/api/career-readiness/6", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["pillars"]["interview_readiness"]["score"] == 80.0
    assert data["pillars"]["interview_readiness"]["status"] == "IN_PROGRESS"


def test_readiness_ignores_in_progress_interviews(client: TestClient, db):
    """Test that IN_PROGRESS or abandoned interviews without overall_score are excluded."""
    ja = JobAnalysis(id=7, user_id=1, job_title="QA Engineer", raw_description="QA")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=7, overall_match_percentage=80.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)

    # 1 completed with 80, 1 in-progress with None score
    iv1 = InterviewSession(
        id=71,
        user_id=1,
        job_analysis_id=7,
        target_role="QA",
        topic="Automation",
        difficulty="INTERMEDIATE",
        status="COMPLETED",
        overall_score=80.0
    )
    iv2 = InterviewSession(
        id=72,
        user_id=1,
        job_analysis_id=7,
        target_role="QA",
        topic="Performance",
        difficulty="INTERMEDIATE",
        status="IN_PROGRESS",
        overall_score=None
    )
    db.add_all([iv1, iv2])
    db.commit()

    res = client.get("/api/career-readiness/7", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["pillars"]["interview_readiness"]["score"] == 80.0
    assert data["pillars"]["interview_readiness"]["details"]["completed_sessions"] == 1


def test_readiness_completed_projects(client: TestClient, db):
    """Test portfolio calculation when 1 of 2 projects is completed (50%)."""
    ja = JobAnalysis(id=8, user_id=1, job_title="Mobile Dev", raw_description="Flutter")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=8, overall_match_percentage=80.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)

    pj1 = ProjectRecommendation(user_id=1, job_analysis_id=8, title="App 1", difficulty="INTERMEDIATE", skills_practiced=["Flutter"], is_completed=True)
    pj2 = ProjectRecommendation(user_id=1, job_analysis_id=8, title="App 2", difficulty="ADVANCED", skills_practiced=["Dart"], is_completed=False)
    db.add_all([pj1, pj2])
    db.commit()

    res = client.get("/api/career-readiness/8", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["pillars"]["portfolio_readiness"]["score"] == 50.0
    assert data["pillars"]["portfolio_readiness"]["status"] == "IN_PROGRESS"


def test_readiness_score_formula_accuracy(client: TestClient, db):
    """
    Test exact weighted formula:
    Skill: 80 * 0.35 = 28.0
    Roadmap: 60 * 0.25 = 15.0
    Interview: 70 * 0.25 = 17.5
    Project: 100 * 0.15 = 15.0
    Total: 28.0 + 15.0 + 17.5 + 15.0 = 75.5
    """
    ja = JobAnalysis(id=9, user_id=1, job_title="Fullstack", raw_description="Fullstack")
    db.add(ja)
    rep = SkillGapReport(user_id=1, job_analysis_id=9, overall_match_percentage=80.0, matching_skills=[], missing_skills=[], weak_skills=[])
    db.add(rep)

    # Roadmap 3/5 completed = 60%
    rm = Roadmap(id=9, user_id=1, job_analysis_id=9, title="R9", target_role="FS", total_weeks=5)
    db.add(rm)
    db.commit()
    for i in range(1, 6):
        db.add(RoadmapItem(roadmap_id=9, week_number=i, topic=f"T{i}", is_completed=(i <= 3)))

    # Interview: 70
    db.add(InterviewSession(
        id=91,
        user_id=1,
        job_analysis_id=9,
        target_role="FS",
        topic="FS Interview",
        difficulty="INTERMEDIATE",
        status="COMPLETED",
        overall_score=70.0
    ))

    # Projects: 2/2 = 100%
    db.add(ProjectRecommendation(user_id=1, job_analysis_id=9, title="P1", difficulty="MID", skills_practiced=[], is_completed=True))
    db.add(ProjectRecommendation(user_id=1, job_analysis_id=9, title="P2", difficulty="MID", skills_practiced=[], is_completed=True))
    db.commit()

    res = client.get("/api/career-readiness/9", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert data["overall_score"] == 75.5
    assert data["tier"] == "COMPETITIVE / MINOR GAPS"


def test_readiness_tier_classification(client: TestClient, db):
    """Test tier classification for 85+ score (Job Ready)."""
    ja = JobAnalysis(id=20, user_id=1, job_title="Tier Test", raw_description="Tier")
    db.add(ja)
    db.add(SkillGapReport(user_id=1, job_analysis_id=20, overall_match_percentage=85.0, matching_skills=[], missing_skills=[], weak_skills=[]))
    db.commit()

    # Roadmap 100%
    rm = Roadmap(id=20, user_id=1, job_analysis_id=20, title="R20", target_role="Tier", total_weeks=1)
    db.add(rm)
    db.commit()
    db.add(RoadmapItem(roadmap_id=20, week_number=1, topic="T1", is_completed=True))

    # Interview 85
    db.add(InterviewSession(
        id=201,
        user_id=1,
        job_analysis_id=20,
        target_role="Tier",
        topic="Tier Topic",
        difficulty="ADVANCED",
        status="COMPLETED",
        overall_score=85.0
    ))
    # Project 100%
    db.add(ProjectRecommendation(user_id=1, job_analysis_id=20, title="P1", difficulty="MID", skills_practiced=[], is_completed=True))
    db.commit()

    res = client.get("/api/career-readiness/20", headers=get_auth_header(1))
    assert res.status_code == 200
    assert res.json()["tier"] == "JOB READY / STRONG CANDIDATE"


def test_readiness_job_specific_filtering(client: TestClient, db):
    """Test that two separate jobs for the same user calculate independently without data bleeding."""
    ja1 = JobAnalysis(id=30, user_id=1, job_title="Job A", raw_description="A")
    ja2 = JobAnalysis(id=31, user_id=1, job_title="Job B", raw_description="B")
    db.add_all([ja1, ja2])
    db.add(SkillGapReport(user_id=1, job_analysis_id=30, overall_match_percentage=100.0, matching_skills=[], missing_skills=[], weak_skills=[]))
    db.add(SkillGapReport(user_id=1, job_analysis_id=31, overall_match_percentage=20.0, matching_skills=[], missing_skills=[], weak_skills=[]))
    db.commit()

    res_a = client.get("/api/career-readiness/30", headers=get_auth_header(1))
    res_b = client.get("/api/career-readiness/31", headers=get_auth_header(1))

    assert res_a.json()["pillars"]["skill_readiness"]["score"] == 100.0
    assert res_b.json()["pillars"]["skill_readiness"]["score"] == 20.0


def test_readiness_user_isolation(client: TestClient, db):
    """Test that User 2 cannot access User 1's career readiness score."""
    ja = JobAnalysis(id=40, user_id=1, job_title="Secret Job", raw_description="Secret")
    db.add(ja)
    db.commit()

    res = client.get("/api/career-readiness/40", headers=get_auth_header(2))
    assert res.status_code == 404


def test_readiness_invalid_job_id(client: TestClient):
    """Test 404 for non-existent job ID."""
    res = client.get("/api/career-readiness/999999", headers=get_auth_header(1))
    assert res.status_code == 404


def test_readiness_score_boundary_zero(client: TestClient, db):
    """Test score clamped correctly at 0.0."""
    ja = JobAnalysis(id=50, user_id=1, job_title="Zero Job", raw_description="Zero")
    db.add(ja)
    db.add(SkillGapReport(user_id=1, job_analysis_id=50, overall_match_percentage=0.0, matching_skills=[], missing_skills=[], weak_skills=[]))
    db.commit()

    res = client.get("/api/career-readiness/50", headers=get_auth_header(1))
    assert res.status_code == 200
    assert res.json()["overall_score"] == 0.0


def test_readiness_score_boundary_hundred(client: TestClient, db):
    """Test score clamped correctly at 100.0."""
    ja = JobAnalysis(id=60, user_id=1, job_title="Max Job", raw_description="Max")
    db.add(ja)
    db.add(SkillGapReport(user_id=1, job_analysis_id=60, overall_match_percentage=100.0, matching_skills=[], missing_skills=[], weak_skills=[]))
    rm = Roadmap(id=60, user_id=1, job_analysis_id=60, title="R60", target_role="Max", total_weeks=1)
    db.add(rm)
    db.commit()
    db.add(RoadmapItem(roadmap_id=60, week_number=1, topic="T1", is_completed=True))
    db.add(InterviewSession(
        id=601,
        user_id=1,
        job_analysis_id=60,
        target_role="Max",
        topic="Max Topic",
        difficulty="ADVANCED",
        status="COMPLETED",
        overall_score=100.0
    ))
    db.add(ProjectRecommendation(user_id=1, job_analysis_id=60, title="P1", difficulty="MID", skills_practiced=[], is_completed=True))
    db.commit()

    res = client.get("/api/career-readiness/60", headers=get_auth_header(1))
    assert res.status_code == 200
    assert res.json()["overall_score"] == 100.0


def test_readiness_next_best_action_generation(client: TestClient, db):
    """Test dynamic Next Best Action reflects actual prioritized gap (missing high priority skill)."""
    ja = JobAnalysis(id=70, user_id=1, job_title="Golang Dev", raw_description="Go, K8s")
    db.add(ja)
    rep = SkillGapReport(
        user_id=1,
        job_analysis_id=70,
        overall_match_percentage=40.0,
        matching_skills=[],
        weak_skills=[],
        missing_skills=[{"skill_name": "Kubernetes", "priority": "HIGH"}]
    )
    db.add(rep)
    db.commit()

    res = client.get("/api/career-readiness/70", headers=get_auth_header(1))
    assert res.status_code == 200
    data = res.json()
    assert "Kubernetes" in data["next_best_action"]["action_text"]
    assert data["next_best_action"]["action_type"] == "SKILL"
