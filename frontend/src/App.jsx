import React, { useState } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Skills from './pages/Skills';
import JobAnalyzer from './pages/JobAnalyzer';
import Roadmap from './pages/Roadmap';
import InterviewSimulator from './pages/InterviewSimulator';
import ProjectRecommendations from './pages/ProjectRecommendations';
import { checkHealth, checkDbHealth } from './services/api';
import { Activity, Server, Database, Cpu, CheckCircle2, XCircle, Sparkles, UserCheck, LogIn, UserPlus, User, Code, FileSearch, Map, Mic, FolderKanban } from 'lucide-react';



function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem', flexWrap: 'wrap', gap: '1rem' }}>
      <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'var(--accent-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)'
          }}>
            <Cpu size={24} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', lineHeight: '1.2' }}>
              SkillForge <span className="gradient-text">AI</span>
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Personal Skill Gap & Career Simulator
            </span>
          </div>
        </div>
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        {isAuthenticated ? (
          <>
            <Link to="/dashboard" className="btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.875rem' }}>
              <UserCheck size={16} /> Dashboard
            </Link>
            <Link to="/profile" className="btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.875rem' }}>
              <User size={16} /> Profile
            </Link>
            <Link to="/skills" className="btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.875rem' }}>
              <Code size={16} /> Skills
            </Link>
            <Link to="/job-analyzer" className="btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.875rem' }}>
              <FileSearch size={16} /> Job Analyzer
            </Link>
            <Link to="/roadmaps" className="btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.875rem' }}>
              <Map size={16} /> Roadmaps
            </Link>
            <Link to="/interviews" className="btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.875rem' }}>
              <Mic size={16} /> Interviews
            </Link>
            <button

              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="btn-secondary"
              style={{ padding: '0.5rem 0.9rem', fontSize: '0.875rem', color: 'var(--accent-rose)' }}
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
              <LogIn size={16} /> Sign In
            </Link>
            <Link to="/register" className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
              <UserPlus size={16} /> Get Started
            </Link>
          </>
        )}
      </div>
    </header>
  );
}

