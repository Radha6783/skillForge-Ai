import React, { useState, useEffect } from 'react';
import { skillsAPI } from '../services/api';
import {
  Code,
  Plus,
  Trash2,
  Edit2,
  CheckCircle,
  AlertCircle,
  Loader2,
  Search,
  Filter,
  Layers,
  Sparkles,
  BookOpen
} from 'lucide-react';

const CATEGORIES = [
  'Programming Language',
  'Framework & Library',
  'Database',
  'Cloud & DevOps',
  'Tools & Platforms',
  'CS Fundamentals',
  'Soft Skills',
  'Technical',
  'Other'
];

const PROFICIENCY_LEVELS = [
  { value: 'BEGINNER', label: '🌱 Beginner', badgeClass: 'badge-warning' },
  { value: 'INTERMEDIATE', label: '🚀 Intermediate', badgeClass: 'badge-success' },
  { value: 'ADVANCED', label: '⚡ Advanced', badgeClass: 'badge-success' },
  { value: 'EXPERT', label: '👑 Expert', badgeClass: 'badge-success' }
];

const Skills = () => {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Add / Edit Modal State
  const [showModal, setShowModal] = useState(false);
  const [editingSkill, setEditingSkill] = useState(null); // null if adding new skill
  const [formSkillName, setFormSkillName] = useState('');
  const [formCategory, setFormCategory] = useState('Programming Language');
  const [formLevel, setFormLevel] = useState('BEGINNER');
  const [formExperienceMonths, setFormExperienceMonths] = useState(6);
  const [submitting, setSubmitting] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('ALL');

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await skillsAPI.getSkills();
      setSkills(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch user skills.');
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setEditingSkill(null);
    setFormSkillName('');
    setFormCategory('Programming Language');
    setFormLevel('BEGINNER');
    setFormExperienceMonths(6);
    setShowModal(true);
  };

  const openEditModal = (skillItem) => {
    setEditingSkill(skillItem);
    setFormSkillName(skillItem.skill_name);
    setFormCategory(skillItem.category || 'Technical');
    setFormLevel(skillItem.self_assessed_level || 'BEGINNER');
    setFormExperienceMonths(skillItem.experience_months || 0);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingSkill(null);
  };

  const handleSaveSkill = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!formSkillName.trim()) {
      setError('Skill name is required.');
      return;
    }

    setSubmitting(true);
    try {
      if (editingSkill) {
        // Edit existing user_skill
        const updated = await skillsAPI.updateSkill(editingSkill.id, {
          category: formCategory,
          self_assessed_level: formLevel,
          experience_months: parseInt(formExperienceMonths, 10) || 0,
        });
        setSkills((prev) => prev.map((s) => (s.id === editingSkill.id ? updated : s)));
        setSuccessMsg(`Updated skill "${updated.skill_name}" successfully!`);
      } else {
        // Add new user_skill
        const added = await skillsAPI.addSkill({
          skill_name: formSkillName.trim(),
          category: formCategory,
          self_assessed_level: formLevel,
          experience_months: parseInt(formExperienceMonths, 10) || 0,
        });
        setSkills((prev) => [...prev, added]);
        setSuccessMsg(`Added skill "${added.skill_name}" to your profile!`);
      }
      closeModal();
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(', '));
      } else {
        setError('Failed to save skill. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteSkill = async (id, name) => {
    if (!window.confirm(`Are you sure you want to remove "${name}" from your skills?`)) {
      return;
    }

    setError('');
    try {
      await skillsAPI.deleteSkill(id);
      setSkills((prev) => prev.filter((s) => s.id !== id));
      setSuccessMsg(`Skill "${name}" removed.`);
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to remove skill "${name}".`);
    }
  };

  // Filtering skills
  const filteredSkills = skills.filter((s) => {
    const matchesSearch = s.skill_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (s.category && s.category.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = selectedCategoryFilter === 'ALL' || s.category === selectedCategoryFilter;
    return matchesSearch && matchesCategory;
  });

  const getLevelBadgeClass = (level) => {
    switch (level) {
      case 'EXPERT': return 'badge-success';
      case 'ADVANCED': return 'badge-success';
      case 'INTERMEDIATE': return 'badge-warning';
      default: return 'badge-secondary';
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', color: 'var(--text-secondary)' }}>
        <Loader2 size={36} className="spinner" style={{ marginBottom: '1rem', color: 'var(--accent-primary)' }} />
        <p>Loading your skill inventory...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      {/* Header Banner */}
      <div className="glass-card" style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'var(--accent-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)',
            flexShrink: 0
          }}>
            <Code size={28} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.75rem', marginBottom: '0.2rem' }}>
              Skill Inventory Management
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
              Add and assess your technical skills, frameworks, databases, and core concepts.
            </p>
          </div>
        </div>

        <button onClick={openAddModal} className="btn-primary" style={{ padding: '0.8rem 1.6rem' }}>
          <Plus size={20} /> Add New Skill
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem' }}>
          <CheckCircle size={20} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="glass-card" style={{ marginBottom: '2rem', padding: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search Bar */}
          <div style={{ flex: '1 1 240px', position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '2.8rem' }}
              placeholder="Filter skills by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Category Dropdown */}
          <div style={{ flex: '0 1 220px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={18} color="var(--accent-primary)" />
            <select
              className="form-input"
              value={selectedCategoryFilter}
              onChange={(e) => setSelectedCategoryFilter(e.target.value)}
              style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
            >
              <option value="ALL">All Categories ({skills.length})</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Skills Grid */}
      {filteredSkills.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem' }}>
          <BookOpen size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>No Skills Found</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
            {skills.length === 0
              ? 'You have not added any skills to your profile yet. Add your programming languages, frameworks, and tools to get started.'
              : 'No skills match your current search or category filter.'}
          </p>
          {skills.length === 0 && (
            <button onClick={openAddModal} className="btn-primary">
              <Plus size={18} /> Add Your First Skill
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: '1.25rem' }}>
          {filteredSkills.map((skill) => (
            <div
              key={skill.id}
              className="glass-card"
              style={{
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'transform 0.2s ease, border-color 0.2s ease',
              }}
            >
              <div>
                {/* Top header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: '700' }}>
                    {skill.skill_name}
                  </h3>
                  <span
                    className="badge"
                    style={{
                      fontSize: '0.7rem',
                      background: 'rgba(99, 102, 241, 0.15)',
                      color: '#a5b4fc',
                      border: '1px solid rgba(99, 102, 241, 0.3)'
                    }}
                  >
                    {skill.category || 'Technical'}
                  </span>
                </div>

                {/* Level & Experience */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Proficiency:</span>{' '}
                    <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                      {skill.self_assessed_level}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Experience:</span>{' '}
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {skill.experience_months >= 12
                        ? `${(skill.experience_months / 12).toFixed(1)} yrs (${skill.experience_months} mos)`
                        : `${skill.experience_months} months`}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.8rem' }}>
                <button
                  onClick={() => openEditModal(skill)}
                  className="btn-secondary"
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                  title="Edit Skill"
                >
                  <Edit2 size={14} /> Edit
                </button>
                <button
                  onClick={() => handleDeleteSkill(skill.id, skill.skill_name)}
                  className="btn-secondary"
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', color: 'var(--accent-rose)', borderColor: 'rgba(244, 63, 94, 0.3)' }}
                  title="Delete Skill"
                >
                  <Trash2 size={14} /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Skill Modal Backdrop */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            className="glass-card"
            style={{
              width: '100%',
              maxWidth: '480px',
              position: 'relative',
              boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
              animation: 'modalFadeIn 0.2s ease-out'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.4rem' }}>
                {editingSkill ? `Edit "${editingSkill.skill_name}"` : 'Add New Skill'}
              </h2>
              <button
                onClick={closeModal}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  padding: '0.2rem 0.6rem'
                }}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSaveSkill}>
              {/* Skill Name */}
              <div className="form-group">
                <label className="form-label" htmlFor="skill_name">
                  Skill Name *
                </label>
                <input
                  id="skill_name"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Python, React, PostgreSQL, Docker"
                  value={formSkillName}
                  onChange={(e) => setFormSkillName(e.target.value)}
                  disabled={!!editingSkill || submitting}
                  required
                />
              </div>

              {/* Category */}
              <div className="form-group">
                <label className="form-label" htmlFor="category">
                  Skill Category
                </label>
                <select
                  id="category"
                  className="form-input"
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                  disabled={submitting}
                  style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              {/* Proficiency Level */}
              <div className="form-group">
                <label className="form-label" htmlFor="level">
                  Self-Assessed Level
                </label>
                <select
                  id="level"
                  className="form-input"
                  value={formLevel}
                  onChange={(e) => setFormLevel(e.target.value)}
                  disabled={submitting}
                  style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                >
                  {PROFICIENCY_LEVELS.map((lvl) => (
                    <option key={lvl.value} value={lvl.value}>
                      {lvl.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Experience Months */}
              <div className="form-group">
                <label className="form-label" htmlFor="experience_months">
                  Experience (in Months)
                </label>
                <input
                  id="experience_months"
                  type="number"
                  min="0"
                  max="480"
                  className="form-input"
                  placeholder="e.g. 12 (for 1 year)"
                  value={formExperienceMonths}
                  onChange={(e) => setFormExperienceMonths(e.target.value)}
                  disabled={submitting}
                />
              </div>

              {/* Modal Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.75rem' }}>
                <button type="button" onClick={closeModal} className="btn-secondary" disabled={submitting}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? <span className="spinner"></span> : editingSkill ? 'Save Changes' : 'Add Skill'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Skills;
