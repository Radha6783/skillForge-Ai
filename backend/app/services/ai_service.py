"""
AI Service for Job Description Analysis, Skill Extraction, and Learning Roadmap Generation.

Uses Google Gemini API when GEMINI_API_KEY is configured.
Includes fallback rule-based analyzer and deterministic curriculum generator
so the application always works reliably offline or without API keys.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from app.schemas.job_analysis import AnalysisResultSchema

logger = logging.getLogger(__name__)

# Common tech skill catalog for fallback parser
TECH_KEYWORDS = {
    "programming_languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Golang",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "SQL", "Bash", "Shell"
    ],
    "frameworks": [
        "React", "React.js", "Vue", "Vue.js", "Angular", "Next.js", "Nuxt.js",
        "Express", "Express.js", "Node.js", "Django", "Flask", "FastAPI", "Spring",
        "Spring Boot", "Laravel", "ASP.NET", "Ruby on Rails", "Tailwind CSS", "Bootstrap"
    ],
    "databases": [
        "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "SQLite",
        "Oracle", "SQL Server", "DynamoDB", "Cassandra", "Elasticsearch", "Neo4j"
    ],
    "cloud_and_devops": [
        "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker",
        "Kubernetes", "K8s", "Terraform", "CI/CD", "GitHub Actions", "Jenkins",
        "Ansible", "Linux", "Nginx", "Serverless"
    ],
    "tools": [
        "Git", "GitHub", "GitLab", "Jira", "Postman", "Figma", "Docker Desktop",
        "VS Code", "Webpack", "Vite", "Grafana", "Prometheus"
    ],
    "soft_skills": [
        "Communication", "Teamwork", "Problem Solving", "Leadership", "Agile",
        "Scrum", "Critical Thinking", "Time Management", "Collaboration", "Mentorship"
    ]
}

# Predefined curriculum templates for common skills
CURRICULUM_CATALOG: Dict[str, Dict[str, str]] = {
    "python": {
        "topic": "Python Programming & Backend Architecture",
        "learning_objectives": "Master OOP principles, type annotations, list/dict comprehensions, context managers, exception handling, and async IO concepts.",
        "practice_task": "Build an asynchronous data processing pipeline that reads and validates unstructured records with error recovery.",
        "suggested_project": "CLI Task & Automation Manager with persistent storage and asynchronous execution."
    },
    "fastapi": {
        "topic": "High-Performance REST APIs with FastAPI",
        "learning_objectives": "Understand ASGI architecture, Pydantic v2 validation models, dependency injection, OAuth2 authentication, and API error handlers.",
        "practice_task": "Create a CRUD REST API with JWT bearer security, query parameter filtering, and automatic Swagger docs.",
        "suggested_project": "Microservice API gateway with authentication, rate limiting, and database session middleware."
    },
    "sql": {
        "topic": "Relational Database Design & Advanced SQL",
        "learning_objectives": "Master INNER/LEFT/FULL joins, GROUP BY aggregations, window functions, CTEs (Common Table Expressions), and query execution plans.",
        "practice_task": "Write complex analytical queries calculating rolling averages, rankings, and cohort retention.",
        "suggested_project": "Database performance optimization suite with schema normalization, indexing strategies, and benchmarks."
    },
    "postgresql": {
        "topic": "PostgreSQL Administration & Schema Modeling",
        "learning_objectives": "Understand relational schemas, foreign keys, constraints, JSONB data types, transaction isolation levels, and migration tools.",
        "practice_task": "Design and execute an Alembic database migration incorporating unique constraints and index tuning.",
        "suggested_project": "E-Commerce relational database schema with full-text search indexing and audit logging."
    },
    "docker": {
        "topic": "Containerization & Docker Ecosystem",
        "learning_objectives": "Master Dockerfile creation, multi-stage builds, container isolation, volume mounts, networking, and Docker Compose orchestration.",
        "practice_task": "Containerize a multi-service web app (frontend, backend, database) with healthchecks and environment variables.",
        "suggested_project": "Production-ready Docker Compose environment with Nginx reverse proxy and SSL configuration."
    },
    "kubernetes": {
        "topic": "Kubernetes Cluster Management & Orchestration",
        "learning_objectives": "Understand Pods, Deployments, ReplicaSets, Services (ClusterIP/NodePort), ConfigMaps, Secrets, and Ingress controllers.",
        "practice_task": "Write declarative YAML manifests to deploy, scale, and expose an application with rolling updates.",
        "suggested_project": "High-availability multi-pod application deployment with automated zero-downtime scaling."
    },
    "react": {
        "topic": "Modern Frontend Development with React",
        "learning_objectives": "Understand functional components, hooks (useState, useEffect, useMemo), custom hooks, component lifecycles, and state management.",
        "practice_task": "Build an interactive dashboard with responsive state, real-time filtering, and modal dialogs.",
        "suggested_project": "Full-featured client web application integrated with REST API endpoints and state persistence."
    },
    "typescript": {
        "topic": "Static Typing & Advanced TypeScript",
        "learning_objectives": "Master interfaces, types, generics, utility types (Partial, Pick, Omit), union discrimination, and TS config options.",
        "practice_task": "Refactor JavaScript modules to strictly typed TypeScript with comprehensive interface definitions.",
        "suggested_project": "Type-safe API client library with runtime validation and response contracts."
    },
    "javascript": {
        "topic": "Modern ECMAScript & Asynchronous JavaScript",
        "learning_objectives": "Understand ES6+ syntax, Promises, async/await, closures, event loop mechanics, and DOM event handling.",
        "practice_task": "Build an asynchronous data fetcher with retry logic, timeout handling, and cancellation tokens.",
        "suggested_project": "Interactive interactive client utility with modular ES modules and event listeners."
    },
    "node.js": {
        "topic": "Server-Side JavaScript with Node.js & Express",
        "learning_objectives": "Understand Node event-driven architecture, streams, buffer, Express middleware routing, and async error handling.",
        "practice_task": "Develop a REST API backend with input sanitization, JWT authorization, and file upload endpoints.",
        "suggested_project": "Real-time logging and notification service utilizing Express and websocket connections."
    },
    "django": {
        "topic": "Full-Stack Web Development with Django",
        "learning_objectives": "Understand MVT architecture, Django ORM, migration system, Django REST framework serializers, and admin dashboards.",
        "practice_task": "Create a Django application with model relationships, custom queryset filters, and serializer validation.",
        "suggested_project": "Content management platform with user role permissions and REST API endpoints."
    },
    "aws": {
        "topic": "Cloud Computing Infrastructure on AWS",
        "learning_objectives": "Understand core AWS services (EC2, S3, RDS, IAM, Lambda, VPC) and cloud security best practices.",
        "practice_task": "Configure an IAM role with least privilege, provision an S3 bucket, and trigger a serverless Lambda function.",
        "suggested_project": "Automated cloud deployment pipeline connecting application storage with S3 and RDS database."
    },
    "git": {
        "topic": "Version Control & Collaborative Git Workflows",
        "learning_objectives": "Master branching strategies, rebasing, merge conflict resolution, interactive rebase, and GitHub pull request workflows.",
        "practice_task": "Simulate and resolve complex merge conflicts across parallel feature branches using rebase.",
        "suggested_project": "Git repository setup with pre-commit hooks, linting automation, and branch protection rules."
    },
    "redis": {
        "topic": "In-Memory Caching & Data Structures with Redis",
        "learning_objectives": "Understand key-value caching, TTL expiration, hashes, sets, sorted sets, Pub/Sub channels, and cache-aside patterns.",
        "practice_task": "Implement an API response caching layer with cache invalidation on write operations.",
        "suggested_project": "Distributed session store and rate-limiting middleware using Redis key expiration."
    },
    "mongodb": {
        "topic": "NoSQL Document Modeling with MongoDB",
        "learning_objectives": "Understand document schemas, BSON types, aggregation pipelines, indexing, and Mongoose/Motor ODM drivers.",
        "practice_task": "Construct a multi-stage aggregation pipeline calculating metrics and grouped stats.",
        "suggested_project": "Event analytics database storing flexible event payloads with index optimization."
    },
    "java": {
        "topic": "Core Java & Object-Oriented System Architecture",
        "learning_objectives": "Master Java OOP concepts, Collections Framework, generics, multithreading, Streams API, and JVM memory model.",
        "practice_task": "Implement a concurrent thread-safe task queue using Java ExecutorService and Streams.",
        "suggested_project": "Enterprise command-line data processing tool with robust logging and unit tests."
    },
    "spring boot": {
        "topic": "Enterprise Microservices with Spring Boot",
        "learning_objectives": "Understand Spring IoC, dependency injection, Spring Data JPA, Spring Security, and actuator monitoring.",
        "practice_task": "Build a secure RESTful service with JPA entity repositories and custom exceptions.",
        "suggested_project": "Banking or payment transaction simulation microservice with auditing and validation."
    }
}


def _extract_fallback_analysis(job_description: str, job_title_hint: Optional[str] = None) -> AnalysisResultSchema:
    """
    Smart heuristic extraction fallback when Gemini API is unavailable or unconfigured.
    Rule-based regex matching across skill catalogs, title detection, and requirements.
    """
    text_lower = job_description.lower()
    lines = [line.strip() for line in job_description.split("\n") if line.strip()]

    # 1. Infer Job Title if not provided
    extracted_title = job_title_hint or ""
    if not extracted_title and lines:
        first_line = lines[0]
        if len(first_line) <= 80 and not first_line.endswith("."):
            extracted_title = first_line
        else:
            match = re.search(
                r'(senior|junior|lead|principal|staff)?\s*(software|full\s*stack|frontend|backend|devops|data|ai|ml|cloud|systems)\s*(engineer|developer|architect|analyst)',
                job_description,
                re.IGNORECASE
            )
            if match:
                extracted_title = match.group(0).title()
            else:
                extracted_title = "Software Professional"

    # 2. Extract Category Tech Stack
    found_langs = [l for l in TECH_KEYWORDS["programming_languages"] if re.search(r'\b' + re.escape(l.lower()) + r'\b', text_lower)]
    found_frameworks = [f for f in TECH_KEYWORDS["frameworks"] if re.search(r'\b' + re.escape(f.lower()) + r'\b', text_lower)]
    found_dbs = [d for d in TECH_KEYWORDS["databases"] if re.search(r'\b' + re.escape(d.lower()) + r'\b', text_lower)]
    found_cloud = [c for c in TECH_KEYWORDS["cloud_and_devops"] if re.search(r'\b' + re.escape(c.lower()) + r'\b', text_lower)]
    found_tools = [t for t in TECH_KEYWORDS["tools"] if re.search(r'\b' + re.escape(t.lower()) + r'\b', text_lower)]
    found_soft = [s for s in TECH_KEYWORDS["soft_skills"] if re.search(r'\b' + re.escape(s.lower()) + r'\b', text_lower)]

    # 3. Categorize into Required vs Preferred
    required_skills = list(set(found_langs + found_frameworks + found_dbs))
    if not required_skills:
        required_skills = ["Software Development", "Problem Solving"]

    preferred_skills = list(set(found_cloud + found_tools + found_soft))

    exp_matches = re.findall(r'(\d+\+?\s*(?:-\s*\d+)?\s*(?:years?|yrs?)(?:\s*of\s*experience)?)', text_lower)
    experience_reqs = [m.title() for m in exp_matches[:3]] if exp_matches else ["3+ years relevant software engineering experience"]

    edu_matches = re.findall(r"(bachelor'?s?|master'?s?|phd|computer science|engineering|degree)", text_lower)
    education_reqs = list(set([m.title() for m in edu_matches])) if edu_matches else ["Bachelor's degree in Computer Science or related technical field"]

    summary = (
        f"Position for {extracted_title}. Core skill requirements include "
        f"{', '.join(required_skills[:5]) if required_skills else 'general technical skills'}. "
        f"Looking for candidates with strong foundational principles and collaborative background."
    )

    keywords = list(set([extracted_title] + required_skills + preferred_skills))

    return AnalysisResultSchema(
        job_title=extracted_title,
        summary=summary,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        programming_languages=found_langs,
        frameworks=found_frameworks,
        databases=found_dbs,
        cloud_and_devops=found_cloud,
        tools=found_tools,
        soft_skills=found_soft,
        experience_requirements=experience_reqs,
        education_requirements=education_reqs,
        keywords=keywords
    )


def analyze_job_description(job_description: str, job_title_hint: Optional[str] = None) -> AnalysisResultSchema:
    """
    Analyzes job description text using Gemini AI model when available,
    falling back to smart heuristic parsing when API key is missing/unreachable.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", "google_gemini")

    if gemini_key and gemini_key != "your_gemini_api_key_here" and ai_provider == "google_gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)

            system_prompt = """
You are an expert technical recruiter and career analyzer AI.
Analyze the following job description and return a structured JSON response matching this schema EXACTLY:
{
    "job_title": "Clean concise job title",
    "summary": "2-3 sentence executive summary of the role",
    "required_skills": ["List of mandatory technical and core skills"],
    "preferred_skills": ["List of nice-to-have or bonus skills"],
    "programming_languages": ["Language 1", "Language 2"],
    "frameworks": ["Framework 1", "Framework 2"],
    "databases": ["Database 1"],
    "cloud_and_devops": ["Cloud/DevOps tool 1"],
    "tools": ["Developer tool 1"],
    "soft_skills": ["Soft skill 1"],
    "experience_requirements": ["Year requirements or specific domain experience"],
    "education_requirements": ["Degree or education requirements"],
    "keywords": ["Top 10 searchable domain keywords"]
}
Return ONLY pure JSON. Do not include markdown code fences or conversational text.
"""
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"{system_prompt}\n\nJob Title Hint: {job_title_hint or 'None'}\n\nJob Description:\n{job_description}"
            
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            cleaned_json = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.MULTILINE)
            cleaned_json = re.sub(r'\s*```$', '', cleaned_json, flags=re.MULTILINE)
            
            data = json.loads(cleaned_json)
            return AnalysisResultSchema(**data)

        except Exception as e:
            logger.warning(f"Gemini API call failed ({e}). Falling back to heuristic job analyzer.")
            return _extract_fallback_analysis(job_description, job_title_hint)

    logger.info("GEMINI_API_KEY not configured. Using fallback heuristic analyzer.")
    return _extract_fallback_analysis(job_description, job_title_hint)


