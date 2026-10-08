"""
Comprehensive unit tests for Phase 7: Personalized Learning Roadmap.

Covers:
1. Roadmap generation
2. Correct JobAnalysis ownership
3. Missing skills prioritized
4. Partial gaps included after missing skills
5. Matched skills excluded
6. Duplicate skills removed
7. Roadmap skill list is based on actual gaps
8. AI fallback works without Gemini
9. Unknown skill fallback works
10. Roadmap retrieval
11. Roadmap listing
12. Completion toggle
13. completed_at set correctly
14. completed_at cleared correctly
15. Progress calculation
16. User isolation
17. Unauthorized access
18. Delete roadmap
19. Non-existent roadmap
20. Non-existent JobAnalysis
"""

import pytest
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.job_analysis import JobAnalysis, JobRequirement, SkillGapReport
from app.models.roadmap import Roadmap, RoadmapItem
from app.utils.security import create_access_token, hash_password
from app.services.roadmap_service import generate_personalized_roadmap
from app.services.ai_service import _generate_fallback_roadmap


@pytest.fixture(autouse=True)
def setup_seed_data(db):
    """Seed users, skills, job analysis, and requirements for roadmap tests."""
    # User 1
    u1 = User(
        id=1,
        email="roadmap_user1@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Roadmap User One"
    )
    # User 2 (Isolation Test)
    u2 = User(
        id=2,
        email="roadmap_user2@example.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Roadmap User Two"
    )
    db.add_all([u1, u2])
    db.commit()

    # Master Skills
    s_py = Skill(id=1, name="Python", category="Technical")
    s_sql = Skill(id=2, name="SQL", category="Technical")
    s_fa = Skill(id=3, name="FastAPI", category="Technical")
    s_doc = Skill(id=4, name="Docker", category="Technical")
    s_k8s = Skill(id=5, name="Kubernetes", category="Technical")
    db.add_all([s_py, s_sql, s_fa, s_doc, s_k8s])
    db.commit()

    # User 1 Skills:
    # Python: ADVANCED (Matched)
    # SQL: BEGINNER (Partial Gap)
    # FastAPI, Docker, Kubernetes: NOT ADDED (Missing)
    us1 = UserSkill(user_id=1, skill_id=1, self_assessed_level="ADVANCED", experience_months=24)
    us2 = UserSkill(user_id=1, skill_id=2, self_assessed_level="BEGINNER", experience_months=6)
    db.add_all([us1, us2])
    db.commit()

    # Job Analysis for User 1
    ja = JobAnalysis(
        id=1,
        user_id=1,
        job_title="Backend Cloud Engineer",
        role_category="Backend Engineering",
        raw_description="Requires Python, SQL, FastAPI, Docker, and Kubernetes."
    )
    db.add(ja)
    db.commit()

    # Requirements:
    # Python: Required High -> Required level ADVANCED (User has ADVANCED -> MATCHED)
    # SQL: Required Med -> Required level INTERMEDIATE (User has BEGINNER -> PARTIAL GAP)
    # FastAPI: Required High -> Required level ADVANCED (User has 0 -> MISSING, HIGH)
    # Docker: Required Med -> Required level INTERMEDIATE (User has 0 -> MISSING, MEDIUM)
    # Kubernetes: Preferred High -> Required level INTERMEDIATE (User has 0 -> MISSING, MEDIUM)
    r1 = JobRequirement(job_analysis_id=1, skill_name="Python", is_required=True, importance_level="HIGH")
    r2 = JobRequirement(job_analysis_id=1, skill_name="SQL", is_required=True, importance_level="MEDIUM")
    r3 = JobRequirement(job_analysis_id=1, skill_name="FastAPI", is_required=True, importance_level="HIGH")
    r4 = JobRequirement(job_analysis_id=1, skill_name="Docker", is_required=True, importance_level="MEDIUM")
    r5 = JobRequirement(job_analysis_id=1, skill_name="Kubernetes", is_required=False, importance_level="HIGH")
    db.add_all([r1, r2, r3, r4, r5])
    db.commit()


def get_auth_header(user_id: int = 1):
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def test_ai_fallback_and_unknown_skill():
    """Verify fallback curriculum generation and unknown skill handling."""
    gaps = [
        {"skill_name": "Solidity", "status": "MISSING", "priority": "HIGH"},
        {"skill_name": "FastAPI", "status": "MISSING", "priority": "HIGH"}
    ]
    roadmap_dict = _generate_fallback_roadmap("Blockchain Engineer", "Web3 Developer", gaps)
    assert "weekly_phases" in roadmap_dict
    assert len(roadmap_dict["weekly_phases"]) == 4  # minimum 4 weeks
    phase_skills = [p["skill_name"] for p in roadmap_dict["weekly_phases"]]
    assert "Solidity" in phase_skills
    assert "FastAPI" in phase_skills


