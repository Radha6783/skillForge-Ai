import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { interviewAPI, jobAnalysisAPI } from '../services/api';
import {
  Mic, Brain, Target, Trophy, ChevronRight, ChevronLeft, CheckCircle2,
  AlertCircle, Briefcase, Zap, Clock, Star, TrendingUp, TrendingDown,
  RefreshCw, Map, List, Play, Award, BarChart2, MessageSquare, BookOpen,
  ArrowRight, Loader, Trash2, XCircle
} from 'lucide-react';

/* ──────────────────────────────────────────────────────────────────────────
   CONSTANTS
   ────────────────────────────────────────────────────────────────────────── */
const INTERVIEW_TYPES = [
  { value: 'TECHNICAL', label: 'Technical', icon: '⚙️', desc: 'Deep technical questions on required skills' },
  { value: 'BEHAVIORAL', label: 'Behavioral', icon: '🤝', desc: 'Situational and soft-skill questions' },
  { value: 'MIXED', label: 'Mixed', icon: '🎯', desc: 'Combination of technical and behavioral' },
];
const DIFFICULTIES = [
  { value: 'EASY', label: 'Easy', color: '#22c55e' },
  { value: 'MEDIUM', label: 'Medium', color: '#f59e0b' },
  { value: 'HARD', label: 'Hard', color: '#ef4444' },
];
const QUESTION_COUNTS = [5, 10, 15];

function scoreColor(score) {
  if (score >= 80) return '#22c55e';
  if (score >= 60) return '#f59e0b';
  if (score >= 40) return '#fb923c';
  return '#ef4444';
}

function readinessColor(level) {
  if (level === 'Strong') return '#22c55e';
  if (level === 'Good') return '#f59e0b';
  if (level === 'Needs Improvement') return '#fb923c';
  return '#ef4444';
}