def _generate_fallback_roadmap(
    target_role: str,
    job_title: str,
    gap_skills: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Deterministic skill-aware fallback learning roadmap generator.
    Produces high-quality, practical learning phases tailored exclusively to the supplied gap skills.
    """
    if not gap_skills:
        gap_skills = [{"skill_name": "Core Software Engineering", "priority": "HIGH"}]

    if not gap_skills:
        gap_skills = [{"skill_name": "Core Software Engineering", "priority": "HIGH"}]

    # Allocate a realistic 4 to 8 week curriculum
    expanded_items = []
    if len(gap_skills) == 1:
        s = gap_skills[0]
        expanded_items = [
            (s, "Foundations & Syntax", "Core fundamentals and essential paradigms."),
            (s, "Core Architecture & Patterns", "Design patterns and architectural best practices."),
            (s, "Advanced Implementation & Testing", "Complex scenarios, unit testing, and optimization."),
            (s, "Production Capstone Project", "End-to-end production deployment and portfolio project.")
        ]
    elif len(gap_skills) == 2:
        s1, s2 = gap_skills[0], gap_skills[1]
        expanded_items = [
            (s1, "Foundations & Core Principles", "Foundational concepts and development workflow."),
            (s1, "Advanced Patterns & Optimization", "Advanced architecture, performance, and best practices."),
            (s2, "Foundations & Core Principles", "Foundational concepts and development workflow."),
            (s2, "Integration & Capstone Deliverable", "Real-world integration and production deliverable.")
        ]
    elif len(gap_skills) == 3:
        s1, s2, s3 = gap_skills[0], gap_skills[1], gap_skills[2]
        expanded_items = [
            (s1, "Foundations & Core Concepts", "Foundational concepts and architecture."),
            (s2, "Foundations & Core Concepts", "Foundational concepts and architecture."),
            (s3, "Foundations & Core Concepts", "Foundational concepts and architecture."),
            (s1, "Advanced Integration & Capstone", "Cross-skill integration and final project.")
        ]
    else:
        expanded_items = [(s, None, None) for s in gap_skills[:8]]

    total_weeks = len(expanded_items)
    weekly_phases = []

    for idx, (skill_info, sub_title, sub_desc) in enumerate(expanded_items):
        week_num = idx + 1
        skill_name = skill_info.get("skill_name", "Technical Skill")
        skill_key = skill_name.strip().lower()
        priority = skill_info.get("priority", "MEDIUM")

        template = CURRICULUM_CATALOG.get(skill_key)
        if template:
            base_topic = template["topic"]
            topic = f"{base_topic}: {sub_title}" if sub_title else base_topic
            objectives = f"{template['learning_objectives']} {sub_desc or ''}".strip()
            task = template["practice_task"]
            project = template["suggested_project"]
        else:
            topic = f"{skill_name}: {sub_title}" if sub_title else f"{skill_name} Foundations & Practical Implementation"
            objectives = f"Understand core architectural principles, key paradigms, and industry best practices for {skill_name}. {sub_desc or ''}".strip()
            task = f"Develop hands-on exercises demonstrating practical configuration and coding with {skill_name}."
            project = f"Implement a functional portfolio module integrating {skill_name} into a real-world scenario."

        est_hours = 12 if priority == "HIGH" else 8

        weekly_phases.append({
            "week_number": week_num,
            "skill_name": skill_name,
            "topic": topic,
            "priority": priority,
            "estimated_hours": est_hours,
            "learning_objectives": objectives,
            "practice_task": task,
            "suggested_project": project
        })

    title = f"{target_role or job_title} Personalized Mastery Roadmap"
    description = (
        f"A targeted {total_weeks}-week accelerated curriculum built to close your critical skill gaps "
        f"for {job_title}. Prioritizes high-impact missing competencies and advances partial skill areas."
    )

    return {
        "title": title,
        "description": description,
        "total_weeks": total_weeks,
        "weekly_phases": weekly_phases
    }



def generate_roadmap_ai(
    target_role: str,
    job_title: str,
    gap_skills: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generates a personalized, week-by-week learning roadmap using Gemini AI when configured,
    or falls back to deterministic curriculum generation based on the actual skill gap list.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", "google_gemini")

    if gemini_key and gemini_key != "your_gemini_api_key_here" and ai_provider == "google_gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)

            system_prompt = """
You are a principal software engineering mentor and curriculum architect.
Create a personalized learning roadmap tailored strictly to the user's specific skill gaps.

CRITICAL RULES:
1. ONLY teach skills explicitly provided in the supplied gap list. Do NOT invent or add external skills (no random React, AWS, etc. unless provided).
2. Prioritize missing skills before partial-gap skills.
3. Keep the total weeks between 4 and 8.
4. Each week must contain actionable, practical learning objectives, a hands-on coding task, and a portfolio mini-project.
5. Return ONLY pure JSON matching this schema:
{
    "title": "Roadmap title",
    "description": "2-3 sentence overview of the customized learning plan",
    "total_weeks": 4,
    "weekly_phases": [
        {
            "week_number": 1,
            "skill_name": "Exact skill name from gap list",
            "topic": "Concise weekly topic",
            "priority": "HIGH or MEDIUM or LOW",
            "estimated_hours": 10,
            "learning_objectives": "Specific concepts to master",
            "practice_task": "Concrete coding task to complete",
            "suggested_project": "Mini-project deliverable"
        }
    ]
}
"""
            model = genai.GenerativeModel('gemini-1.5-flash')
            gaps_summary = json.dumps([
                {"skill": g.get("skill_name"), "status": g.get("status"), "priority": g.get("priority")}
                for g in gap_skills
            ], indent=2)

            prompt = (
                f"{system_prompt}\n\n"
                f"Target Role: {target_role}\n"
                f"Job Position Title: {job_title}\n"
                f"User Skill Gaps to Cover:\n{gaps_summary}"
            )

            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            cleaned_json = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.MULTILINE)
            cleaned_json = re.sub(r'\s*```$', '', cleaned_json, flags=re.MULTILINE)

            data = json.loads(cleaned_json)
            # Validate required fields
            if "weekly_phases" in data and len(data["weekly_phases"]) > 0:
                return data

        except Exception as e:
            logger.warning(f"Gemini roadmap generation failed ({e}). Falling back to curriculum generator.")
            return _generate_fallback_roadmap(target_role, job_title, gap_skills)

    logger.info("Using fallback deterministic roadmap generator.")
    return _generate_fallback_roadmap(target_role, job_title, gap_skills)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 8: INTERVIEW SIMULATOR — Question Generation & Answer Evaluation
# ─────────────────────────────────────────────────────────────────────────────

# Per-skill question templates (difficulty: EASY/MEDIUM/HARD; type: TECHNICAL/SCENARIO/BEHAVIORAL)
INTERVIEW_QUESTION_CATALOG: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "python": {
        "TECHNICAL": [
            {"EASY": "What are Python's mutable vs immutable data types? Give one example of each.",
             "key_points": "list/dict mutable; int/str/tuple immutable; memory implications"},
            {"MEDIUM": "Explain Python's Global Interpreter Lock (GIL) and its impact on multi-threaded programs.",
             "key_points": "GIL prevents true parallel thread execution; affects CPU-bound tasks; use multiprocessing for parallelism"},
            {"HARD": "Design a Python async pipeline that fetches data concurrently from multiple endpoints and aggregates results with error handling.",
             "key_points": "asyncio, aiohttp, gather/TaskGroup, error isolation, result aggregation"},
        ],
        "SCENARIO": [
            {"MEDIUM": "A Python API is consuming 4GB of memory processing large CSV files. How would you diagnose and fix this?",
             "key_points": "generator-based reading, chunked processing, memory profiling, pandas chunksize"},
        ],
    },
    "fastapi": {
        "TECHNICAL": [
            {"EASY": "How does FastAPI use Pydantic for request validation?",
             "key_points": "type annotations, BaseModel, automatic 422 response, request body parsing"},
            {"MEDIUM": "Explain FastAPI's dependency injection system with an example.",
             "key_points": "Depends(), reusable dependencies, database sessions, auth injection"},
            {"HARD": "How would you implement rate limiting and request throttling in a FastAPI application?",
             "key_points": "middleware, Redis token bucket, SlowAPI, per-user limits"},
        ],
        "SCENARIO": [
            {"MEDIUM": "A FastAPI endpoint returns 200ms in development but 2s in production under load. Walk me through your investigation.",
             "key_points": "profiling, DB queries, connection pooling, async vs sync, load testing"},
        ],
    },
    "sql": {
        "TECHNICAL": [
            {"EASY": "What is the difference between INNER JOIN and LEFT JOIN?",
             "key_points": "INNER returns matching rows only; LEFT returns all left table rows + matched right"},
            {"MEDIUM": "Write a SQL query using a window function to rank employees by salary within their department.",
             "key_points": "RANK()/DENSE_RANK(), PARTITION BY department, ORDER BY salary"},
            {"HARD": "What is a Common Table Expression (CTE) and when would you use a recursive CTE?",
             "key_points": "WITH clause, readability, recursive for hierarchical/tree data, termination condition"},
        ],
        "SCENARIO": [
            {"MEDIUM": "A query that joins 3 large tables takes 45 seconds. How would you optimize it?",
             "key_points": "EXPLAIN ANALYZE, indexes, query rewrite, avoid SELECT *, covering index"},
        ],
    },
    "docker": {
        "TECHNICAL": [
            {"EASY": "What is the difference between a Docker image and a Docker container?",
             "key_points": "image is blueprint/read-only; container is running instance; layers"},
            {"MEDIUM": "Explain multi-stage Docker builds and why they reduce image size.",
             "key_points": "builder stage vs runtime stage, only copy artifacts, no dev dependencies in prod"},
            {"HARD": "How would you configure a Docker Compose setup for a web app with zero-downtime deployments?",
             "key_points": "rolling updates, healthchecks, depends_on, nginx load balancing, rolling restart"},
        ],
    },
    "react": {
        "TECHNICAL": [
            {"EASY": "What is the difference between state and props in React?",
             "key_points": "props are read-only/passed by parent; state is internal and mutable via setState"},
            {"MEDIUM": "Explain React's useEffect hook and when to provide a cleanup function.",
             "key_points": "side effects, dependency array, cleanup for subscriptions/timers/event listeners"},
            {"HARD": "What is React's reconciliation algorithm and how does the virtual DOM optimize performance?",
             "key_points": "diffing, fiber reconciler, key prop importance, batching updates"},
        ],
        "SCENARIO": [
            {"MEDIUM": "A React app re-renders unnecessarily causing poor performance. How do you diagnose and fix it?",
             "key_points": "React DevTools Profiler, memo, useMemo, useCallback, key stability"},
        ],
    },
    "aws": {
        "TECHNICAL": [
            {"EASY": "What is the difference between S3 and EC2?",
             "key_points": "S3 = object storage; EC2 = virtual machine; use cases"},
            {"MEDIUM": "Explain the difference between vertical and horizontal scaling in AWS.",
             "key_points": "vertical = bigger instance; horizontal = more instances + load balancer; auto-scaling groups"},
            {"HARD": "Design a highly available, fault-tolerant AWS architecture for a REST API serving 100k requests/min.",
             "key_points": "ALB, ECS/EKS, multi-AZ RDS, ElastiCache, CloudFront, WAF, auto-scaling"},
        ],
    },
    "kubernetes": {
        "TECHNICAL": [
            {"EASY": "What is the difference between a Pod and a Deployment in Kubernetes?",
             "key_points": "Pod = smallest unit; Deployment = manages replica sets and rolling updates"},
            {"MEDIUM": "How do Kubernetes Services expose applications, and what is the difference between ClusterIP, NodePort, and LoadBalancer?",
             "key_points": "ClusterIP=internal; NodePort=node port; LoadBalancer=cloud LB; Ingress for HTTP routing"},
            {"HARD": "Describe how Kubernetes handles rolling deployments and what you configure to prevent downtime.",
             "key_points": "maxUnavailable, maxSurge, readinessProbe, livenessProbe, rollback"},
        ],
    },
    "postgresql": {
        "TECHNICAL": [
            {"EASY": "What are PostgreSQL indexes and why are they important?",
             "key_points": "speed up SELECT queries; B-tree default; trade-off with write speed; covering indexes"},
            {"MEDIUM": "Explain JSONB in PostgreSQL and when you would use it instead of a relational schema.",
             "key_points": "binary JSON; indexable; flexible schema; good for variable attributes; operators @>, ->, ->>"},
            {"HARD": "What are PostgreSQL transaction isolation levels and what anomalies do they prevent?",
             "key_points": "READ COMMITTED (default), REPEATABLE READ, SERIALIZABLE; dirty read, non-repeatable read, phantom read"},
        ],
    },
    "typescript": {
        "TECHNICAL": [
            {"EASY": "What are TypeScript interfaces and how do they differ from types?",
             "key_points": "interface: extendable, declaration merging; type: unions/intersections; generally interchangeable for objects"},
            {"MEDIUM": "Explain TypeScript generics and give an example.",
             "key_points": "type parameters, reusable typed components, <T>, constrained generics with extends"},
            {"HARD": "What are TypeScript mapped types and conditional types? Provide a real-world use case.",
             "key_points": "Partial<T>, Required<T>, Record, Readonly; conditional: T extends U ? X : Y; utility types"},
        ],
    },
    "node.js": {
        "TECHNICAL": [
            {"EASY": "What is the Node.js event loop and why is Node considered non-blocking?",
             "key_points": "single-threaded; libuv; async I/O; event queue phases; callbacks/promises"},
            {"MEDIUM": "Explain the difference between process.nextTick() and setImmediate() in Node.js.",
             "key_points": "nextTick fires before I/O events; setImmediate fires in check phase; use cases"},
            {"HARD": "How would you handle CPU-intensive tasks in a Node.js application without blocking the event loop?",
             "key_points": "Worker threads, child_process, clustering, offloading to microservices"},
        ],
    },
    "mongodb": {
        "TECHNICAL": [
            {"EASY": "What is MongoDB and how does it differ from relational databases?",
             "key_points": "document-oriented; BSON; flexible schema; no fixed joins; horizontal sharding"},
            {"MEDIUM": "Explain MongoDB's aggregation pipeline and give an example.",
             "key_points": "$match, $group, $project, $sort, $lookup; pipeline stages; performance"},
            {"HARD": "When would you use MongoDB vs PostgreSQL for a new application?",
             "key_points": "document flexibility vs strong relations; ACID vs eventual consistency; schema maturity; query patterns"},
        ],
    },
    "git": {
        "TECHNICAL": [
            {"EASY": "What is the difference between git merge and git rebase?",
             "key_points": "merge preserves history with merge commit; rebase linearizes history; when to use each"},
            {"MEDIUM": "Explain the Git branching strategy used in a production workflow (e.g. Gitflow or trunk-based).",
             "key_points": "feature branches, main/develop/release, PR reviews, CI integration, trunk-based = short-lived branches"},
        ],
    },
}

# Behavioral question templates (role-agnostic but contextually framed)
BEHAVIORAL_QUESTIONS: List[Dict[str, str]] = [
    {"text": "Tell me about a time you encountered a difficult technical bug. How did you diagnose and resolve it?",
     "key_points": "systematic debugging, root cause analysis, communication, documentation"},
    {"text": "Describe a situation where you had to learn a new technology quickly to deliver a project. What was your approach?",
     "key_points": "learning strategy, prioritization, applying knowledge, outcome"},
    {"text": "Tell me about a time you disagreed with a technical decision made by your team. How did you handle it?",
     "key_points": "constructive disagreement, data-driven argument, team alignment, outcome"},
    {"text": "Describe your experience working in an Agile environment. How do you manage competing priorities and deadlines?",
     "key_points": "sprint planning, backlog grooming, communication, trade-off decisions"},
    {"text": "Tell me about a time you had to explain a complex technical concept to a non-technical stakeholder.",
     "key_points": "simplification, analogies, active listening, outcome"},
    {"text": "Describe a project where you took ownership of a critical component end-to-end. What challenges did you face?",
     "key_points": "ownership, proactive communication, problem solving, delivery"},
    {"text": "Tell me about a time you identified and fixed a performance issue in a system you were working on.",
     "key_points": "profiling, root cause, fix, measurement, impact"},
    {"text": "How do you approach code reviews — both giving and receiving feedback?",
     "key_points": "constructive critique, learning mindset, standards, team culture"},
    {"text": "Describe how you handle situations when project requirements change mid-development.",
     "key_points": "adaptability, stakeholder communication, impact assessment, reprioritization"},
    {"text": "Tell me about a time when you had to collaborate across teams to deliver a feature.",
     "key_points": "cross-functional collaboration, communication, dependency management, outcome"},
]


def _get_difficulty_questions(skill_lower: str, difficulty: str, q_type: str) -> Optional[Dict[str, str]]:
    """Fetch a question for a specific skill, difficulty, and type from catalog."""
    catalog = INTERVIEW_QUESTION_CATALOG.get(skill_lower, {})
    type_questions = catalog.get(q_type, catalog.get("TECHNICAL", []))
    if not type_questions:
        return None
    for q in type_questions:
        if difficulty in q:
            return {"text": q[difficulty], "key_points": q.get("key_points", "")}
    # Fallback to first available question in that category
    first = type_questions[0]
    for diff in ["MEDIUM", "HARD", "EASY"]:
        if diff in first:
            return {"text": first[diff], "key_points": first.get("key_points", "")}
    return None


def _make_generic_question(skill_name: str, difficulty: str, q_type: str) -> Dict[str, str]:
    """Generate a skill-specific generic question for skills not in the catalog."""
    templates = {
        "TECHNICAL": {
            "EASY": f"What is {skill_name} and what problem does it solve? Describe its core use case.",
            "MEDIUM": f"Explain the key concepts and architecture of {skill_name}. How have you applied it in a project?",
            "HARD": f"Describe an advanced {skill_name} scenario you have implemented, including the design decisions and trade-offs you made.",
        },
        "SCENARIO": {
            "EASY": f"You are asked to evaluate whether {skill_name} is a good fit for a new project. What factors do you consider?",
            "MEDIUM": f"A team member is struggling with a complex {skill_name} problem. Walk me through how you would help them debug it.",
            "HARD": f"You need to migrate an existing system to use {skill_name} at scale. How do you plan and execute this migration with zero downtime?",
        },
        "BEHAVIORAL": {
            "EASY": f"Describe your experience working with {skill_name}. How did you get started?",
            "MEDIUM": f"Tell me about a project where {skill_name} was critical. What challenges did you face?",
            "HARD": f"Describe a time when you had to make a difficult architectural decision involving {skill_name}. What were the trade-offs?",
        },
    }
    diff = difficulty if difficulty in ["EASY", "MEDIUM", "HARD"] else "MEDIUM"
    qt = q_type if q_type in templates else "TECHNICAL"
    return {
        "text": templates[qt][diff],
        "key_points": f"knowledge of {skill_name}, practical experience, problem solving, trade-offs"
    }


def _generate_fallback_questions(
    target_role: str,
    job_title: str,
    job_requirements: List[Dict[str, Any]],
    skill_gaps: Dict[str, Any],
    interview_type: str,
    difficulty: str,
    count: int
) -> List[Dict[str, Any]]:
    """
    Generates exactly `count` interview questions deterministically from actual JobAnalysis
    skills and SkillGapReport data. No hallucinated technologies.

    Priority order:
    1. Missing HIGH-priority skills
    2. Missing MEDIUM-priority skills
    3. Missing LOW-priority skills
    4. Partial/weak skills
    5. Matched required skills from JobAnalysis
    6. Behavioral questions (fills remaining slots when type is BEHAVIORAL/MIXED)
    """
    missing = skill_gaps.get("missing_skills", [])
    weak = skill_gaps.get("weak_skills", [])
    matched = skill_gaps.get("matching_skills", [])

    # Ordered required skills from job analysis for grounding
    req_skill_names = [r.get("skill_name", "") for r in job_requirements if r.get("skill_name")]

    # Priority buckets from gap data
    def _bucket(skills_list: List, status: str) -> List[Dict]:
        result = []
        for item in skills_list:
            sn = item.get("skill_name") or item.get("skill") or ""
            priority = item.get("priority", "MEDIUM") if isinstance(item, dict) else "MEDIUM"
            if sn:
                result.append({"skill_name": sn, "status": status, "priority": priority})
        return result

    priority_skills: List[Dict] = []
    # Missing HIGH → MED → LOW
    for pri in ["HIGH", "MEDIUM", "LOW"]:
        priority_skills += [s for s in _bucket(missing, "MISSING") if s["priority"] == pri]
    # Weak HIGH → MED → LOW
    for pri in ["HIGH", "MEDIUM", "LOW"]:
        priority_skills += [s for s in _bucket(weak, "PARTIAL") if s["priority"] == pri]
    # Matched required skills (low priority for technical grounding)
    for sn in req_skill_names:
        if not any(ps["skill_name"].lower() == sn.lower() for ps in priority_skills):
            priority_skills.append({"skill_name": sn, "status": "MATCHED", "priority": "LOW"})

    # Determine question type distribution
    if interview_type == "TECHNICAL":
        type_pool = ["TECHNICAL", "SCENARIO", "TECHNICAL", "TECHNICAL", "SCENARIO"]
    elif interview_type == "BEHAVIORAL":
        type_pool = ["BEHAVIORAL"] * count
    else:  # MIXED
        # ~60% technical, 40% behavioral
        n_tech = max(1, int(count * 0.6))
        n_beh = count - n_tech
        type_pool = ["TECHNICAL"] * n_tech + ["BEHAVIORAL"] * n_beh

    questions: List[Dict[str, Any]] = []
    used_skills: set = set()
    beh_idx = 0

    for i in range(count):
        q_type = type_pool[i] if i < len(type_pool) else "TECHNICAL"

        if q_type == "BEHAVIORAL":
            bq = BEHAVIORAL_QUESTIONS[beh_idx % len(BEHAVIORAL_QUESTIONS)]
            beh_idx += 1
            questions.append({
                "question_order": i + 1,
                "question_text": bq["text"],
                "question_type": "BEHAVIORAL",
                "skill_name": "Soft Skills",
                "topic": target_role,
                "difficulty": difficulty,
                "expected_key_points": bq["key_points"],
            })
        else:
            # Pick a skill not yet used
            skill_entry = None
            for ps in priority_skills:
                if ps["skill_name"].lower() not in used_skills:
                    skill_entry = ps
                    break
            if not skill_entry and priority_skills:
                # Cycle through skills if all used
                skill_entry = priority_skills[i % len(priority_skills)]

            if skill_entry:
                sn = skill_entry["skill_name"]
                used_skills.add(sn.lower())
                skill_lower = sn.lower().replace(" ", "").replace(".", "").replace("+", "plus")
                # Also try normalized key like "nodejs" for "node.js"
                catalog_key = skill_lower
                if catalog_key not in INTERVIEW_QUESTION_CATALOG:
                    # Try aliases
                    for alias in [sn.lower(), sn.lower().replace("-", ""), sn.lower().split(".")[0]]:
                        if alias in INTERVIEW_QUESTION_CATALOG:
                            catalog_key = alias
                            break

                q_data = _get_difficulty_questions(catalog_key, difficulty, "TECHNICAL" if q_type != "SCENARIO" else "SCENARIO")
                if not q_data:
                    q_data = _make_generic_question(sn, difficulty, q_type)

                questions.append({
                    "question_order": i + 1,
                    "question_text": q_data["text"],
                    "question_type": q_type if q_type in ["TECHNICAL", "SCENARIO"] else "TECHNICAL",
                    "skill_name": sn,
                    "topic": sn,
                    "difficulty": difficulty,
                    "expected_key_points": q_data.get("key_points", ""),
                })
            else:
                # No skills available — use a behavioral fallback
                bq = BEHAVIORAL_QUESTIONS[beh_idx % len(BEHAVIORAL_QUESTIONS)]
                beh_idx += 1
                questions.append({
                    "question_order": i + 1,
                    "question_text": bq["text"],
                    "question_type": "BEHAVIORAL",
                    "skill_name": "General",
                    "topic": target_role,
                    "difficulty": difficulty,
                    "expected_key_points": bq["key_points"],
                })

    return questions


def generate_interview_questions_ai(
    target_role: str,
    job_title: str,
    job_requirements: List[Dict[str, Any]],
    skill_gaps: Dict[str, Any],
    interview_type: str,
    difficulty: str,
    count: int
) -> List[Dict[str, Any]]:
    """
    Generates personalized interview questions grounded in the actual JobAnalysis
    and SkillGapReport. Uses Gemini when available, falls back to deterministic generator.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", "google_gemini")

    if gemini_key and gemini_key != "your_gemini_api_key_here" and ai_provider == "google_gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)

            req_summary = json.dumps(
                [{"skill": r.get("skill_name"), "importance": r.get("importance_level", "HIGH"),
                  "category": r.get("category")} for r in job_requirements],
                indent=2
            )
            missing = [s.get("skill_name") or s.get("skill") for s in skill_gaps.get("missing_skills", [])]
            weak = [s.get("skill_name") or s.get("skill") for s in skill_gaps.get("weak_skills", [])]

            prompt = f"""You are an expert technical interviewer creating a personalized interview for a {target_role} position.

STRICT RULES:
1. Generate EXACTLY {count} questions.
2. ONLY test skills from the provided job requirements list. Do NOT invent or add skills absent from the list.
3. Prioritize missing skills first: {missing}, then weak/partial skills: {weak}.
4. Interview type is {interview_type}. If TECHNICAL: mostly technical and scenario questions. If BEHAVIORAL: only behavioral. If MIXED: ~60% technical/scenario, ~40% behavioral.
5. All questions must be at {difficulty} difficulty level.
6. Each question MUST map to a real skill from the job requirements (use "Soft Skills" for behavioral).
7. Do not repeat the same question twice. Avoid near-duplicates.
8. Return ONLY a JSON array. No explanations, no markdown.

Job Requirements:
{req_summary}

Return JSON array (no wrapping object):
[
  {{
    "question_order": 1,
    "question_text": "...",
    "question_type": "TECHNICAL|SCENARIO|BEHAVIORAL",
    "skill_name": "exact skill name from requirements",
    "topic": "brief topic label",
    "difficulty": "{difficulty}",
    "expected_key_points": "comma-separated concepts expected in a good answer"
  }}
]"""

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)

            data = json.loads(cleaned)
            if isinstance(data, list) and len(data) == count:
                # Validate each question has required fields
                required_fields = {"question_order", "question_text", "question_type", "skill_name"}
                if all(required_fields.issubset(q.keys()) for q in data):
                    return data

        except Exception as e:
            logger.warning(f"Gemini interview question generation failed ({e}). Using deterministic fallback.")

    logger.info("Using deterministic interview question generator.")
    return _generate_fallback_questions(
        target_role, job_title, job_requirements, skill_gaps, interview_type, difficulty, count
    )


