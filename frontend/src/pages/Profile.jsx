import React, { useState, useEffect } from 'react';
import { profileAPI } from '../services/api';
import { User, GraduationCap, Award, Target, Save, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const Profile = () => {
  const [formData, setFormData] = useState({
    full_name: '',
    college: '',
    degree: '',
    branch: '',
    graduation_year: '',
    target_role: '',
    experience_level: 'BEGINNER',
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await profileAPI.getProfile();
      setFormData({
        full_name: data.full_name || '',
        college: data.college || '',
        degree: data.degree || '',
        branch: data.branch || '',
        graduation_year: data.graduation_year || '',
        target_role: data.target_role || '',
        experience_level: data.experience_level || 'BEGINNER',
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load profile details.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccessMsg('');

    const payload = {
      ...formData,
      graduation_year: formData.graduation_year ? parseInt(formData.graduation_year, 10) : null,
    };

    try {
      const updated = await profileAPI.updateProfile(payload);
      setFormData({
        full_name: updated.full_name || '',
        college: updated.college || '',
        degree: updated.degree || '',
        branch: updated.branch || '',
        graduation_year: updated.graduation_year || '',
        target_role: updated.target_role || '',
        experience_level: updated.experience_level || 'BEGINNER',
      });
      setSuccessMsg('Profile updated successfully!');
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(', '));
      } else {
        setError('Failed to update profile. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', color: 'var(--text-secondary)' }}>
        <Loader2 size={36} className="spinner" style={{ marginBottom: '1rem', color: 'var(--accent-primary)' }} />
        <p>Loading your profile...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
      {/* Header Banner */}
      <div className="glass-card" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
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
          <User size={28} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.75rem', marginBottom: '0.2rem' }}>
            Student Profile Management
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Set up your academic background and career goals to personalize your SkillForge AI gap analysis & roadmaps.
          </p>
        </div>
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

      {/* Profile Form */}
      <form onSubmit={handleSubmit} className="glass-card" style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          
          {/* Personal Info */}
          <div>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <User size={18} /> Personal Details
            </h3>

            <div className="form-group">
              <label className="form-label" htmlFor="full_name">
                Full Name
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                className="form-input"
                placeholder="e.g. Alex Johnson"
                value={formData.full_name}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="college">
                College / University
              </label>
              <input
                id="college"
                name="college"
                type="text"
                className="form-input"
                placeholder="e.g. Stanford University / Tech Institute"
                value={formData.college}
                onChange={handleChange}
              />
            </div>
          </div>

          {/* Academic Info */}
          <div>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <GraduationCap size={18} /> Academic Credentials
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="degree">
                  Degree
                </label>
                <input
                  id="degree"
                  name="degree"
                  type="text"
                  className="form-input"
                  placeholder="e.g. B.Tech / B.S."
                  value={formData.degree}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="branch">
                  Branch / Field
                </label>
                <input
                  id="branch"
                  name="branch"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Computer Science"
                  value={formData.branch}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="graduation_year">
                Graduation Year
              </label>
              <input
                id="graduation_year"
                name="graduation_year"
                type="number"
                min="1990"
                max="2040"
                className="form-input"
                placeholder="e.g. 2026"
                value={formData.graduation_year}
                onChange={handleChange}
              />
            </div>
          </div>
        </div>

        <hr style={{ borderColor: 'var(--border-color)', margin: '0.5rem 0' }} />

        {/* Career Goals */}
        <div>
          <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Target size={18} /> Target Career Role & Level
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="target_role">
                Target Job Role
              </label>
              <input
                id="target_role"
                name="target_role"
                type="text"
                className="form-input"
                placeholder="e.g. Backend Engineer / Full Stack Developer"
                value={formData.target_role}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="experience_level">
                Experience Level
              </label>
              <select
                id="experience_level"
                name="experience_level"
                className="form-input"
                value={formData.experience_level}
                onChange={handleChange}
                style={{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
              >
                <option value="BEGINNER">🌱 Beginner (Student / Entry-level)</option>
                <option value="INTERMEDIATE">🚀 Intermediate (1-2 years projects/internships)</option>
                <option value="ADVANCED">⚡ Advanced (3+ years / Experienced)</option>
              </select>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button type="submit" className="btn-primary" disabled={saving} style={{ padding: '0.8rem 2rem' }}>
            {saving ? (
              <>
                <span className="spinner"></span> Saving Changes...
              </>
            ) : (
              <>
                <Save size={18} /> Save Profile
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Profile;
