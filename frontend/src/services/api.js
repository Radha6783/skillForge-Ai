import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to add JWT authorization header if present
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const url = error.config?.url || '';
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to connect to backend API',
    };
  }
};

export const checkDbHealth = async () => {
  try {
    const response = await apiClient.get('/api/health/db');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to connect to database',
    };
  }
};

export const authAPI = {
  register: async (userData) => {
    const response = await apiClient.post('/api/auth/register', userData);
    return response.data;
  },
  login: async (credentials) => {
    const response = await apiClient.post('/api/auth/login', credentials);
    return response.data;
  },
  getMe: async () => {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
  },
};

export const profileAPI = {
  getProfile: async () => {
    const response = await apiClient.get('/api/profile/me');
    return response.data;
  },
  updateProfile: async (profileData) => {
    const response = await apiClient.put('/api/profile/me', profileData);
    return response.data;
  },
};

export const skillsAPI = {
  getSkills: async () => {
    const response = await apiClient.get('/api/skills/me');
    return response.data;
  },
  addSkill: async (skillData) => {
    const response = await apiClient.post('/api/skills/me', skillData);
    return response.data;
  },
  updateSkill: async (id, skillData) => {
    const response = await apiClient.put(`/api/skills/me/${id}`, skillData);
    return response.data;
  },
  deleteSkill: async (id) => {
    const response = await apiClient.delete(`/api/skills/me/${id}`);
    return response.data;
  },
  getCatalog: async () => {
    const response = await apiClient.get('/api/skills/catalog');
    return response.data;
  },
};

export const jobAnalysisAPI = {
  analyzeJob: async (data) => {
    const response = await apiClient.post('/api/job-analysis/analyze', data, { timeout: 30000 });
    return response.data;
  },
  getHistory: async () => {
    const response = await apiClient.get('/api/job-analysis/history');
    return response.data;
  },
  getAnalysisDetail: async (id) => {
    const response = await apiClient.get(`/api/job-analysis/${id}`);
    return response.data;
  },
  deleteAnalysis: async (id) => {
    const response = await apiClient.delete(`/api/job-analysis/${id}`);
    return response.data;
  },
};

export const skillGapAPI = {
  analyzeSkillGap: async (jobAnalysisId) => {
    const response = await apiClient.post(`/api/skill-gap/analyze/${jobAnalysisId}`);
    return response.data;
  },
  getSkillGapReport: async (jobAnalysisId) => {
    const response = await apiClient.get(`/api/skill-gap/report/${jobAnalysisId}`);
    return response.data;
  },
  getSkillGapSummary: async () => {
    const response = await apiClient.get('/api/skill-gap/summary');
    return response.data;
  },
};

export const roadmapAPI = {
  generateRoadmap: async (jobAnalysisId) => {
    const response = await apiClient.post(`/api/roadmaps/generate/${jobAnalysisId}`, {}, { timeout: 35000 });
    return response.data;
  },
  getRoadmaps: async () => {
    const response = await apiClient.get('/api/roadmaps');
    return response.data;
  },
  getRoadmap: async (roadmapId) => {
    const response = await apiClient.get(`/api/roadmaps/${roadmapId}`);
    return response.data;
  },
  updateRoadmapItem: async (roadmapId, itemId, isCompleted) => {
    const response = await apiClient.patch(`/api/roadmaps/${roadmapId}/items/${itemId}`, {
      is_completed: isCompleted,
    });
    return response.data;
  },
  deleteRoadmap: async (roadmapId) => {
    const response = await apiClient.delete(`/api/roadmaps/${roadmapId}`);
    return response.data;
  },
  getRoadmapProgress: async () => {
    const response = await apiClient.get('/api/roadmaps/summary/progress');
    return response.data;
  },
};

export const interviewAPI = {
  startInterview: async (data) => {
    const response = await apiClient.post('/api/interviews/start', data, { timeout: 35000 });
    return response.data;
  },
  getInterviews: async () => {
    const response = await apiClient.get('/api/interviews');
    return response.data;
  },
  getInterview: async (sessionId) => {
    const response = await apiClient.get(`/api/interviews/${sessionId}`);
    return response.data;
  },
  submitAnswer: async (sessionId, data) => {
    const response = await apiClient.post(`/api/interviews/${sessionId}/answer`, data);
    return response.data;
  },
  finishInterview: async (sessionId) => {
    const response = await apiClient.post(`/api/interviews/${sessionId}/finish`);
    return response.data;
  },
  getInterviewResults: async (sessionId) => {
    const response = await apiClient.get(`/api/interviews/${sessionId}/results`);
    return response.data;
  },
  deleteInterview: async (sessionId) => {
    const response = await apiClient.delete(`/api/interviews/${sessionId}`);
    return response.data;
  },
  getRecentSummary: async () => {
    const response = await apiClient.get('/api/interviews/summary/recent');
    return response.data;
  },
};

export const projectAPI = {
  generateProjectRecommendations: async (jobAnalysisId) => {
    const response = await apiClient.post(`/api/project-recommendations/generate/${jobAnalysisId}`, {}, { timeout: 35000 });
    return response.data;
  },
  getProjectRecommendations: async (jobAnalysisId) => {
    const response = await apiClient.get(`/api/project-recommendations/${jobAnalysisId}`);
    return response.data;
  },
  toggleProjectRecommendationComplete: async (recommendationId, isCompleted) => {
    const response = await apiClient.patch(`/api/project-recommendations/${recommendationId}/complete`, { is_completed: isCompleted });
    return response.data;
  },
  deleteProjectRecommendations: async (jobAnalysisId) => {
    const response = await apiClient.delete(`/api/project-recommendations/${jobAnalysisId}`);
    return response.data;
  },
  getRecentProjectRecommendations: async (limit = 5) => {
    const response = await apiClient.get(`/api/project-recommendations/recent?limit=${limit}`);
    return response.data;
  },
};

export const careerReadinessAPI = {
  getReadiness: async () => {
    const response = await apiClient.get('/api/career-readiness');
    return response.data;
  },
  getReadinessForJob: async (jobAnalysisId) => {
    const response = await apiClient.get(`/api/career-readiness/${jobAnalysisId}`);
    return response.data;
  },
  getTargetRoles: async () => {
    const response = await apiClient.get('/api/career-readiness/target-roles');
    return response.data;
  },
};

export default apiClient;