def _evaluate_fallback_answer(
    question_text: str,
    skill_name: str,
    expected_key_points: str,
    difficulty: str,
    user_answer: str,
) -> Dict[str, Any]:
    """
    Deterministic answer evaluation. Same question + same answer always produces the same result.
    Based on: answer length, key point coverage, technical vocabulary, and clarity.
    """
    answer_lower = user_answer.lower().strip()
    word_count = len(user_answer.split())
    key_points = [kp.strip().lower() for kp in expected_key_points.split(",") if kp.strip()]

    # 1. Length/substance score (0-25 pts)
    if word_count >= 120:
        length_score = 25
    elif word_count >= 60:
        length_score = 20
    elif word_count >= 30:
        length_score = 13
    elif word_count >= 10:
        length_score = 7
    else:
        length_score = 2

    # 2. Key point coverage (0-40 pts)
    if key_points:
        matched_kps = sum(1 for kp in key_points if any(word in answer_lower for word in kp.split()))
        coverage_ratio = matched_kps / len(key_points)
        coverage_score = int(coverage_ratio * 40)
    else:
        coverage_score = 20  # No key points defined, neutral

    # 3. Technical vocabulary score (0-20 pts)
    tech_terms = [
        "implement", "design", "optimize", "configure", "deploy", "debug", "refactor",
        "architecture", "performance", "scalable", "trade-off", "integration", "pipeline",
        "efficient", "latency", "throughput", "cache", "async", "concurrent", "index",
    ]
    skill_words = skill_name.lower().split()
    all_terms = tech_terms + skill_words
    term_hits = sum(1 for t in all_terms if t in answer_lower)
    vocab_score = min(20, term_hits * 3)

    # 4. Clarity score — sentence structure (0-15 pts)
    sentence_count = max(1, answer_lower.count(".") + answer_lower.count("!") + answer_lower.count("?"))
    avg_words_per_sentence = word_count / sentence_count
    if 10 <= avg_words_per_sentence <= 25:
        clarity_score = 15
    elif 6 <= avg_words_per_sentence < 30:
        clarity_score = 10
    else:
        clarity_score = 5

    raw_score = length_score + coverage_score + vocab_score + clarity_score  # max 100

    # Adjust for difficulty
    difficulty_multiplier = {"EASY": 1.0, "MEDIUM": 0.95, "HARD": 0.9}.get(difficulty, 0.95)
    final_score = min(100.0, round(raw_score * difficulty_multiplier, 1))

    # Derive component scores
    correctness = min(100.0, round((coverage_score / 40) * 100, 1))
    relevance = min(100.0, round((coverage_score + vocab_score) / 60 * 100, 1))
    technical_depth = min(100.0, round((vocab_score + length_score) / 45 * 100, 1))
    clarity = min(100.0, round((clarity_score + length_score * 0.3) / 22.5 * 100, 1))

    # Build feedback
    if final_score >= 80:
        strengths = f"Strong understanding of {skill_name}. Answer is well-structured, covers key concepts, and demonstrates practical knowledge."
        weaknesses = "Consider adding more concrete examples or discussing edge cases to strengthen your response."
        suggestion = f"Excellent answer. To push further, discuss performance trade-offs or real-world scenarios specific to {skill_name}."
    elif final_score >= 60:
        strengths = f"Demonstrates foundational knowledge of {skill_name} with some relevant details."
        weaknesses = f"The answer could benefit from covering more specific concepts: {', '.join(key_points[:3]) if key_points else 'core principles'}."
        suggestion = f"Expand your answer with concrete examples. Address key concepts: {', '.join(key_points[:2]) if key_points else skill_name + ' fundamentals'}."
    elif final_score >= 40:
        strengths = "Shows some awareness of the topic area."
        weaknesses = f"Missing important technical depth. Key areas not addressed: {', '.join(key_points[:3]) if key_points else skill_name + ' core concepts'}."
        suggestion = f"Study the fundamentals of {skill_name}. Focus on: {', '.join(key_points) if key_points else 'core concepts and practical applications'}."
    else:
        strengths = "Answer was submitted."
        weaknesses = f"The response lacks sufficient technical content about {skill_name}."
        suggestion = f"Review {skill_name} fundamentals thoroughly. A strong answer should cover: {', '.join(key_points) if key_points else 'key concepts, practical examples, and trade-offs'}."

    suggested = f"A strong answer would cover: {', '.join(key_points)}." if key_points else f"Demonstrate hands-on understanding of {skill_name} with concrete examples."

    return {
        "score": final_score,
        "correctness_score": correctness,
        "relevance_score": relevance,
        "technical_depth_score": technical_depth,
        "clarity_score": clarity,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvement_suggestion": suggestion,
        "suggested_answer": suggested,
        "topics_to_revise": ", ".join(key_points[:3]) if key_points else skill_name,
    }


