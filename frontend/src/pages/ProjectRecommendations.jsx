import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectAPI, jobAnalysisAPI } from '../services/api';

const ProjectRecommendations = () => {
  const { jobAnalysisId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    if (jobAnalysisId) {
      loadRecommendations(jobAnalysisId);
    }
  }, [jobAnalysisId]);

  const loadRecommendations = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await projectAPI.getProjectRecommendations(id);
      setData(res);
    } catch (err) {
      if (import.meta.env.DEV) { console.error('Failed to load project recommendations:', err); }
      setError(err.response?.data?.detail || 'Failed to load project recommendations.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!jobAnalysisId) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await projectAPI.generateProjectRecommendations(jobAnalysisId);
      setData(res);
    } catch (err) {
      if (import.meta.env.DEV) { console.error('Failed to regenerate projects:', err); }
      setError(err.response?.data?.detail || 'Failed to regenerate projects.');
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleComplete = async (projectId, currentStatus) => {
    try {
      const updated = await projectAPI.toggleProjectRecommendationComplete(projectId, !currentStatus);
      setData((prev) => {
        if (!prev) return prev;
        const updatedProjects = prev.projects.map((p) =>
          p.id === projectId ? { ...p, is_completed: updated.is_completed } : p
        );
        const completedCount = updatedProjects.filter((p) => p.is_completed).length;
        return {
          ...prev,
          completed_projects: completedCount,
          projects: updatedProjects,
        };
      });
    } catch (err) {
      if (import.meta.env.DEV) { console.error('Failed to toggle project completion:', err); }
    }
  };

  const handleCopyResumeBullet = (projectId, bulletText) => {
    if (!bulletText) return;
    navigator.clipboard.writeText(bulletText);
    setCopiedId(projectId);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const getDifficultyBadgeColor = (diff) => {
    switch ((diff || '').toUpperCase()) {
      case 'BEGINNER':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'ADVANCED':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'INTERMEDIATE':
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400 mb-4"></div>
        <p className="text-gray-300 text-lg">Synthesizing personalized portfolio projects...</p>
        <p className="text-gray-500 text-sm mt-1">Grounding recommendations in your job skill gap report</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Top Breadcrumb / Nav */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div className="flex items-center space-x-2 text-sm text-gray-400">
          <Link to="/" className="hover:text-cyan-400 transition-colors">Dashboard</Link>
          <span>/</span>
          <Link to="/job-analyzer" className="hover:text-cyan-400 transition-colors">Job Analyzer</Link>
          <span>/</span>
          <span className="text-gray-200">Recommended Projects</span>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to={`/roadmap`}
            className="px-4 py-2 rounded-lg text-sm bg-slate-800/80 hover:bg-slate-700 text-gray-200 border border-slate-700 transition-all"
          >
            🗺️ View Learning Roadmap
          </Link>
          <button
            onClick={handleRegenerate}
            disabled={generating}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {generating ? (
              <>
                <span className="inline-block animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                Generating...
              </>
            ) : (
              <>⚡ Regenerate Recommendations</>
            )}
          </button>
        </div>
      </div>

      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800/90 to-slate-900 border border-slate-800/80 rounded-2xl p-6 mb-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">🚀</span>
              <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-white via-gray-200 to-cyan-400 bg-clip-text text-transparent">
                AI Portfolio Project Recommendations
              </h1>
            </div>
            <p className="text-gray-400 text-sm md:text-base">
              Target Role:{' '}
              <span className="text-cyan-300 font-medium">
                {data?.target_role || data?.job_title || 'Software Engineering'}
              </span>{' '}
              {data?.job_title && data?.target_role !== data?.job_title && (
                <span className="text-gray-500">({data.job_title})</span>
              )}
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-4 bg-slate-800/60 border border-slate-700/60 rounded-xl px-5 py-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{data?.total_projects || 0}</div>
              <div className="text-xs text-gray-400 uppercase tracking-wider">Projects</div>
            </div>
            <div className="h-8 w-px bg-slate-700"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-400">{data?.completed_projects || 0}</div>
              <div className="text-xs text-gray-400 uppercase tracking-wider">Completed</div>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Projects List */}
      {data?.projects?.length > 0 ? (
        <div className="space-y-6">
          {data.projects.map((project, idx) => (
            <div
              key={project.id || idx}
              className={`border rounded-2xl p-6 backdrop-blur-xl transition-all duration-300 ${
                project.is_completed
                  ? 'bg-slate-900/60 border-emerald-500/30 shadow-emerald-500/5'
                  : 'bg-slate-900/80 border-slate-800 hover:border-cyan-500/40 shadow-xl'
              }`}
            >
              {/* Project Top Bar */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-800/80">
                <div className="flex items-start md:items-center gap-3">
                  <span className="text-xl">💼</span>
                  <div>
                    <h2 className="text-xl font-bold text-white hover:text-cyan-300 transition-colors">
                      {project.title}
                    </h2>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${getDifficultyBadgeColor(
                          project.difficulty
                        )}`}
                      >
                        {project.difficulty}
                      </span>
                      {project.estimated_hours && (
                        <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-gray-300 border border-slate-700">
                          ⏱️ ~{project.estimated_hours} hrs
                        </span>
                      )}
                      {project.is_completed && (
                        <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          ✓ Completed
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Completion Toggle */}
                <button
                  onClick={() => handleToggleComplete(project.id, project.is_completed)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${
                    project.is_completed
                      ? 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40'
                      : 'bg-slate-800 hover:bg-slate-700 text-gray-300 border border-slate-700'
                  }`}
                >
                  <span>{project.is_completed ? '✓ Completed' : 'Mark as Completed'}</span>
                </button>
              </div>

              {/* Skills Badges */}
              {project.skills_practiced?.length > 0 && (
                <div className="mb-4">
                  <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
                    Skills Addressed
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {project.skills_practiced.map((skill, sIdx) => (
                      <span
                        key={sIdx}
                        className="text-xs px-3 py-1 rounded-lg bg-cyan-950/40 text-cyan-300 border border-cyan-800/40 font-mono"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Why Recommended Callout */}
              {project.why_recommended && (
                <div className="mb-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200/90 text-sm flex items-start gap-2.5">
                  <span className="text-base mt-0.5">💡</span>
                  <div>
                    <strong className="text-amber-300">Why Recommended:</strong> {project.why_recommended}
                  </div>
                </div>
              )}

              {/* Description & Expected Outcome */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 text-sm">
                {project.description && (
                  <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4">
                    <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">
                      Project Overview
                    </div>
                    <p className="text-gray-300 leading-relaxed">{project.description}</p>
                  </div>
                )}
                {project.expected_outcome && (
                  <div className="bg-slate-800/40 border border-slate-800/80 rounded-xl p-4">
                    <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1.5">
                      Portfolio Deliverable
                    </div>
                    <p className="text-gray-300 leading-relaxed">{project.expected_outcome}</p>
                  </div>
                )}
              </div>

              {/* Resume Bullet Suggestion */}
              {project.resume_bullet && (
                <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-sm relative group">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="text-xs font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                      <span>📄</span> Suggested Resume Accomplishment Bullet
                    </div>
                    <button
                      onClick={() => handleCopyResumeBullet(project.id, project.resume_bullet)}
                      className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-gray-300 border border-slate-700 transition-colors flex items-center gap-1"
                    >
                      {copiedId === project.id ? '✓ Copied!' : '📋 Copy Bullet'}
                    </button>
                  </div>
                  <p className="text-gray-300 font-mono text-xs leading-relaxed bg-slate-900/50 p-2.5 rounded border border-slate-800">
                    "{project.resume_bullet}"
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
          <span className="text-4xl block mb-3">📂</span>
          <h3 className="text-lg font-semibold text-white mb-1">No Project Recommendations Yet</h3>
          <p className="text-gray-400 text-sm max-w-md mx-auto mb-6">
            Click below to generate grounded portfolio projects targeting your identified skill gaps.
          </p>
          <button
            onClick={handleRegenerate}
            disabled={generating}
            className="px-6 py-2.5 rounded-xl font-medium bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/25 transition-all"
          >
            {generating ? 'Generating Projects...' : '⚡ Generate Project Recommendations'}
          </button>
        </div>
      )}
    </div>
  );
};

export default ProjectRecommendations;