function ScoreRing({ score, size = 100 }) {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  const color = scoreColor(score);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: 'block' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={10} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={color} strokeWidth={10}
        strokeDasharray={`${filled} ${circ}`}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dasharray 0.7s ease' }}
      />
      <text x="50%" y="54%" textAnchor="middle" fill={color}
        fontSize={size * 0.22} fontWeight="800" fontFamily="inherit">
        {Math.round(score)}
      </text>
    </svg>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   SETUP SCREEN
   ────────────────────────────────────────────────────────────────────────── */
function SetupScreen({ onStart }) {
  const [searchParams] = useSearchParams();
  const preselectedId = searchParams.get('job_analysis_id');

  const [jobAnalyses, setJobAnalyses] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(preselectedId ? parseInt(preselectedId) : '');
  const [interviewType, setInterviewType] = useState('MIXED');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [questionCount, setQuestionCount] = useState(5);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    jobAnalysisAPI.getHistory().then(data => {
      setJobAnalyses(Array.isArray(data) ? data : []);
    }).catch(() => setJobAnalyses([])).finally(() => setLoading(false));
  }, []);

  const selectedJob = jobAnalyses.find(j => j.id === parseInt(selectedJobId));

  const handleStart = async () => {
    if (!selectedJobId) { setError('Please select a job analysis.'); return; }
    setStarting(true); setError('');
    try {
      const session = await interviewAPI.startInterview({
        job_analysis_id: parseInt(selectedJobId),
        interview_type: interviewType,
        difficulty,
        question_count: questionCount,
      });
      onStart(session);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start interview. Please try again.');
    } finally {
      setStarting(false);
    }
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <div className="spinner" style={{ width: 32, height: 32, margin: '0 auto 1rem' }} />
      <p style={{ color: 'var(--text-muted)' }}>Loading your job analyses…</p>
    </div>
  );

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <div className="glass-card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid #818cf8' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--accent-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Mic size={24} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>AI Interview Simulator</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Personalized questions from your actual job analysis</p>
          </div>
        </div>

        {/* Job Analysis Selection */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
            <Briefcase size={14} style={{ marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Select Job Analysis
          </label>
          {jobAnalyses.length === 0 ? (
            <div className="alert alert-error">
              No job analyses found. <Link to="/job-analyzer" style={{ color: '#818cf8' }}>Analyze a job description first →</Link>
            </div>
          ) : (
            <select
              value={selectedJobId}
              onChange={e => setSelectedJobId(e.target.value)}
              style={{
                width: '100%', padding: '0.75rem 1rem', borderRadius: 10,
                background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)',
                color: 'var(--text-primary)', fontSize: '0.95rem', cursor: 'pointer',
              }}
            >
              <option value="">— Choose a job analysis —</option>
              {jobAnalyses.map(j => (
                <option key={j.id} value={j.id}>
                  {j.job_title}{j.company_name ? ` @ ${j.company_name}` : ''}
                </option>
              ))}
            </select>
          )}
          {selectedJob && (
            <div style={{ marginTop: '0.75rem', padding: '0.75rem 1rem', background: 'rgba(129,140,248,0.08)', borderRadius: 8, fontSize: '0.85rem', color: 'var(--text-secondary)', borderLeft: '3px solid #818cf8' }}>
              <strong style={{ color: '#818cf8' }}>{selectedJob.job_title}</strong>
              {selectedJob.company_name && <> at <strong>{selectedJob.company_name}</strong></>}
            </div>
          )}
        </div>

        {/* Interview Type */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            <Brain size={14} style={{ marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Interview Type
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
            {INTERVIEW_TYPES.map(t => (
              <button
                key={t.value}
                onClick={() => setInterviewType(t.value)}
                style={{
                  padding: '1rem 0.5rem', borderRadius: 10, border: '2px solid',
                  borderColor: interviewType === t.value ? '#818cf8' : 'var(--border-color)',
                  background: interviewType === t.value ? 'rgba(129,140,248,0.12)' : 'rgba(255,255,255,0.03)',
                  cursor: 'pointer', textAlign: 'center', transition: 'all 0.2s',
                  color: 'var(--text-primary)',
                }}
              >
                <div style={{ fontSize: '1.5rem', marginBottom: '0.3rem' }}>{t.icon}</div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{t.label}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{t.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Difficulty */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            <Zap size={14} style={{ marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Difficulty
          </label>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            {DIFFICULTIES.map(d => (
              <button
                key={d.value}
                onClick={() => setDifficulty(d.value)}
                style={{
                  flex: 1, padding: '0.75rem', borderRadius: 10, border: '2px solid',
                  borderColor: difficulty === d.value ? d.color : 'var(--border-color)',
                  background: difficulty === d.value ? `${d.color}18` : 'rgba(255,255,255,0.03)',
                  cursor: 'pointer', fontWeight: 700, color: difficulty === d.value ? d.color : 'var(--text-muted)',
                  transition: 'all 0.2s',
                }}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Question Count */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            <List size={14} style={{ marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Number of Questions
          </label>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            {QUESTION_COUNTS.map(c => (
              <button
                key={c}
                onClick={() => setQuestionCount(c)}
                style={{
                  flex: 1, padding: '0.75rem', borderRadius: 10, border: '2px solid',
                  borderColor: questionCount === c ? '#818cf8' : 'var(--border-color)',
                  background: questionCount === c ? 'rgba(129,140,248,0.12)' : 'rgba(255,255,255,0.03)',
                  cursor: 'pointer', fontWeight: 700,
                  color: questionCount === c ? '#818cf8' : 'var(--text-muted)',
                  transition: 'all 0.2s',
                }}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}><AlertCircle size={16} />{error}</div>}

        <button
          onClick={handleStart}
          disabled={starting || !selectedJobId || jobAnalyses.length === 0}
          className="btn-primary"
          style={{ width: '100%', padding: '1rem', fontSize: '1rem', justifyContent: 'center' }}
        >
          {starting ? <><span className="spinner" />Generating personalized questions…</> : <><Play size={18} /> Start Interview Simulator</>}
        </button>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   ACTIVE INTERVIEW SCREEN
   ────────────────────────────────────────────────────────────────────────── */
function ActiveInterview({ session, onFinish }) {
  const questions = [...(session.questions || [])].sort((a, b) => a.question_order - b.question_order);
  const [currentIdx, setCurrentIdx] = useState(() => {
    // Resume from last unanswered question
    const idx = questions.findIndex(q => !q.answer);
    return idx === -1 ? 0 : idx;
  });
  const [userAnswer, setUserAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [error, setError] = useState('');
  const [finishing, setFinishing] = useState(false);

  const currentQ = questions[currentIdx];
  const isLastQuestion = currentIdx === questions.length - 1;
  const answered = !!currentQ?.answer || !!evaluation;

  const wordCount = userAnswer.trim().split(/\s+/).filter(Boolean).length;

  const handleSubmit = async () => {
    if (!userAnswer.trim()) { setError('Please write your answer before submitting.'); return; }
    setSubmitting(true); setError('');
    try {
      const result = await interviewAPI.submitAnswer(session.id, {
        question_id: currentQ.id,
        user_answer: userAnswer.trim(),
      });
      setEvaluation(result);
    } catch (err) {
      const detail = err.response?.data?.detail || '';
      if (err.response?.status === 409) {
        setError('Session is already completed.');
      } else {
        setError(detail || 'Failed to submit answer. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    setEvaluation(null);
    setUserAnswer('');
    setError('');
    setCurrentIdx(i => i + 1);
  };

  const handleFinish = async () => {
    setFinishing(true);
    try {
      await interviewAPI.finishInterview(session.id);
      onFinish(session.id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to complete interview.');
      setFinishing(false);
    }
  };

  const typeColors = { TECHNICAL: '#818cf8', SCENARIO: '#a855f7', BEHAVIORAL: '#22c55e' };
  const typeColor = typeColors[currentQ?.question_type] || '#818cf8';

  return (
    <div style={{ maxWidth: 760, margin: '0 auto' }}>
      {/* Header */}
      <div className="glass-card" style={{ marginBottom: '1.2rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
              {session.target_role} · {session.interview_type} · {session.difficulty}
            </div>
            <div style={{ fontWeight: 800, fontSize: '1.1rem' }}>{session.topic}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#818cf8' }}>
              Q {currentIdx + 1} / {questions.length}
            </span>
            <div style={{ width: 120, height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3 }}>
              <div style={{
                width: `${((currentIdx + 1) / questions.length) * 100}%`,
                height: '100%', borderRadius: 3,
                background: 'linear-gradient(90deg, #818cf8, #a855f7)',
                transition: 'width 0.4s ease',
              }} />
            </div>
          </div>
        </div>
      </div>

      {/* Question Card */}
      <div className="glass-card" style={{ marginBottom: '1.2rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
          <span className="badge" style={{ background: `${typeColor}20`, color: typeColor, border: `1px solid ${typeColor}40` }}>
            {currentQ?.question_type || 'TECHNICAL'}
          </span>
          {currentQ?.skill_name && (
            <span className="badge badge-primary">{currentQ.skill_name}</span>
          )}
          <span className="badge" style={{
            background: currentQ?.difficulty === 'HARD' ? '#ef444420' : currentQ?.difficulty === 'EASY' ? '#22c55e20' : '#f59e0b20',
            color: currentQ?.difficulty === 'HARD' ? '#ef4444' : currentQ?.difficulty === 'EASY' ? '#22c55e' : '#f59e0b',
          }}>
            {currentQ?.difficulty || session.difficulty}
          </span>
        </div>
        <p style={{ fontSize: '1.1rem', lineHeight: 1.7, fontWeight: 600, color: 'var(--text-primary)' }}>
          {currentQ?.question_text}
        </p>
      </div>

      {/* Answer / Feedback */}
      {!answered ? (
        <div className="glass-card">
          <label style={{ display: 'block', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            <MessageSquare size={14} style={{ marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Your Answer
          </label>
          <textarea
            value={userAnswer}
            onChange={e => { setUserAnswer(e.target.value); setError(''); }}
            placeholder="Type your answer here. Be specific and use concrete examples where possible…"
            rows={6}
            style={{
              width: '100%', padding: '0.875rem', borderRadius: 10,
              background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)',
              color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: 1.6, resize: 'vertical',
              outline: 'none', fontFamily: 'inherit',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: wordCount > 50 ? '#22c55e' : 'var(--text-muted)' }}>
              {wordCount} word{wordCount !== 1 ? 's' : ''}
              {wordCount < 20 && wordCount > 0 && ' (try to be more detailed)'}
            </span>
            {error && <span style={{ color: '#ef4444', fontSize: '0.85rem' }}><AlertCircle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />{error}</span>}
          </div>
          <button
            onClick={handleSubmit}
            disabled={submitting || !userAnswer.trim()}
            className="btn-primary"
            style={{ marginTop: '1rem', width: '100%', justifyContent: 'center' }}
          >
            {submitting ? <><span className="spinner" />Evaluating your answer…</> : <><CheckCircle2 size={18} /> Submit Answer</>}
          </button>
        </div>
      ) : (
        <div className="glass-card">
          {/* Score row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <ScoreRing score={evaluation?.score ?? currentQ?.answer?.score ?? 0} size={90} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 800, fontSize: '1.15rem', marginBottom: '0.5rem' }}>Evaluation</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.4rem' }}>
                {[
                  ['Correctness', evaluation?.correctness_score ?? currentQ?.answer?.correctness_score],
                  ['Relevance', evaluation?.relevance_score ?? currentQ?.answer?.relevance_score],
                  ['Technical Depth', evaluation?.technical_depth_score ?? currentQ?.answer?.technical_depth_score],
                  ['Clarity', evaluation?.clarity_score ?? currentQ?.answer?.clarity_score],
                ].map(([label, val]) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                    <span style={{ fontWeight: 700, color: scoreColor(val ?? 0) }}>{Math.round(val ?? 0)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Strengths / Weaknesses */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
            <div style={{ padding: '0.875rem', borderRadius: 8, background: 'rgba(34,197,94,0.08)', borderLeft: '3px solid #22c55e' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#22c55e', marginBottom: '0.4rem' }}>
                <TrendingUp size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />Strengths
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                {evaluation?.strengths ?? currentQ?.answer?.strengths}
              </p>
            </div>
            <div style={{ padding: '0.875rem', borderRadius: 8, background: 'rgba(239,68,68,0.08)', borderLeft: '3px solid #ef4444' }}>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#ef4444', marginBottom: '0.4rem' }}>
                <TrendingDown size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />Weaknesses
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                {evaluation?.weaknesses ?? currentQ?.answer?.weaknesses}
              </p>
            </div>
          </div>

          <div style={{ padding: '0.875rem', borderRadius: 8, background: 'rgba(129,140,248,0.08)', borderLeft: '3px solid #818cf8', marginBottom: '0.75rem' }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#818cf8', marginBottom: '0.4rem' }}>
              <BookOpen size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />Improvement Suggestion
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              {evaluation?.improvement_suggestion ?? currentQ?.answer?.improvement_suggestion}
            </p>
          </div>

          <details style={{ marginBottom: '1rem' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-muted)', padding: '0.5rem 0' }}>
              📋 Model Answer
            </summary>
            <div style={{ padding: '0.875rem', borderRadius: 8, background: 'rgba(255,255,255,0.04)', marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {evaluation?.suggested_answer ?? currentQ?.answer?.suggested_answer}
            </div>
          </details>

          {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}><AlertCircle size={16} />{error}</div>}

          {isLastQuestion ? (
            <button
              onClick={handleFinish}
              disabled={finishing}
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {finishing ? <><span className="spinner" />Finishing interview…</> : <><Trophy size={18} /> View Final Results</>}
            </button>
          ) : (
            <button onClick={handleNext} className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
              Next Question <ChevronRight size={18} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   RESULTS SCREEN
   ────────────────────────────────────────────────────────────────────────── */
function ResultsScreen({ sessionId, onRetake }) {
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedQ, setExpandedQ] = useState(null);

  useEffect(() => {
    interviewAPI.getInterviewResults(sessionId).then(setResults).catch(err => {
      setError(err.response?.data?.detail || 'Failed to load results.');
    }).finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <div className="spinner" style={{ width: 32, height: 32, margin: '0 auto 1rem' }} />
      <p style={{ color: 'var(--text-muted)' }}>Computing your results…</p>
    </div>
  );
  if (error) return <div className="alert alert-error"><AlertCircle size={16} />{error}</div>;
  if (!results) return null;

  const rColor = readinessColor(results.readiness_level);

  return (
    <div style={{ maxWidth: 820, margin: '0 auto' }}>
      {/* Hero */}
      <div className="glass-card" style={{ marginBottom: '1.5rem', textAlign: 'center', borderLeft: `4px solid ${rColor}` }}>
        <div style={{ marginBottom: '1rem' }}>
          <Trophy size={40} color={rColor} style={{ marginBottom: '0.5rem' }} />
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.25rem' }}>Interview Complete!</h2>
          <p style={{ color: 'var(--text-muted)' }}>{results.target_role} · {results.interview_type} · {results.difficulty}</p>
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
          <ScoreRing score={results.overall_score} size={130} />
        </div>
        <div style={{ display: 'inline-block', padding: '0.5rem 1.5rem', borderRadius: 999, background: `${rColor}18`, border: `1px solid ${rColor}40`, color: rColor, fontWeight: 800, fontSize: '1rem', marginBottom: '0.75rem' }}>
          {results.readiness_level}
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{results.summary_feedback}</p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          <span><strong style={{ color: 'var(--text-primary)' }}>{results.answered_questions}</strong> answered</span>
          <span><strong style={{ color: 'var(--text-primary)' }}>{results.total_questions}</strong> total</span>
        </div>
      </div>

      {/* Skill Performance */}
      {results.skill_performance?.length > 0 && (
        <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart2 size={18} color="#818cf8" /> Skill Performance
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {results.skill_performance.map((sp, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem', fontSize: '0.875rem' }}>
                  <span style={{ fontWeight: 600 }}>{sp.skill_name}</span>
                  <span style={{ color: scoreColor(sp.average_score), fontWeight: 700 }}>{Math.round(sp.average_score)}/100 · {sp.performance_label}</span>
                </div>
                <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3 }}>
                  <div style={{ width: `${sp.average_score}%`, height: '100%', borderRadius: 3, background: `linear-gradient(90deg, ${scoreColor(sp.average_score)}, ${scoreColor(sp.average_score)}99)`, transition: 'width 0.7s ease' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Question Review */}
      <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <List size={18} color="#818cf8" /> Question Review
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {results.question_results?.map((qr, i) => (
            <div key={i} style={{ border: '1px solid var(--border-color)', borderRadius: 10, overflow: 'hidden' }}>
              <button
                onClick={() => setExpandedQ(expandedQ === i ? null : i)}
                style={{
                  width: '100%', padding: '0.875rem 1rem', background: 'rgba(255,255,255,0.03)',
                  border: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between',
                  alignItems: 'center', gap: '0.75rem', color: 'var(--text-primary)', textAlign: 'left',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8' }}>Q{qr.question_order}</span>
                    {qr.skill_name && <span className="badge badge-primary" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}>{qr.skill_name}</span>}
                    {!qr.answered && <span className="badge badge-warning" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem' }}>Not Answered</span>}
                  </div>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{qr.question_text.length > 90 ? qr.question_text.slice(0, 90) + '…' : qr.question_text}</span>
                </div>
                {qr.answered && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                    <span style={{ fontSize: '1rem', fontWeight: 800, color: scoreColor(qr.score ?? 0) }}>{Math.round(qr.score ?? 0)}</span>
                    <ChevronRight size={16} style={{ transform: expandedQ === i ? 'rotate(90deg)' : 'none', transition: '0.2s', color: 'var(--text-muted)' }} />
                  </div>
                )}
              </button>
              {expandedQ === i && qr.answered && (
                <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>Your Answer</div>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{qr.user_answer}</p>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
                    <div style={{ padding: '0.6rem 0.875rem', borderRadius: 8, background: 'rgba(34,197,94,0.08)', borderLeft: '3px solid #22c55e' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#22c55e', marginBottom: '0.25rem' }}>Strengths</div>
                      <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{qr.strengths}</p>
                    </div>
                    <div style={{ padding: '0.6rem 0.875rem', borderRadius: 8, background: 'rgba(239,68,68,0.08)', borderLeft: '3px solid #ef4444' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ef4444', marginBottom: '0.25rem' }}>Weaknesses</div>
                      <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{qr.weaknesses}</p>
                    </div>
                  </div>
                  <div style={{ padding: '0.6rem 0.875rem', borderRadius: 8, background: 'rgba(129,140,248,0.08)', borderLeft: '3px solid #818cf8' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8', marginBottom: '0.25rem' }}>Improvement</div>
                    <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{qr.improvement_suggestion}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <button onClick={onRetake} className="btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>
          <RefreshCw size={16} /> Retake Interview
        </button>
        <button onClick={() => navigate('/roadmaps')} className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
          <Map size={16} /> Review Recommended Roadmap
        </button>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   HISTORY SIDEBAR
   ────────────────────────────────────────────────────────────────────────── */
function InterviewHistory({ onResume, onNewInterview }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    interviewAPI.getInterviews().then(setSessions).catch(() => setSessions([])).finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this interview session?')) return;
    setDeletingId(id);
    try {
      await interviewAPI.deleteInterview(id);
      setSessions(prev => prev.filter(s => s.id !== id));
    } catch {}
    setDeletingId(null);
  };

  const statusColor = { IN_PROGRESS: '#f59e0b', COMPLETED: '#22c55e', NOT_STARTED: 'var(--text-muted)' };

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Mic size={20} color="#818cf8" /> Interview History
        </h2>
        <button onClick={onNewInterview} className="btn-primary">
          <Play size={16} /> New Interview
        </button>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '2rem' }}><div className="spinner" style={{ margin: '0 auto' }} /></div>}
      {!loading && sessions.length === 0 && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
          <Mic size={40} color="var(--text-muted)" style={{ marginBottom: '1rem', opacity: 0.5 }} />
          <p style={{ color: 'var(--text-muted)' }}>No interviews yet. Start your first simulation!</p>
          <button onClick={onNewInterview} className="btn-primary" style={{ marginTop: '1rem' }}>
            <Play size={16} /> Start Interview
          </button>
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {sessions.map(s => (
          <div
            key={s.id}
            className="glass-card"
            onClick={() => onResume(s)}
            style={{ cursor: 'pointer', padding: '1rem 1.25rem', transition: 'transform 0.15s', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem' }}
            onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseLeave={e => e.currentTarget.style.transform = ''}
          >
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
                <span className="badge badge-primary" style={{ fontSize: '0.72rem' }}>{s.interview_type}</span>
                <span className="badge" style={{ fontSize: '0.72rem', background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)' }}>{s.difficulty}</span>
                <span style={{ fontSize: '0.72rem', color: statusColor[s.status] || 'var(--text-muted)', fontWeight: 700 }}>● {s.status.replace('_', ' ')}</span>
              </div>
              <div style={{ fontWeight: 700 }}>{s.topic}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{s.target_role} · {s.total_questions} questions</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              {s.overall_score != null && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: scoreColor(s.overall_score) }}>{Math.round(s.overall_score)}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>score</div>
                </div>
              )}
              <button
                onClick={e => handleDelete(s.id, e)}
                disabled={deletingId === s.id}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '0.4rem' }}
              >
                {deletingId === s.id ? <span className="spinner" style={{ width: 14, height: 14 }} /> : <Trash2 size={16} />}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
   MAIN PAGE COMPONENT
   ────────────────────────────────────────────────────────────────────────── */
export default function InterviewSimulator() {
  const [searchParams] = useSearchParams();
  const [view, setView] = useState(() => searchParams.get('job_analysis_id') ? 'setup' : 'history');
  const [activeSession, setActiveSession] = useState(null);
  const [resultSessionId, setResultSessionId] = useState(null);

  const handleSessionStarted = (session) => {
    setActiveSession(session);
    setView('active');
  };

  const handleFinished = (sessionId) => {
    setResultSessionId(sessionId);
    setView('results');
  };

  const handleResume = (session) => {
    if (session.status === 'COMPLETED') {
      setResultSessionId(session.id);
      setView('results');
    } else {
      setActiveSession(session);
      setView('active');
    }
  };

  const handleRetake = () => {
    setActiveSession(null);
    setResultSessionId(null);
    setView('setup');
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', width: '100%' }}>
      {/* Page Title */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg, #818cf8, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Mic size={20} color="#fff" />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>
            Interview <span className="gradient-text">Simulator</span>
          </h1>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginLeft: '3.25rem' }}>
          AI-powered mock interviews personalized to your selected job analysis
        </p>
        {/* View Toggle */}
        {view !== 'active' && view !== 'results' && (
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.25rem', marginLeft: '3.25rem' }}>
            {[['setup', <><Play size={14} /> New Interview</>], ['history', <><List size={14} /> History</>]].map(([v, label]) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={view === v ? 'btn-primary' : 'btn-secondary'}
                style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {view === 'setup' && <SetupScreen onStart={handleSessionStarted} />}
      {view === 'active' && activeSession && <ActiveInterview session={activeSession} onFinish={handleFinished} />}
      {view === 'results' && resultSessionId && <ResultsScreen sessionId={resultSessionId} onRetake={handleRetake} />}
      {view === 'history' && <InterviewHistory onResume={handleResume} onNewInterview={() => setView('setup')} />}
    </div>
  );
}