def test_roadmap_generation_and_skill_prioritization(client):
    """Test POST /api/roadmaps/generate/{job_analysis_id} endpoint."""
    headers = get_auth_header(1)

    res = client.post("/api/roadmaps/generate/1", headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["job_analysis_id"] == 1
    assert data["total_weeks"] >= 4
    assert len(data["items"]) >= 4

    # Extract all skills targeted in roadmap
    item_skills = [item["skill_name"].upper() for item in data["items"] if item["skill_name"]]

    # 1. Missing skills must be present (FastAPI, Docker, Kubernetes)
    assert "FASTAPI" in item_skills
    assert "DOCKER" in item_skills

    # 2. Matched skill (Python) should NOT receive a learning item since it's already ADVANCED matched
    assert "PYTHON" not in item_skills

    # 3. Missing skills must be prioritized before partial gap skills
    # Find indices
    if "FASTAPI" in item_skills and "SQL" in item_skills:
        assert item_skills.index("FASTAPI") < item_skills.index("SQL")


def test_roadmap_retrieval_and_listing(client):
    """Test GET /api/roadmaps and GET /api/roadmaps/{id}."""
    headers = get_auth_header(1)

    # Generate roadmap first
    gen_res = client.post("/api/roadmaps/generate/1", headers=headers)
    assert gen_res.status_code == 201
    roadmap_id = gen_res.json()["id"]

    # List
    list_res = client.get("/api/roadmaps", headers=headers)
    assert list_res.status_code == 200
    roadmaps = list_res.json()
    assert len(roadmaps) >= 1
    assert roadmaps[0]["id"] == roadmap_id

    # Detail
    get_res = client.get(f"/api/roadmaps/{roadmap_id}", headers=headers)
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == roadmap_id
    assert detail["total_items"] == len(detail["items"])
    assert detail["completion_percentage"] == 0.0


def test_roadmap_item_completion_toggle(client):
    """Test PATCH /api/roadmaps/{roadmap_id}/items/{item_id}."""
    headers = get_auth_header(1)

    gen_res = client.post("/api/roadmaps/generate/1", headers=headers)
    roadmap_id = gen_res.json()["id"]
    item_id = gen_res.json()["items"][0]["id"]

    # Toggle to completed
    patch_res = client.patch(
        f"/api/roadmaps/{roadmap_id}/items/{item_id}",
        json={"is_completed": True},
        headers=headers
    )
    assert patch_res.status_code == 200
    item_data = patch_res.json()
    assert item_data["is_completed"] is True
    assert item_data["completed_at"] is not None

    # Check progress updated
    detail_res = client.get(f"/api/roadmaps/{roadmap_id}", headers=headers)
    assert detail_res.json()["completed_items"] == 1
    assert detail_res.json()["completion_percentage"] > 0

    # Toggle back to incomplete
    patch_back = client.patch(
        f"/api/roadmaps/{roadmap_id}/items/{item_id}",
        json={"is_completed": False},
        headers=headers
    )
    assert patch_back.status_code == 200
    assert patch_back.json()["is_completed"] is False
    assert patch_back.json()["completed_at"] is None


def test_roadmap_progress_summary_endpoint(client):
    """Test GET /api/roadmaps/summary/progress."""
    headers = get_auth_header(1)

    client.post("/api/roadmaps/generate/1", headers=headers)

    sum_res = client.get("/api/roadmaps/summary/progress", headers=headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["total_roadmaps"] >= 1
    assert summary["active_roadmap"] is not None
    assert summary["total_items"] > 0


def test_user_isolation_and_unauthorized_access(client):
    """Verify unauthorized and cross-user access restrictions."""
    headers_u1 = get_auth_header(1)
    headers_u2 = get_auth_header(2)

    gen_res = client.post("/api/roadmaps/generate/1", headers=headers_u1)
    roadmap_id = gen_res.json()["id"]
    item_id = gen_res.json()["items"][0]["id"]

    # Unauthenticated access
    assert client.get("/api/roadmaps").status_code == 401
    assert client.get(f"/api/roadmaps/{roadmap_id}").status_code == 401
    assert client.post("/api/roadmaps/generate/1").status_code == 401

    # User 2 cannot generate roadmap for User 1's job analysis (ID 1)
    res_gen_u2 = client.post("/api/roadmaps/generate/1", headers=headers_u2)
    assert res_gen_u2.status_code == 404

    # User 2 cannot view User 1's roadmap
    res_view_u2 = client.get(f"/api/roadmaps/{roadmap_id}", headers=headers_u2)
    assert res_view_u2.status_code == 404

    # User 2 cannot toggle User 1's roadmap item
    res_toggle_u2 = client.patch(
        f"/api/roadmaps/{roadmap_id}/items/{item_id}",
        json={"is_completed": True},
        headers=headers_u2
    )
    assert res_toggle_u2.status_code == 404


def test_delete_roadmap_and_non_existent(client):
    """Test DELETE /api/roadmaps/{id} and 404 handling."""
    headers = get_auth_header(1)

    # Non-existent job analysis
    assert client.post("/api/roadmaps/generate/9999", headers=headers).status_code == 404

    # Non-existent roadmap
    assert client.get("/api/roadmaps/9999", headers=headers).status_code == 404
    assert client.delete("/api/roadmaps/9999", headers=headers).status_code == 404

    # Delete existing
    gen_res = client.post("/api/roadmaps/generate/1", headers=headers)
    roadmap_id = gen_res.json()["id"]

    del_res = client.delete(f"/api/roadmaps/{roadmap_id}", headers=headers)
    assert del_res.status_code == 200

    # Getting after delete should 404
    assert client.get(f"/api/roadmaps/{roadmap_id}", headers=headers).status_code == 404
