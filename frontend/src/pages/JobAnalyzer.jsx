import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { jobAnalysisAPI, skillGapAPI, roadmapAPI } from '../services/api';
import {
  FileSearch,
  Sparkles,
  Briefcase,
  Building,
  CheckCircle2,
  AlertCircle,
  Clock,
  Trash2,
  ChevronRight,
  Code,
  Database,
  Cloud,
  Wrench,
  UserCheck,
  BookOpen,
  Award,
  Layers,
  ArrowRight,
  Target,
  TrendingUp,
  AlertTriangle,
  XCircle,
  Zap,
  RefreshCw,
  Map
} from 'lucide-react';


const SAMPLE_JOB_DESCRIPTIONS = [
  {
    title: "Senior Full Stack Engineer",
    company: "TechScale Innovations",
    description: `We are looking for a Senior Full Stack Engineer to join our core product team.
Key Responsibilities:
- Design and implement scalable RESTful APIs using Python (FastAPI/Django) and Node.js.
- Architect modern single-page applications using React, TypeScript, and Tailwind CSS.
- Manage PostgreSQL databases, optimize complex queries, and handle Redis caching.
- Deploy and maintain containerized applications using Docker, Kubernetes, and AWS (EC2, S3, ECS).
- Implement automated CI/CD pipelines with GitHub Actions.

Requirements:
- 4+ years of full-stack software development experience.
- Bachelor's or Master's degree in Computer Science or Software Engineering.
- Strong proficiency in JavaScript/TypeScript, Python, and SQL.
- Experience with Git, Postman, Jest, and Agile team environments.
- Excellent communication and technical problem-solving skills.`
  },
  {
    title: "DevOps & Cloud Engineer",
    company: "CloudCore Systems",
    description: `CloudCore is seeking a DevOps Specialist to manage cloud infrastructure and automation.
Requirements:
- 3+ years managing AWS or GCP cloud architecture.
- Heavy hands-on experience with Terraform, Ansible, Docker, and Kubernetes (EKS).
- Proficiency in Python, Bash scripting, and SQL queries.
- Strong understanding of Linux system administration, Nginx, and network security.
- Experience setting up Prometheus, Grafana, and ELK monitoring stacks.`
  }
];

