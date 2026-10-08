import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { careerReadinessAPI, authAPI } from '../services/api';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip
} from 'recharts';
import {
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Map,
  Sparkles,
  Mic,
  FolderKanban,
  Zap,
  Award,
  BookOpen,
  Layers,
  ChevronDown
} from 'lucide-react';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [targetRoles, setTargetRoles] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [error, setError] = useState('');

  // Diagnostic auth tester state
  const [meData, setMeData] = useState(null);
  const [loadingMe, setLoadingMe] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Fetch user's analyzed jobs list
      const roles = await careerReadinessAPI.getTargetRoles().catch(() => []);
      setTargetRoles(roles || []);

      // 2. Fetch career readiness (default to latest or first)
      const data = await careerReadinessAPI.getReadiness();
      setReadiness(data);
      if (data?.job_analysis_id) {
        setSelectedJobId(data.job_analysis_id);
      } else if (roles?.length > 0) {
        setSelectedJobId(roles[0].id);
      }
    } catch (err) {
      if (import.meta.env.DEV) { console.error('Failed to load dashboard data:', err); }
      setError(err.response?.data?.detail || 'Failed to load career readiness data.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (e) => {
    const jobId = e.target.value ? parseInt(e.target.value, 10) : null;
    setSelectedJobId(jobId);
    if (!jobId) return;

    setLoading(true);
    setError('');
    try {
      const data = await careerReadinessAPI.getReadinessForJob(jobId);
      setReadiness(data);
    } catch (err) {
      if (import.meta.env.DEV) { console.error('Failed to load job-specific readiness:', err); }
      setError(err.response?.data?.detail || 'Failed to load readiness for selected role.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchMe = async () => {
    setLoadingMe(true);
    try {
      const data = await authAPI.getMe();
      setMeData(data);
    } catch (err) {
      if (import.meta.env.DEV) { console.error('Failed to fetch me data:', err); }
    } finally {
      setLoadingMe(false);
    }
  };

  // Helper for Tier Badge colors
  const getTierBadgeStyle = (tier) => {
    if (tier?.includes('JOB READY')) {
      return { background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' };
    }
    if (tier?.includes('COMPETITIVE')) {
      return { background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', border: '1px solid rgba(6, 182, 212, 0.3)' };
    }
    if (tier?.includes('IN TRAINING')) {
      return { background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' };
    }
    return { background: 'rgba(244, 63, 94, 0.15)', color: '#fb7185', border: '1px solid rgba(244, 63, 94, 0.3)' };
  };

  // Prepare radar chart data from the 4 pillars
  const radarData = readiness?.pillars
    ? [
        { subject: 'Skills (35%)', score: readiness.pillars.skill_readiness.score, fullMark: 100 },
        { subject: 'Roadmap (25%)', score: readiness.pillars.roadmap_progress.score, fullMark: 100 },
        { subject: 'Interview (25%)', score: readiness.pillars.interview_readiness.score, fullMark: 100 },
        { subject: 'Portfolio (15%)', score: readiness.pillars.portfolio_readiness.score, fullMark: 100 },
      ]
    : [];

  return (
    <div style={{ maxWidth: '1080px', margin: '2rem auto', width: '100%', padding: '0 1rem' }}>
      {/* 1. Top Header & User Banner */}
      <div className="glass-card" style={{ marginBottom: '2rem', backdropFilter: 'blur(16px)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '0.35rem' }}>
              <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>
                Welcome back, <span className="gradient-text">{user?.email?.split('@')[0]}</span>!
              </h2>
              <span className={`badge ${user?.role === 'ADMIN' ? 'badge-warning' : 'badge-success'}`}>
                {user?.role || 'STUDENT'}
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              Unified Career Readiness & Intelligence Dashboard
            </p>
          </div>

          {/* Target Role Dropdown Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            {targetRoles.length > 0 && (
              <div style={{ position: 'relative', minWidth: '220px' }}>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.2rem', fontWeight: 600, textTransform: 'uppercase' }}>
                  Target Job Focus
                </label>
                <select
                  value={selectedJobId || ''}
                  onChange={handleRoleChange}
                  disabled={loading}
                  style={{
                    width: '100%',
                    padding: '0.55rem 2rem 0.55rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(15, 23, 42, 0.85)',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    color: '#f8fafc',
                    fontSize: '0.88rem',
                    fontWeight: 600,
                    outline: 'none',
                    appearance: 'none',
                    cursor: 'pointer'
                  }}
                >
                  {targetRoles.map((role) => (
                    <option key={role.id} value={role.id} style={{ background: '#0f172a', color: '#fff' }}>
                      {role.target_role || role.job_title}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} color="var(--accent-primary)" style={{ position: 'absolute', right: '0.75rem', bottom: '0.75rem', pointerEvents: 'none' }} />
              </div>
            )}

            <button onClick={logout} className="btn-secondary" style={{ color: 'var(--accent-rose)', borderColor: 'rgba(244,63,94,0.3)', padding: '0.55rem 0.9rem', fontSize: '0.85rem' }}>
              Logout 🚪
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {loading ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 1rem' }}></div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>Calculating multi-pillar Career Readiness metrics...</p>
        </div>
      ) : !readiness?.has_target_job ? (
        /* Empty State: No Target Job Analyzed */
        <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem' }}>
          <Sparkles size={44} color="var(--accent-primary)" style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.5rem' }}>No Target Job Analyzed Yet</h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0 auto 1.5rem', fontSize: '0.95rem' }}>
            Submit a target job description to calculate your personalized 4-pillar Career Readiness score and generate custom learning milestones!
          </p>
          <Link to="/job-analyzer" className="btn-primary" style={{ display: 'inline-flex', padding: '0.8rem 2rem', fontSize: '1rem' }}>
            Analyze Your First Job <ArrowRight size={18} />
          </Link>
        </div>
      ) : (
        <>
          {/* 2. HERO CAREER READINESS SCORE CARD */}
          <div
            className="glass-card"
            style={{
              marginBottom: '2rem',
              background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 27, 75, 0.85) 50%, rgba(15, 23, 42, 0.95) 100%)',
              border: '1px solid rgba(99, 102, 241, 0.35)',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
              <div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                  <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontWeight: 700 }}>
                    CAREER READINESS
                  </span>
                  <span className="badge" style={getTierBadgeStyle(readiness.tier)}>
                    {readiness.tier}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.4rem' }}>
                  Target Role: <span className="gradient-text">{readiness.target_role || readiness.job_title}</span>
                </h3>

                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '580px', lineHeight: '1.5' }}>
                  {readiness.points_to_next_tier != null
                    ? `You are currently ${readiness.points_to_next_tier} points away from Job Ready status for this position.`
                    : readiness.tier_description}
                </p>
              </div>

              {/* Radial Big Score Badge */}
              <div style={{
                textAlign: 'center',
                padding: '1.5rem 2rem',
                borderRadius: 'var(--radius-lg)',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                minWidth: '160px'
              }}>
                <div style={{
                  fontSize: '3rem',
                  fontWeight: 900,
                  lineHeight: '1',
                  background: readiness.overall_score >= 85 ? 'linear-gradient(135deg, #34d399, #10b981)' : (readiness.overall_score >= 65 ? 'linear-gradient(135deg, #38bdf8, #6366f1)' : 'linear-gradient(135deg, #fbbf24, #f43f5e)'),
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  marginBottom: '0.2rem'
                }}>
                  {readiness.overall_score}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  out of 100
                </div>
              </div>
            </div>
          </div>

          {/* 3. RADAR CHART & NEXT BEST ACTION SECTION */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            {/* Competency Radar Chart */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem', alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={16} color="var(--accent-primary)" /> 4-Pillar Competency Radar
              </h4>
              <div style={{ width: '100%', height: '240px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                    <PolarGrid stroke="rgba(255, 255, 255, 0.15)" />
                    <PolarAngleAxis dataKey="subject" stroke="#94a3b8" tick={{ fill: '#cbd5e1', fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="rgba(255, 255, 255, 0.2)" tick={{ fill: '#64748b', fontSize: 10 }} />
                    <Radar name="Readiness" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.45} />
                    <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Next Best Action Card */}
            {readiness.next_best_action && (
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', borderLeft: '4px solid #6366f1' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <Zap size={18} color="#818cf8" />
                    <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontSize: '0.75rem' }}>
                      RECOMMENDED NEXT ACTION
                    </span>
                  </div>
                  <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem', color: '#f8fafc' }}>
                    Highest-Impact Milestone
                  </h4>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {readiness.next_best_action.action_text}
                  </p>
                </div>

                {readiness.next_best_action.destination && (
                  <div style={{ marginTop: '1.25rem' }}>
                    <Link
                      to={readiness.next_best_action.destination}
                      className="btn-primary"
                      style={{ padding: '0.65rem 1.4rem', fontSize: '0.88rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                      Take Action Now <ArrowRight size={15} />
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 4. FOUR PILLARS GRID */}
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={18} color="var(--accent-primary)" /> Score Pillar Breakdown (100% Total)
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
            {/* Pillar 1: Skill Readiness */}
            <div className="glass-card" style={{ borderTop: '3px solid #38bdf8' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                  1. Skill Match (35%)
                </span>
                <span className={`badge ${readiness.pillars.skill_readiness.status === 'COMPLETED' ? 'badge-success' : 'badge-secondary'}`} style={{ fontSize: '0.7rem' }}>
                  {readiness.pillars.skill_readiness.status}
                </span>
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>
                {readiness.pillars.skill_readiness.score}%
              </div>
              {/* Progress bar */}
              <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.75rem' }}>
                <div style={{ width: `${readiness.pillars.skill_readiness.score}%`, height: '100%', background: 'linear-gradient(90deg, #06b6d4, #38bdf8)', borderRadius: '3px' }}></div>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                {readiness.pillars.skill_readiness.action_cta}
              </p>
              <Link to="/job-analyzer" style={{ fontSize: '0.8rem', color: '#38bdf8', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                View Skill Gap <ArrowRight size={12} />
              </Link>
            </div>

            {/* Pillar 2: Roadmap Progress */}
            <div className="glass-card" style={{ borderTop: '3px solid #818cf8' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase' }}>
                  2. Learning Roadmap (25%)
                </span>
                <span className={`badge ${readiness.pillars.roadmap_progress.status === 'COMPLETED' ? 'badge-success' : 'badge-secondary'}`} style={{ fontSize: '0.7rem' }}>
                  {readiness.pillars.roadmap_progress.status}
                </span>
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>
                {readiness.pillars.roadmap_progress.score}%
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.75rem' }}>
                <div style={{ width: `${readiness.pillars.roadmap_progress.score}%`, height: '100%', background: 'linear-gradient(90deg, #6366f1, #818cf8)', borderRadius: '3px' }}></div>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                {readiness.pillars.roadmap_progress.action_cta}
              </p>
              <Link to="/roadmaps" style={{ fontSize: '0.8rem', color: '#818cf8', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                Open Roadmap <ArrowRight size={12} />
              </Link>
            </div>

            {/* Pillar 3: Interview Readiness */}
            <div className="glass-card" style={{ borderTop: '3px solid #c084fc' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#c084fc', textTransform: 'uppercase' }}>
                  3. Interview Mastery (25%)
                </span>
                <span className={`badge ${readiness.pillars.interview_readiness.status === 'COMPLETED' ? 'badge-success' : 'badge-secondary'}`} style={{ fontSize: '0.7rem' }}>
                  {readiness.pillars.interview_readiness.status}
                </span>
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>
                {readiness.pillars.interview_readiness.score}%
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.75rem' }}>
                <div style={{ width: `${readiness.pillars.interview_readiness.score}%`, height: '100%', background: 'linear-gradient(90deg, #a855f7, #c084fc)', borderRadius: '3px' }}></div>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                {readiness.pillars.interview_readiness.action_cta}
              </p>
              <Link to="/interviews" style={{ fontSize: '0.8rem', color: '#c084fc', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                Simulate Interview <ArrowRight size={12} />
              </Link>
            </div>

            {/* Pillar 4: Portfolio Readiness */}
            <div className="glass-card" style={{ borderTop: '3px solid #34d399' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>
                  4. Portfolio Projects (15%)
                </span>
                <span className={`badge ${readiness.pillars.portfolio_readiness.status === 'COMPLETED' ? 'badge-success' : 'badge-secondary'}`} style={{ fontSize: '0.7rem' }}>
                  {readiness.pillars.portfolio_readiness.status}
                </span>
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>
                {readiness.pillars.portfolio_readiness.score}%
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.75rem' }}>
                <div style={{ width: `${readiness.pillars.portfolio_readiness.score}%`, height: '100%', background: 'linear-gradient(90deg, #10b981, #34d399)', borderRadius: '3px' }}></div>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                {readiness.pillars.portfolio_readiness.action_cta}
              </p>
              <Link
                to={readiness.job_analysis_id ? `/project-recommendations/${readiness.job_analysis_id}` : '/job-analyzer'}
                style={{ fontSize: '0.8rem', color: '#34d399', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
              >
                View Projects <ArrowRight size={12} />
              </Link>
            </div>
          </div>

          {/* 5. FORMULA BREAKDOWN / TRANSPARENCY CARD */}
          <div className="glass-card" style={{ marginBottom: '2rem', background: 'rgba(0,0,0,0.25)' }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              📐 Transparent Score Calculation
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <div>
                Skill Points: <strong style={{ color: '#38bdf8' }}>{readiness.formula_breakdown?.skill_points}</strong> pts ({readiness.pillars.skill_readiness.score} × 35%)
              </div>
              <div>+</div>
              <div>
                Roadmap Points: <strong style={{ color: '#818cf8' }}>{readiness.formula_breakdown?.roadmap_points}</strong> pts ({readiness.pillars.roadmap_progress.score} × 25%)
              </div>
              <div>+</div>
              <div>
                Interview Points: <strong style={{ color: '#c084fc' }}>{readiness.formula_breakdown?.interview_points}</strong> pts ({readiness.pillars.interview_readiness.score} × 25%)
              </div>
              <div>+</div>
              <div>
                Portfolio Points: <strong style={{ color: '#34d399' }}>{readiness.formula_breakdown?.portfolio_points}</strong> pts ({readiness.pillars.portfolio_readiness.score} × 15%)
              </div>
              <div>=</div>
              <div>
                Total: <strong style={{ color: '#fff', fontSize: '0.95rem' }}>{readiness.overall_score} / 100</strong>
              </div>
            </div>
          </div>
        </>
      )}

      {/* 6. Diagnostic Test Me Inspector (Preserved) */}
      <div className="glass-card" style={{ marginTop: '1rem' }}>
        <button onClick={handleFetchMe} className="btn-secondary" disabled={loadingMe} style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>
          {loadingMe ? <span className="spinner"></span> : 'Inspect /api/auth/me Session'}
        </button>

        {meData && (
          <div style={{ marginTop: '0.75rem', background: 'rgba(0,0,0,0.3)', padding: '0.8rem', borderRadius: 'var(--radius-md)' }}>
            <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#a7f3d0', overflowX: 'auto', margin: 0 }}>
              {JSON.stringify(meData, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
