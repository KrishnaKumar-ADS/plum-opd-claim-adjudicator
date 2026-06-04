import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

// Claims
export const submitClaim = (formData) => api.post('/api/claims', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});

export const submitClaimJSON = (data) => api.post('/api/claims/json', data);

export const getClaims = (skip = 0, limit = 50) =>
  api.get(`/api/claims?skip=${skip}&limit=${limit}`);

export const getClaim = (claimId) => api.get(`/api/claims/${claimId}`);

// Decisions
export const getDecisions = (type = null) =>
  api.get(`/api/decisions${type ? `?decision_type=${type}` : ''}`);

export const getDecision = (claimId) => api.get(`/api/decisions/${claimId}`);

// Appeals
export const createAppeal = (data) => api.post('/api/appeals', data);
export const getAppeals = () => api.get('/api/appeals');
export const reviewAppeal = (id, data) => api.put(`/api/appeals/${id}/review`, data);

// Admin
export const getStats = () => api.get('/api/admin/stats');
export const getReviewQueue = () => api.get('/api/admin/review-queue');
export const submitManualReview = (claimId, data) =>
  api.put(`/api/admin/review/${claimId}`, data);

// Evaluation
export const runEvaluation = () => api.post('/api/evaluation/run');
export const getEvalResults = () => api.get('/api/evaluation/results');

// Policy Configuration
export const getPolicy = () => api.get('/api/admin/policy');
export const updatePolicy = (data) => api.put('/api/admin/policy', data);

export default api;