def evaluate_interview_answer_ai(
    question_text: str,
    skill_name: str,
    expected_key_points: str,
    difficulty: str,
    user_answer: str,
) -> Dict[str, Any]:
    """
    Evaluates a user's interview answer using Gemini AI when available,
    or falls back to deterministic evaluation rules.
    Returns structured feedback without exposing chain-of-thought.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", "google_gemini")

    if gemini_key and gemini_key != "your_gemini_api_key_here" and ai_provider == "google_gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)

            prompt = f"""You are a senior technical interviewer evaluating a candidate's answer.

Question: {question_text}
Skill being tested: {skill_name}
Expected concepts: {expected_key_points}
Difficulty: {difficulty}
Candidate's answer: {user_answer}

Evaluate strictly based on the question and skill. Do NOT reward unrelated content.
Return ONLY a JSON object with these fields (no explanation, no markdown):

{{
  "score": <0-100 overall>,
  "correctness_score": <0-100>,
  "relevance_score": <0-100>,
  "technical_depth_score": <0-100>,
  "clarity_score": <0-100>,
  "strengths": "2-3 specific strengths",
  "weaknesses": "2-3 specific gaps or improvements needed",
  "improvement_suggestion": "concrete actionable improvement advice",
  "suggested_answer": "a concise model answer in 3-5 sentences"
}}"""

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
            data = json.loads(cleaned)

            required = {"score", "correctness_score", "relevance_score", "technical_depth_score",
                        "clarity_score", "strengths", "weaknesses", "improvement_suggestion", "suggested_answer"}
            if required.issubset(data.keys()):
                # Clamp all scores to 0-100
                for field in ["score", "correctness_score", "relevance_score", "technical_depth_score", "clarity_score"]:
                    if field in data:
                        data[field] = max(0.0, min(100.0, float(data[field])))
                data["topics_to_revise"] = expected_key_points[:100] if expected_key_points else skill_name
                return data

        except Exception as e:
            logger.warning(f"Gemini answer evaluation failed ({e}). Using deterministic fallback.")

    logger.info("Using deterministic answer evaluator.")
    return _evaluate_fallback_answer(question_text, skill_name, expected_key_points, difficulty, user_answer)


# ---------------------------------------------------------------------------
# Phase 9: AI & Fallback Project Recommendation Generator
# ---------------------------------------------------------------------------

def _generate_fallback_project_recommendations(
    target_role: Optional[str],
    experience_level: Optional[str],
    job_title: Optional[str],
    missing_skills: List[Any],
    weak_skills: List[Any],
) -> List[Dict[str, Any]]:
    """
    Deterministic fallback project recommendation generator.
    Generates 2-3 personalized project recommendations grounded in the user's actual skill gaps.
    """
    role_label = (target_role or job_title or "Software Engineer").strip()
    exp_level = (experience_level or "MID").strip().upper()
    
    diff_map = {"JUNIOR": "BEGINNER", "ENTRY": "BEGINNER", "MID": "INTERMEDIATE", "SENIOR": "ADVANCED", "LEAD": "ADVANCED"}
    base_diff = diff_map.get(exp_level, "INTERMEDIATE")

    # Extract skill objects/names
    missing_names: List[str] = []
    for item in (missing_skills or []):
        s_name = item.get("skill_name") if isinstance(item, dict) else str(item)
        if s_name and s_name not in missing_names:
            missing_names.append(s_name)

    weak_names: List[str] = []
    for item in (weak_skills or []):
        s_name = item.get("skill_name") if isinstance(item, dict) else str(item)
        if s_name and s_name not in weak_names and s_name not in missing_names:
            weak_names.append(s_name)

    all_target_skills = missing_names + weak_names

    if not all_target_skills:
        all_target_skills = ["Core Engineering Practices", "System Architecture", "Code Quality"]

    # Partition skills into 2-3 project bundles
    projects: List[Dict[str, Any]] = []

    # Bundle 1: Primary Missing Skills Capstone
    group1 = all_target_skills[:3]
    g1_str = ", ".join(group1)
    projects.append({
        "title": f"Grounded {group1[0]} & {role_label} Focus Capstone",
        "difficulty": base_diff,
        "skills_practiced": group1,
        "description": f"Build a practical {role_label} application centered around {g1_str}. Implement core business logic, input validation, robust error handling, and end-to-end integration.",
        "why_recommended": f"Directly addresses your primary missing skill gaps in {g1_str} required for the {role_label} position.",
        "estimated_hours": 12,
        "expected_outcome": f"A fully functional production-ready portfolio repository demonstrating applied proficiency in {g1_str}.",
        "resume_bullet": f"Designed and deployed a modular {role_label} application leveraging {g1_str}, featuring automated validation and persistent data storage."
    })

    # Bundle 2: Secondary & Partial Skills Synthesis
    if len(all_target_skills) > 1:
        group2 = all_target_skills[1:4] if len(all_target_skills) >= 4 else all_target_skills[::-1][:3]
        g2_str = ", ".join(group2)
        diff2 = "ADVANCED" if base_diff == "INTERMEDIATE" else base_diff
        projects.append({
            "title": f"Production Integration Suite ({g2_str})",
            "difficulty": diff2,
            "skills_practiced": group2,
            "description": f"Architect a multi-component integration project that exercises {g2_str}. Focus on clean architecture, performance optimization, and modular component interaction.",
            "why_recommended": f"Strengthens partial knowledge and missing secondary technical requirements in {g2_str}.",
            "estimated_hours": 15,
            "expected_outcome": f"An extensible service suite incorporating testing, structured logging, and clean API boundaries for {g2_str}.",
            "resume_bullet": f"Engineered an extensible integration service with {g2_str}, achieving robust error recovery and automated component testing."
        })

    # Bundle 3: Quality & Tooling Capstone (if 3+ target skills available)
    if len(all_target_skills) >= 3 or len(projects) < 3:
        group3 = [all_target_skills[-1]] + (all_target_skills[:2] if len(all_target_skills) > 2 else ["API Testing", "Containerization"])
        # Deduplicate
        group3_clean: List[str] = []
        for s in group3:
            if s not in group3_clean:
                group3_clean.append(s)
        g3_str = ", ".join(group3_clean)
        projects.append({
            "title": f"Full-Lifecycle {role_label} Utility",
            "difficulty": "INTERMEDIATE" if base_diff == "BEGINNER" else base_diff,
            "skills_practiced": group3_clean,
            "description": f"Develop a realistic CLI or micro-utility focusing on real-world workflows involving {g3_str}. Implement clean separation of concerns and clear documentation.",
            "why_recommended": f"Reinforces end-to-end practical execution using {g3_str} to round out your career readiness.",
            "estimated_hours": 10,
            "expected_outcome": f"A clean, documented open-source candidate project showcasing software engineering best practices with {g3_str}.",
            "resume_bullet": f"Built a full-lifecycle software utility with {g3_str}, implementing structured error handling and comprehensive documentation."
        })

    return projects[:3]


def generate_project_recommendations_ai(
    target_role: Optional[str],
    experience_level: Optional[str],
    job_title: Optional[str],
    job_requirements: List[Any],
    missing_skills: List[Any],
    weak_skills: List[Any],
) -> List[Dict[str, Any]]:
    """
    Generates 2-3 tailored project recommendations using Gemini AI when available,
    or falls back to deterministic rule-based generator.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    ai_provider = os.getenv("AI_PROVIDER", "google_gemini")

    if gemini_key and gemini_key != "your_gemini_api_key_here" and ai_provider == "google_gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)

            # Format skill context
            missing_str = ", ".join([s.get("skill_name", str(s)) if isinstance(s, dict) else str(s) for s in (missing_skills or [])])
            weak_str = ", ".join([s.get("skill_name", str(s)) if isinstance(s, dict) else str(s) for s in (weak_skills or [])])

            prompt = f"""You are an expert technical career mentor designing portfolio project recommendations for a candidate.

Target Role: {target_role or job_title or 'Software Engineer'}
Job Title: {job_title or target_role or 'Developer'}
Experience Level: {experience_level or 'MID'}

Candidate's Missing Skills (Highest Priority): {missing_str or 'None'}
Candidate's Partial/Weak Skills (Secondary Priority): {weak_str or 'None'}

Design EXACTLY 2 to 3 distinct, practical, portfolio-worthy project recommendations.
Each project MUST:
1. Target 2-4 complementary skills from the missing/weak skills list above.
2. Be realistically completable in 8-20 hours.
3. Match the candidate's experience level ({experience_level or 'MID'}).
4. Include a suggested resume bullet point template.

Return ONLY a JSON array containing 2 to 3 project objects with these exact keys:
[
  {{
    "title": "Project Title",
    "difficulty": "BEGINNER" | "INTERMEDIATE" | "ADVANCED",
    "skills_practiced": ["Skill1", "Skill2"],
    "description": "2-3 sentence overview of the project.",
    "why_recommended": "Explanation of why this project targets the candidate's missing/weak skills.",
    "estimated_hours": 12,
    "expected_outcome": "Description of final portfolio deliverable.",
    "resume_bullet": "Suggested resume bullet template (e.g. 'Built a ... using ... featuring ...')"
  }}
]"""

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
            data = json.loads(cleaned)

            if isinstance(data, list) and 1 <= len(data) <= 5:
                valid_projects = []
                for item in data:
                    if isinstance(item, dict) and "title" in item and "skills_practiced" in item:
                        # Ensure fields
                        item["difficulty"] = (item.get("difficulty") or "INTERMEDIATE").strip().upper()
                        if item["difficulty"] not in {"BEGINNER", "INTERMEDIATE", "ADVANCED"}:
                            item["difficulty"] = "INTERMEDIATE"
                        if not isinstance(item.get("skills_practiced"), list):
                            item["skills_practiced"] = [str(item.get("skills_practiced"))]
                        item["estimated_hours"] = max(1, int(item.get("estimated_hours", 10)))
                        valid_projects.append(item)
                
                if valid_projects:
                    logger.info(f"Successfully generated {len(valid_projects)} AI project recommendations via Gemini.")
                    return valid_projects[:3]

        except Exception as e:
            logger.warning(f"Gemini project recommendation generation failed ({e}). Using fallback.")

    logger.info("Using deterministic fallback project recommendation generator.")
    return _generate_fallback_project_recommendations(
        target_role=target_role,
        experience_level=experience_level,
        job_title=job_title,
        missing_skills=missing_skills,
        weak_skills=weak_skills,
    )

