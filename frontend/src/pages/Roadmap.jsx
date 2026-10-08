import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { roadmapAPI } from '../services/api';
import {
  Map,
  CheckCircle2,
  Circle,
  Clock,
  BookOpen,
  Code,
  Briefcase,
  Layers,
  ChevronRight,
  Trash2,
  AlertCircle,
  Calendar,
  Sparkles,
  ArrowRight,
  Flame,
  Zap
} from 'lucide-react';

export default function Roadmap() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [roadmaps, setRoadmaps] = useState([]);
  const [activeRoadmap, setActiveRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingItemId, setUpdatingItemId] = useState(null);

  useEffect(() => {
    fetchRoadmaps();
  }, [id]);

  const fetchRoadmaps = async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await roadmapAPI.getRoadmaps();
      setRoadmaps(list);

      if (id) {
        const detail = await roadmapAPI.getRoadmap(id);
        setActiveRoadmap(detail);
      } else if (list.length > 0) {
        // Load the first (most recent) roadmap
        const detail = await roadmapAPI.getRoadmap(list[0].id);
        setActiveRoadmap(detail);
      } else {
        setActiveRoadmap(null);
      }
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Failed to load roadmaps:", err); }
      setError(
        err.response?.data?.detail || err.message || "Failed to load learning roadmaps."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleToggleItem = async (item) => {
    if (!activeRoadmap) return;
    const newStatus = !item.is_completed;
    setUpdatingItemId(item.id);

    try {
      const updatedItem = await roadmapAPI.updateRoadmapItem(
        activeRoadmap.id,
        item.id,
        newStatus
      );

      // Update local state immediately
      setActiveRoadmap((prev) => {
        if (!prev) return prev;
        const newItems = prev.items.map((it) =>
          it.id === item.id ? { ...it, ...updatedItem } : it
        );
        const comp = newItems.filter((it) => it.is_completed).length;
        const tot = newItems.length;
        const pct = tot > 0 ? Math.round((comp / tot) * 1000) / 10 : 0;
        return {
          ...prev,
          items: newItems,
          completed_items: comp,
          completion_percentage: pct,
        };
      });

      // Update in roadmaps sidebar list
      setRoadmaps((prev) =>
        prev.map((r) => {
          if (r.id === activeRoadmap.id) {
            const comp = r.completed_items + (newStatus ? 1 : -1);
            const pct = r.total_items > 0 ? Math.round((comp / r.total_items) * 1000) / 10 : 0;
            return { ...r, completed_items: comp, completion_percentage: pct };
          }
          return r;
        })
      );
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Failed to toggle item completion:", err); }
      alert("Could not update item status. Please try again.");
    } finally {
      setUpdatingItemId(null);
    }
  };

  const handleDeleteRoadmap = async (roadmapId) => {
    if (!window.confirm("Are you sure you want to delete this learning roadmap?")) return;
    try {
      await roadmapAPI.deleteRoadmap(roadmapId);
      const remaining = roadmaps.filter((r) => r.id !== roadmapId);
      setRoadmaps(remaining);
      if (activeRoadmap?.id === roadmapId) {
        if (remaining.length > 0) {
          navigate(`/roadmaps/${remaining[0].id}`);
        } else {
          setActiveRoadmap(null);
          navigate('/roadmaps');
        }
      }
    } catch (err) {
      if (import.meta.env.DEV) { console.error("Failed to delete roadmap:", err); }
      alert("Failed to delete roadmap.");
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0' }}>
        <span className="spinner"></span>
        <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Loading personalized learning roadmap...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: '2rem', alignItems: 'start' }}>
      
      {/* Main Roadmap Area */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        {/* Banner Header */}
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 18px rgba(59, 130, 246, 0.4)'
            }}>
              <Map size={24} color="#ffffff" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>
                Personalized <span className="gradient-text">Learning Roadmap</span>
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Custom week-by-week curriculum structured to close your verified technical skill gaps.
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="alert alert-error">
            <AlertCircle size={18} /> {error}
          </div>
        )}

        {!activeRoadmap ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem' }}>
            <Sparkles size={40} color="var(--accent-primary)" style={{ margin: '0 auto 1rem' }} />
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>No Active Learning Roadmap</h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '500px', margin: '0 auto 1.5rem', fontSize: '0.95rem' }}>
              Analyze a target job posting and run Skill Gap Analysis to generate your customized accelerated learning roadmap!
            </p>
            <Link to="/job-analyzer" className="btn-primary" style={{ display: 'inline-flex', padding: '0.75rem 1.75rem' }}>
              Go to Job Analyzer <ArrowRight size={16} />
            </Link>
          </div>
        ) : (
          <>
            {/* Active Roadmap Overview Card */}
            <div className="glass-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
                <div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                    <span className="badge badge-primary">
                      <Briefcase size={12} /> {activeRoadmap.target_role}
                    </span>
                    <span className="badge badge-secondary">
                      <Calendar size={12} /> {activeRoadmap.total_weeks} Weeks Plan
                    </span>
                  </div>
                  <h2 style={{ fontSize: '1.6rem', fontWeight: '800' }}>
                    {activeRoadmap.title}
                  </h2>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  {activeRoadmap.job_analysis_id && (
                    <Link
                      to={`/project-recommendations/${activeRoadmap.job_analysis_id}`}
                      className="btn-secondary"
                      style={{
                        padding: '0.45rem 0.85rem',
                        fontSize: '0.8rem',
                        color: 'var(--accent-cyan)',
                        borderColor: 'rgba(6, 182, 212, 0.4)',
                        textDecoration: 'none'
                      }}
                    >
                      🚀 Recommended Projects
                    </Link>
                  )}
                  <button
                    onClick={() => handleDeleteRoadmap(activeRoadmap.id)}
                    className="btn-secondary"
                    style={{ color: 'var(--accent-rose)', borderColor: 'rgba(244, 63, 94, 0.3)', padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
                    title="Delete Roadmap"
                  >
                    <Trash2 size={14} /> Delete
                  </button>
                </div>
              </div>

              {activeRoadmap.description && (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6', marginBottom: '1.5rem' }}>
                  {activeRoadmap.description}
                </p>
              )}

              {/* Progress Bar & Counters */}
              <div style={{
                background: 'rgba(0, 0, 0, 0.25)',
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: '600', color: '#e2e8f0' }}>
                    Curriculum Progress: {activeRoadmap.completed_items} of {activeRoadmap.total_items} Phases Completed
                  </span>
                  <span style={{ fontSize: '1.2rem', fontWeight: '800', color: '#34d399' }}>
                    {activeRoadmap.completion_percentage}%
                  </span>
                </div>

                <div style={{
                  width: '100%',
                  height: '10px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '5px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${Math.min(100, Math.max(0, activeRoadmap.completion_percentage))}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #6366f1, #10b981)',
                    borderRadius: '5px',
                    transition: 'width 0.5s ease'
                  }} />
                </div>
              </div>
            </div>

            {/* Weekly Phases Timeline */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={20} color="var(--accent-primary)" /> Weekly Learning Modules ({activeRoadmap.items?.length || 0})
              </h3>

              {activeRoadmap.items?.map((item) => (
                <div
                  key={item.id}
                  className="glass-card"
                  style={{
                    borderLeft: item.is_completed ? '4px solid #10b981' : '4px solid rgba(99, 102, 241, 0.4)',
                    background: item.is_completed ? 'rgba(16, 185, 129, 0.04)' : 'rgba(255, 255, 255, 0.02)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {/* Item Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                      <span style={{
                        padding: '0.3rem 0.75rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--accent-gradient)',
                        fontSize: '0.75rem',
                        fontWeight: '800',
                        color: '#ffffff'
                      }}>
                        WEEK {item.week_number}
                      </span>

                      {item.skill_name && (
                        <span className="badge badge-primary" style={{ fontSize: '0.8rem' }}>
                          <Code size={12} /> {item.skill_name}
                        </span>
                      )}

                      <span className={`badge ${item.priority === 'HIGH' ? 'badge-error' : item.priority === 'MEDIUM' ? 'badge-warning' : 'badge-secondary'}`} style={{ fontSize: '0.75rem' }}>
                        {item.priority || 'MEDIUM'} PRIORITY
                      </span>

                      {item.estimated_hours && (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <Clock size={12} /> {item.estimated_hours} Hours
                        </span>
                      )}
                    </div>

                    {/* Interactive Completion Button */}
                    <button
                      onClick={() => handleToggleItem(item)}
                      disabled={updatingItemId === item.id}
                      style={{
                        background: item.is_completed ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                        border: item.is_completed ? '1px solid #10b981' : '1px solid var(--border-color)',
                        color: item.is_completed ? '#34d399' : 'var(--text-muted)',
                        padding: '0.45rem 0.9rem',
                        borderRadius: 'var(--radius-md)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {updatingItemId === item.id ? (
                        <span className="spinner" style={{ width: '14px', height: '14px' }}></span>
                      ) : item.is_completed ? (
                        <>
                          <CheckCircle2 size={16} color="#34d399" /> Completed
                        </>
                      ) : (
                        <>
                          <Circle size={16} /> Mark Complete
                        </>
                      )}
                    </button>
                  </div>

                  {/* Topic Title */}
                  <h4 style={{
                    fontSize: '1.2rem',
                    fontWeight: '800',
                    marginBottom: '0.75rem',
                    color: item.is_completed ? '#34d399' : '#e2e8f0',
                    textDecoration: item.is_completed ? 'line-through' : 'none'
                  }}>
                    {item.topic}
                  </h4>

                  {/* Objectives */}
                  {item.learning_objectives && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                        Learning Objectives
                      </div>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                        {item.learning_objectives}
                      </p>
                    </div>
                  )}

                  {/* Practice Task & Suggested Project Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginTop: '0.75rem' }}>
                    {item.practice_task && (
                      <div style={{
                        padding: '0.85rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(99, 102, 241, 0.06)',
                        border: '1px solid rgba(99, 102, 241, 0.2)'
                      }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#818cf8', textTransform: 'uppercase', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <Code size={13} /> Practical Hands-On Exercise
                        </div>
                        <p style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.5' }}>
                          {item.practice_task}
                        </p>
                      </div>
                    )}

                    {item.suggested_project && (
                      <div style={{
                        padding: '0.85rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(16, 185, 129, 0.06)',
                        border: '1px solid rgba(16, 185, 129, 0.2)'
                      }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#34d399', textTransform: 'uppercase', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <Zap size={13} /> Portfolio Mini-Deliverable
                        </div>
                        <p style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.5' }}>
                          {item.suggested_project}
                        </p>
                      </div>
                    )}
                  </div>

                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Sidebar: All Roadmaps History */}
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Map size={18} color="var(--accent-primary)" /> My Roadmaps ({roadmaps.length})
        </h3>

        {roadmaps.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem 0' }}>
            No roadmaps created yet.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '600px', overflowY: 'auto' }}>
            {roadmaps.map((r) => (
              <div
                key={r.id}
                onClick={() => navigate(`/roadmaps/${r.id}`)}
                style={{
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-md)',
                  background: activeRoadmap?.id === r.id ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                  border: activeRoadmap?.id === r.id ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                  <h5 style={{ fontSize: '0.9rem', fontWeight: '700', paddingRight: '1rem' }}>
                    {r.title}
                  </h5>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteRoadmap(r.id);
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      padding: '2px'
                    }}
                    title="Delete"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  {r.target_role}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>{r.total_weeks} Weeks • {r.completed_items}/{r.total_items} done</span>
                  <span style={{ fontWeight: 'bold', color: r.completion_percentage === 100 ? '#34d399' : 'inherit' }}>
                    {r.completion_percentage}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
          <Link to="/job-analyzer" className="btn-secondary" style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}>
            + New from Job Analysis
          </Link>
        </div>
      </div>

    </div>
  );
}