function HomePage() {
  const [healthData, setHealthData] = useState(null);
  const [dbHealthData, setDbHealthData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dbLoading, setDbLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dbError, setDbError] = useState(null);

  const handleCheckHealth = async () => {
    setLoading(true);
    setError(null);
    const result = await checkHealth();
    if (result.success) {
      setHealthData(result.data);
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleCheckDbHealth = async () => {
    setDbLoading(true);
    setDbError(null);
    const result = await checkDbHealth();
    if (result.success) {
      setDbHealthData(result.data);
    } else {
      setDbError(result.error);
    }
    setDbLoading(false);
  };

  return (
    <main style={{ display: 'grid', gap: '2rem' }}>
      <section className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem' }}>
        <div className="badge badge-success" style={{ marginBottom: '1rem' }}>
          <Sparkles size={14} /> Phase 4 Active: Student Profile & Skill Management Complete
        </div>
        
        <h1 style={{ fontSize: '2.8rem', marginBottom: '1rem', fontWeight: '800' }}>
          Bridge Your <span className="gradient-text">Skill Gaps</span> for Target Engineering Roles
        </h1>
        
        <p style={{
          maxWidth: '680px',
          margin: '0 auto 2.5rem',
          color: 'var(--text-secondary)',
          fontSize: '1.1rem',
          lineHeight: '1.7'
        }}>
          SkillForge AI analyzes job descriptions, measures your real technical readiness, generates customized learning roadmaps, and conducts interactive AI technical interview simulations.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <Link to="/register" className="btn-primary" style={{ padding: '0.8rem 2rem', fontSize: '1.05rem' }}>
            Get Started Free 🚀
          </Link>
          <button 
            className="btn-secondary" 
            onClick={handleCheckHealth}
            disabled={loading}
            id="test-backend-btn"
          >
            {loading ? <span className="spinner"></span> : <><Server size={18} /> Test FastAPI Health</>}
          </button>
          <button 
            className="btn-secondary" 
            onClick={handleCheckDbHealth}
            disabled={dbLoading}
            id="test-db-btn"
          >
            {dbLoading ? <span className="spinner"></span> : <><Database size={18} color="var(--accent-emerald)" /> Test DB Connection</>}
          </button>
        </div>
      </section>

      {/* Database Health Response Box */}
      {(dbHealthData || dbError) && (
        <section className="glass-card" style={{ borderLeft: dbHealthData ? '4px solid #10b981' : '4px solid #f43f5e' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            {dbHealthData ? <CheckCircle2 size={24} color="#10b981" /> : <XCircle size={24} color="#f43f5e" />}
            <h3 style={{ fontSize: '1.2rem' }}>
              Database Status: {dbHealthData ? 'Connected' : 'Connection Refused'}
            </h3>
          </div>

          {dbHealthData && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.4)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.9rem',
              color: '#e2e8f0',
              lineHeight: '1.6'
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Status:</span>
                <span style={{ color: '#34d399', fontWeight: 'bold' }}>{dbHealthData.status}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Database State:</span>
                <span style={{ color: '#34d399' }}>{dbHealthData.database}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Engine Dialect:</span>
                <span>{dbHealthData.engine}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '0.5rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Timestamp:</span>
                <span>{dbHealthData.timestamp}</span>
              </div>
            </div>
          )}

          {dbError && (
            <div className="alert alert-error">
              <strong>Database Error:</strong> {dbError}
            </div>
          )}
        </section>
      )}

      {/* Backend Response Display Box */}
      {(healthData || error) && (
        <section className="glass-card" style={{ borderLeft: healthData ? '4px solid #10b981' : '4px solid #f43f5e' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            {healthData ? <CheckCircle2 size={24} color="#10b981" /> : <XCircle size={24} color="#f43f5e" />}
            <h3 style={{ fontSize: '1.2rem' }}>
              Backend Health Status: {healthData ? 'Connected' : 'Connection Failed'}
            </h3>
          </div>

          {healthData && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.4)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.9rem',
              color: '#e2e8f0',
              lineHeight: '1.6'
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>API Status:</span>
                <span style={{ color: '#34d399', fontWeight: 'bold' }}>{healthData.status}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Message:</span>
                <span>{healthData.message}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '0.5rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Timestamp:</span>
                <span>{healthData.timestamp}</span>
              </div>
            </div>
          )}

          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
          )}
        </section>
      )}

      {/* Architecture & Phase Roadmap */}
      <section className="glass-card">
        <h3 style={{ fontSize: '1.2rem', marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={20} color="var(--accent-primary)" /> Project Implementation Progress
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <div style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 'bold', marginBottom: '0.2rem' }}>✓ PHASE 1</div>
            <div style={{ fontWeight: '600', marginBottom: '0.4rem' }}>Setup & Health API</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Vite + React, FastAPI, CORS.</div>
          </div>

          <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <div style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 'bold', marginBottom: '0.2rem' }}>✓ PHASE 2</div>
            <div style={{ fontWeight: '600', marginBottom: '0.4rem' }}>Database & Models</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>PostgreSQL & 12 ORM models.</div>
          </div>

          <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <div style={{ fontSize: '0.85rem', color: '#34d399', fontWeight: 'bold', marginBottom: '0.2rem' }}>✓ PHASE 3</div>
            <div style={{ fontWeight: '600', marginBottom: '0.4rem' }}>Auth & JWT Security</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>User login, register & session state.</div>
          </div>

          <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.4)' }}>
            <div style={{ fontSize: '0.85rem', color: '#818cf8', fontWeight: 'bold', marginBottom: '0.2rem' }}>✓ PHASE 4</div>
            <div style={{ fontWeight: '600', marginBottom: '0.4rem' }}>Profile & Skill Matrix</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Student profile & skill inventory CRUD.</div>
          </div>
        </div>
      </section>
    </main>
  );
}

function App() {
  return (
    <AuthProvider>
      <div className="app-container">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/skills"
            element={
              <ProtectedRoute>
                <Skills />
              </ProtectedRoute>
            }
          />
          <Route
            path="/job-analyzer"
            element={
              <ProtectedRoute>
                <JobAnalyzer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roadmaps"
            element={
              <ProtectedRoute>
                <Roadmap />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roadmaps/:id"
            element={
              <ProtectedRoute>
                <Roadmap />
              </ProtectedRoute>
            }
          />
          <Route
            path="/interviews"
            element={
              <ProtectedRoute>
                <InterviewSimulator />
              </ProtectedRoute>
            }
          />
          <Route
            path="/project-recommendations/:jobAnalysisId"
            element={
              <ProtectedRoute>
                <ProjectRecommendations />
              </ProtectedRoute>
            }
          />
          <Route
            path="/project-recommendations"
            element={
              <ProtectedRoute>
                <ProjectRecommendations />
              </ProtectedRoute>
            }
          />
        </Routes>

        <footer style={{
          marginTop: '3rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid var(--border-color)',
          textAlign: 'center',
          fontSize: '0.85rem',
          color: 'var(--text-muted)'
        }}>
          SkillForge AI © 2026 — Modular Full-Stack Portfolio Application
        </footer>
      </div>
    </AuthProvider>
  );
}

export default App;