export default function JobAnalyzer() {
  const navigate = useNavigate();
  const [jobDescription, setJobDescription] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');

  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  // Phase 6: Skill Gap State
  const [skillGapReport, setSkillGapReport] = useState(null);
  const [loadingSkillGap, setLoadingSkillGap] = useState(false);
  const [gapError, setGapError] = useState(null);

  // Phase 7: Roadmap State
  const [generatingRoadmap, setGeneratingRoadmap] = useState(false);
  const [roadmapError, setRoadmapError] = useState(null);

  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);

  const handleGenerateRoadmap = async () => {
    if (!analysisResult?.id) return;
    setGeneratingRoadmap(true);
    setRoadmapError(null);
    try {
      const response = await roadmapAPI.generateRoadmap(analysisResult.id);
      if (response?.id) {
        navigate(`/roadmaps/${response.id}`);
      }
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Roadmap generation error:", err); }
      setRoadmapError(
        err.response?.data?.detail || err.message || "Failed to generate learning roadmap."
      );
    } finally {
      setGeneratingRoadmap(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await jobAnalysisAPI.getHistory();
      setHistory(data);
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Failed to load analysis history:", err); }
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (jobDescription.trim().length < 50) {
      setError("Job description must be at least 50 characters long.");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysisResult(null);
    setSkillGapReport(null);

    try {
      const response = await jobAnalysisAPI.analyzeJob({
        job_description: jobDescription,
        job_title: jobTitle || undefined,
        company_name: companyName || undefined,
      });

      setAnalysisResult(response);
      fetchHistory(); // Refresh history sidebar

      // Automatically trigger initial skill gap analysis for this job
      if (response?.id) {
        loadSkillGap(response.id);
      }
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Job analysis error:", err); }
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Failed to analyze job description. Please check your connection."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const loadSkillGap = async (jobAnalysisId) => {
    setLoadingSkillGap(true);
    setGapError(null);
    try {
      const report = await skillGapAPI.analyzeSkillGap(jobAnalysisId);
      setSkillGapReport(report);
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Failed to calculate skill gap:", err); }
      // Attempt fetching existing report
      try {
        const existing = await skillGapAPI.getSkillGapReport(jobAnalysisId);
        setSkillGapReport(existing);
      } catch (e) {
        setGapError("Could not calculate skill gap. Please try again.");
      }
    } finally {
      setLoadingSkillGap(false);
    }
  };

  const handleSelectHistoryItem = async (id) => {
    if (selectedHistoryId === id && analysisResult) return;
    setAnalyzing(true);
    setError(null);
    setSelectedHistoryId(id);
    setSkillGapReport(null);

    try {
      const detail = await jobAnalysisAPI.getAnalysisDetail(id);
      setAnalysisResult(detail);

      // Fetch or compute skill gap report
      loadSkillGap(id);
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Failed to load detail:", err); }
      setError("Could not load details for this analysis.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDeleteHistoryItem = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm("Delete this job analysis from history?")) return;

    try {
      await jobAnalysisAPI.deleteAnalysis(id);
      setHistory(prev => prev.filter(item => item.id !== id));
      if (analysisResult?.id === id) {
        setAnalysisResult(null);
        setSelectedHistoryId(null);
        setSkillGapReport(null);
      }
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Failed to delete analysis:", err); }
    }
  };

  const loadSample = (sample) => {
    setJobTitle(sample.title);
    setCompanyName(sample.company);
    setJobDescription(sample.description);
    setError(null);
  };

  const aiData = analysisResult?.analysis_result;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 320px', gap: '2rem', alignItems: 'start' }}>
      {/* Main Analysis Section */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        {/* Header Banner */}
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 18px rgba(168, 85, 247, 0.4)'
            }}>
              <FileSearch size={24} color="#ffffff" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>
                AI Job <span className="gradient-text">Analyzer & Skill Gap</span>
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Paste technical job listings, extract required competencies, and calculate your real career skill match.
              </p>
            </div>
          </div>
        </div>

        {/* Job Input Form */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <h3 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Briefcase size={18} color="var(--accent-primary)" /> Job Details & Description
            </h3>

            {/* Quick Sample Buttons */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', alignSelf: 'center' }}>Load Sample:</span>
              {SAMPLE_JOB_DESCRIPTIONS.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => loadSample(sample)}
                  className="btn-secondary"
                  style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                >
                  {sample.title}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleAnalyze} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Briefcase size={14} /> Optional Job Title
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Senior Backend Engineer"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Building size={14} /> Optional Company Name
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Google, Acme Inc."
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="form-label">
                Job Description Text <span style={{ color: 'var(--accent-rose)' }}>*</span>
              </label>
              <textarea
                className="form-input"
                rows={8}
                placeholder="Paste full job posting text here (responsibilities, required tech stack, qualifications)..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                style={{ resize: 'vertical', fontFamily: 'inherit' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <span>Minimum 50 characters required</span>
                <span>{jobDescription.length} characters</span>
              </div>
            </div>

            {error && (
              <div className="alert alert-error" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={18} /> {error}
              </div>
            )}

            <button
              type="submit"
              className="btn-primary"
              disabled={analyzing || jobDescription.trim().length < 50}
              style={{ padding: '0.85rem 1.5rem', fontSize: '1rem', justifyContent: 'center' }}
            >
              {analyzing ? (
                <>
                  <span className="spinner"></span> Analyzing Job Description with AI...
                </>
              ) : (
                <>
                  <Sparkles size={18} /> Analyze Job & Extract Skills
                </>
              )}
            </button>
          </form>
        </div>

        {/* Structured Results Display */}
        {analysisResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* Job Summary Banner */}
            <div className="glass-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <div className="badge badge-success" style={{ marginBottom: '0.5rem' }}>
                    <Layers size={13} /> {analysisResult.role_category || 'Software Engineering'}
                  </div>
                  <h2 style={{ fontSize: '1.6rem', fontWeight: '800' }}>
                    {analysisResult.job_title}
                  </h2>
                  {analysisResult.company_name && (
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                      <Building size={14} style={{ display: 'inline', marginRight: '4px' }} />
                      {analysisResult.company_name}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => loadSkillGap(analysisResult.id)}
                    className="btn-primary"
                    disabled={loadingSkillGap}
                    style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                  >
                    {loadingSkillGap ? (
                      <>
                        <span className="spinner"></span> Calculating Gap...
                      </>
                    ) : (
                      <>
                        <RefreshCw size={14} /> Refresh Skill Gap
                      </>
                    )}
                  </button>
                </div>
              </div>

              {aiData?.summary && (
                <p style={{ background: 'rgba(99, 102, 241, 0.08)', padding: '1rem', borderRadius: 'var(--radius-md)', color: '#e2e8f0', lineHeight: '1.6' }}>
                  <strong>AI Executive Summary:</strong> {aiData.summary}
                </p>
              )}
            </div>

            {/* PHASE 6: SKILL GAP ANALYSIS REPORT SECTION */}
            <div className="glass-card" style={{ borderLeft: '4px solid #10b981' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.4rem', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Target size={22} color="var(--accent-primary)" /> Career Match & Skill Gap Analysis
                  </h3>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    Evaluated against your active profile skills with weighted scoring.
                  </p>
                </div>

                {skillGapReport && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    padding: '0.75rem 1.25rem',
                    borderRadius: 'var(--radius-md)'
                  }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Career Match
                      </div>
                      <div style={{ fontSize: '1.8rem', fontWeight: '900', color: '#34d399' }}>
                        {skillGapReport.overall_match_percentage}%
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {loadingSkillGap ? (
                <div style={{ textAlign: 'center', padding: '2rem 0' }}>
                  <span className="spinner"></span>
                  <p style={{ marginTop: '0.75rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Comparing job requirements with your skills inventory...
                  </p>
                </div>
              ) : gapError ? (
                <div className="alert alert-error">
                  <AlertCircle size={18} /> {gapError}
                </div>
              ) : skillGapReport ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
                  
                  {/* Match Progress Bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Overall Role Readiness</span>
                      <span style={{ fontWeight: 'bold', color: '#34d399' }}>{skillGapReport.overall_match_percentage}%</span>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '10px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '5px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${Math.min(100, Math.max(0, skillGapReport.overall_match_percentage))}%`,
                        height: '100%',
                        background: 'linear-gradient(90deg, #6366f1, #10b981)',
                        borderRadius: '5px',
                        transition: 'width 0.6s ease'
                      }} />
                    </div>
                  </div>

                  {/* Stat Summary Pills */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                    <div style={{ padding: '0.85rem', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                      <div style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 'bold' }}>MATCHED SKILLS</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: '800' }}>{skillGapReport.matching_skills?.length || 0}</div>
                    </div>
                    <div style={{ padding: '0.85rem', borderRadius: 'var(--radius-md)', background: 'rgba(251, 191, 36, 0.08)', border: '1px solid rgba(251, 191, 36, 0.2)' }}>
                      <div style={{ fontSize: '0.8rem', color: '#fbbf24', fontWeight: 'bold' }}>PARTIAL GAPS</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: '800' }}>{skillGapReport.weak_skills?.length || 0}</div>
                    </div>
                    <div style={{ padding: '0.85rem', borderRadius: 'var(--radius-md)', background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.2)' }}>
                      <div style={{ fontSize: '0.8rem', color: '#f43f5e', fontWeight: 'bold' }}>MISSING SKILLS</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: '800' }}>{skillGapReport.missing_skills?.length || 0}</div>
                    </div>
                  </div>

                  {/* Prioritized Recommended Skills */}
                  {skillGapReport.recommended_skills?.length > 0 && (
                    <div style={{ background: 'rgba(99, 102, 241, 0.06)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
                      <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#818cf8' }}>
                        <Zap size={18} /> High-Impact Recommended Skills to Learn
                      </h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.9rem' }}>
                        Focusing on these missing and partial gap skills will yield the largest boost to your match rating:
                      </p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
                        {skillGapReport.recommended_skills.map((rec, idx) => (
                          <div
                            key={idx}
                            style={{
                              background: 'rgba(0, 0, 0, 0.3)',
                              padding: '0.5rem 0.85rem',
                              borderRadius: 'var(--radius-sm)',
                              border: rec.priority === 'HIGH' ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(251, 191, 36, 0.3)',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.5rem',
                              fontSize: '0.85rem'
                            }}
                          >
                            <span style={{ fontWeight: '600' }}>{rec.skill_name}</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                              ({rec.user_level} → {rec.required_level})
                            </span>
                            <span className={`badge ${rec.priority === 'HIGH' ? 'badge-error' : 'badge-warning'}`} style={{ fontSize: '0.7rem' }}>
                              {rec.priority}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Detailed Skill Comparison Lists */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.25rem' }}>
                    
                    {/* Partial Gaps */}
                    {skillGapReport.weak_skills?.length > 0 && (
                      <div>
                        <h4 style={{ fontSize: '1.05rem', marginBottom: '0.75rem', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <AlertTriangle size={18} /> Partial Proficiency Gaps ({skillGapReport.weak_skills.length})
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
                          {skillGapReport.weak_skills.map((item, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: '0.85rem',
                                borderRadius: 'var(--radius-md)',
                                background: 'rgba(251, 191, 36, 0.05)',
                                border: '1px solid rgba(251, 191, 36, 0.25)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.4rem'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>{item.skill_name}</span>
                                <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>PARTIAL GAP</span>
                              </div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Your Level: <span style={{ color: '#fbbf24', fontWeight: 'bold' }}>{item.user_level}</span> → Required: <span style={{ fontWeight: 'bold', color: '#e2e8f0' }}>{item.required_level}</span>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                <span>Gap Delta: -{item.gap_delta} level</span>
                                <span>Priority: {item.priority}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Skills */}
                    {skillGapReport.missing_skills?.length > 0 && (
                      <div>
                        <h4 style={{ fontSize: '1.05rem', marginBottom: '0.75rem', color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <XCircle size={18} /> Missing Required Skills ({skillGapReport.missing_skills.length})
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
                          {skillGapReport.missing_skills.map((item, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: '0.85rem',
                                borderRadius: 'var(--radius-md)',
                                background: 'rgba(244, 63, 94, 0.05)',
                                border: '1px solid rgba(244, 63, 94, 0.25)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.4rem'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>{item.skill_name}</span>
                                <span className="badge badge-error" style={{ fontSize: '0.7rem' }}>MISSING</span>
                              </div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Not in profile → Required: <span style={{ fontWeight: 'bold', color: '#e2e8f0' }}>{item.required_level}</span>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                <span>{item.is_required ? 'Mandatory Requirement' : 'Preferred'}</span>
                                <span>Priority: {item.priority}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Matched Skills */}
                    {skillGapReport.matching_skills?.length > 0 && (
                      <div>
                        <h4 style={{ fontSize: '1.05rem', marginBottom: '0.75rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <CheckCircle2 size={18} /> Fully Matched Competencies ({skillGapReport.matching_skills.length})
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
                          {skillGapReport.matching_skills.map((item, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: '0.85rem',
                                borderRadius: 'var(--radius-md)',
                                background: 'rgba(16, 185, 129, 0.05)',
                                border: '1px solid rgba(16, 185, 129, 0.25)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.4rem'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>{item.skill_name}</span>
                                <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>MATCHED</span>
                              </div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Your Level: <span style={{ color: '#34d399', fontWeight: 'bold' }}>{item.user_level}</span> (Req: {item.required_level})
                              </div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                Ready for role expectations
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>

                  {/* Phase 7: Roadmap Action CTA */}
                  <div style={{
                    marginTop: '1rem',
                    padding: '1.25rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.12) 100%)',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    textAlign: 'center'
                  }}>
                    <h4 style={{ fontSize: '1.1rem', fontWeight: '800', marginBottom: '0.4rem' }}>
                      Ready to Close Your Skill Gaps? 🚀
                    </h4>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem', maxWidth: '580px', margin: '0 auto 1rem' }}>
                      Generate an actionable week-by-week learning roadmap customized specifically to your missing and partial competencies for this role.
                    </p>

                    {roadmapError && (
                      <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                        <AlertCircle size={16} /> {roadmapError}
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        onClick={handleGenerateRoadmap}
                        className="btn-primary"
                        disabled={generatingRoadmap}
                        style={{ padding: '0.8rem 1.6rem', fontSize: '0.95rem' }}
                      >
                        {generatingRoadmap ? (
                          <>
                            <span className="spinner"></span> Crafting roadmap...
                          </>
                        ) : (
                          <>
                            <Map size={18} /> Generate Learning Roadmap
                          </>
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => navigate(`/project-recommendations/${analysisResult.id}`)}
                        className="btn-primary"
                        style={{
                          padding: '0.8rem 1.6rem',
                          fontSize: '0.95rem',
                          background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
                          boxShadow: '0 4px 15px rgba(6, 182, 212, 0.3)'
                        }}
                      >
                        🚀 Get Project Recommendations
                      </button>

                      <button
                        type="button"
                        onClick={() => navigate(`/interviews?job_analysis_id=${analysisResult.id}`)}
                        className="btn-secondary"
                        style={{ padding: '0.8rem 1.6rem', fontSize: '0.95rem' }}
                      >
                        🎙️ Simulate AI Interview
                      </button>
                    </div>
                  </div>

                </div>
              ) : (

                <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
                  <button
                    onClick={() => loadSkillGap(analysisResult.id)}
                    className="btn-primary"
                    style={{ margin: '0 auto' }}
                  >
                    <Target size={18} /> Analyze Skill Gap for this Role
                  </button>
                </div>
              )}
            </div>

            {/* Categorized Tech Stack */}
            {aiData && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.2rem' }}>
                
                {/* Languages */}
                {aiData.programming_languages?.length > 0 && (
                  <div className="glass-card">
                    <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#818cf8' }}>
                      <Code size={18} /> Programming Languages
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {aiData.programming_languages.map((item, idx) => (
                        <span key={idx} className="badge badge-primary">{item}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Frameworks */}
                {aiData.frameworks?.length > 0 && (
                  <div className="glass-card">
                    <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#a855f7' }}>
                      <Layers size={18} /> Frameworks & Libraries
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {aiData.frameworks.map((item, idx) => (
                        <span key={idx} className="badge badge-primary">{item}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Databases */}
                {aiData.databases?.length > 0 && (
                  <div className="glass-card">
                    <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399' }}>
                      <Database size={18} /> Databases & Storage
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {aiData.databases.map((item, idx) => (
                        <span key={idx} className="badge badge-success">{item}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cloud & DevOps */}
                {aiData.cloud_and_devops?.length > 0 && (
                  <div className="glass-card">
                    <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8' }}>
                      <Cloud size={18} /> Cloud & DevOps
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {aiData.cloud_and_devops.map((item, idx) => (
                        <span key={idx} className="badge badge-primary">{item}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Developer Tools */}
                {aiData.tools?.length > 0 && (
                  <div className="glass-card">
                    <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f43f5e' }}>
                      <Wrench size={18} /> Tools & Ecosystem
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {aiData.tools.map((item, idx) => (
                        <span key={idx} className="badge badge-secondary">{item}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Soft Skills */}
                {aiData.soft_skills?.length > 0 && (
                  <div className="glass-card">
                    <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fbbf24' }}>
                      <UserCheck size={18} /> Professional Soft Skills
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {aiData.soft_skills.map((item, idx) => (
                        <span key={idx} className="badge badge-secondary">{item}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Qualifications & Experience */}
            {(aiData?.experience_requirements?.length > 0 || aiData?.education_requirements?.length > 0) && (
              <div className="glass-card">
                <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Award size={18} color="var(--accent-primary)" /> Qualifications & Experience Requirements
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                  {aiData.experience_requirements?.length > 0 && (
                    <div>
                      <h5 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Experience Requirements</h5>
                      <ul style={{ listStyleType: 'disc', paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                        {aiData.experience_requirements.map((req, idx) => (
                          <li key={idx}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {aiData.education_requirements?.length > 0 && (
                    <div>
                      <h5 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Education & Credentials</h5>
                      <ul style={{ listStyleType: 'disc', paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                        {aiData.education_requirements.map((req, idx) => (
                          <li key={idx}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Extracted Requirements Table */}
            {analysisResult.requirements?.length > 0 && (
              <div className="glass-card">
                <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <BookOpen size={18} color="var(--accent-primary)" /> Extracted Skill Requirements Inventory ({analysisResult.requirements.length})
                </h3>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '0.75rem' }}>Skill Name</th>
                        <th style={{ padding: '0.75rem' }}>Category</th>
                        <th style={{ padding: '0.75rem' }}>Requirement Type</th>
                        <th style={{ padding: '0.75rem' }}>Importance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysisResult.requirements.map((req) => (
                        <tr key={req.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          <td style={{ padding: '0.75rem', fontWeight: '600' }}>{req.skill_name}</td>
                          <td style={{ padding: '0.75rem', color: 'var(--text-secondary)' }}>{req.category || 'Technical'}</td>
                          <td style={{ padding: '0.75rem' }}>
                            {req.is_required ? (
                              <span className="badge badge-success" style={{ fontSize: '0.75rem' }}>Required</span>
                            ) : (
                              <span className="badge badge-secondary" style={{ fontSize: '0.75rem' }}>Preferred</span>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{req.importance_level}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

          </div>
        )}
      </div>

      {/* History Sidebar */}
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Clock size={18} color="var(--accent-primary)" /> Analysis History
        </h3>

        {loadingHistory ? (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <span className="spinner"></span>
          </div>
        ) : history.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem 0' }}>
            No past job analyses found. Submit a job description to get started!
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '600px', overflowY: 'auto' }}>
            {history.map((item) => (
              <div
                key={item.id}
                onClick={() => handleSelectHistoryItem(item.id)}
                style={{
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-md)',
                  background: analysisResult?.id === item.id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                  border: analysisResult?.id === item.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                  <h5 style={{ fontSize: '0.9rem', fontWeight: '700', paddingRight: '1.5rem' }}>
                    {item.job_title}
                  </h5>
                  <button
                    onClick={(e) => handleDeleteHistoryItem(e, item.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      position: 'absolute',
                      top: '0.75rem',
                      right: '0.75rem'
                    }}
                    title="Delete record"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                {item.company_name && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                    {item.company_name}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  <ChevronRight size={14} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
