import axios from 'axios';

// All API requests go through the environment variable URL (for production) or /api (proxied to Django on port 8000)
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT access token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh token on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refresh = localStorage.getItem('refresh_token');
        const { data } = await axios.post(`${baseURL}/auth/token/refresh/`, { refresh });
        localStorage.setItem('access_token', data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ===== AUTH =====
export const authApi = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  logout: (refresh) => api.post('/auth/logout/', { refresh }),
  me: () => api.get('/auth/me/'),
  updateMe: (data) => api.patch('/auth/me/', data),
  searchUsers: (q) => api.get(`/auth/users/search/?q=${encodeURIComponent(q)}`),
};

// ===== GROUPS =====
export const groupsApi = {
  list: () => api.get('/groups/'),
  create: (data) => api.post('/groups/', data),
  get: (id) => api.get(`/groups/${id}/`),
  update: (id, data) => api.patch(`/groups/${id}/`, data),
  delete: (id) => api.delete(`/groups/${id}/`),
  addMember: (groupId, data) => api.post(`/groups/${groupId}/members/`, data),
  updateMembership: (groupId, membershipId, data) =>
    api.patch(`/groups/${groupId}/members/${membershipId}/`, data),
  removeMembership: (groupId, membershipId) =>
    api.delete(`/groups/${groupId}/members/${membershipId}/`),
};

// ===== EXPENSES =====
export const expensesApi = {
  list: (groupId, params = {}) => api.get(`/expenses/${groupId}/`, { params }),
  create: (groupId, data) => api.post(`/expenses/${groupId}/`, data),
  get: (groupId, expenseId) => api.get(`/expenses/${groupId}/${expenseId}/`),
  update: (groupId, expenseId, data) => api.patch(`/expenses/${groupId}/${expenseId}/`, data),
  delete: (groupId, expenseId) => api.delete(`/expenses/${groupId}/${expenseId}/`),
};

// ===== BALANCES =====
export const balancesApi = {
  get: (groupId) => api.get(`/expenses/${groupId}/balances/`),
  breakdown: (groupId) => api.get(`/expenses/${groupId}/balances/breakdown/`),
};

// ===== SETTLEMENTS =====
export const settlementsApi = {
  list: (groupId) => api.get(`/expenses/${groupId}/settlements/`),
  create: (groupId, data) => api.post(`/expenses/${groupId}/settlements/`, data),
  delete: (groupId, settlementId) => api.delete(`/expenses/${groupId}/settlements/${settlementId}/`),
};

// ===== CURRENCY =====
export const currencyApi = {
  getRate: (from = 'USD', to = 'INR') =>
    api.get(`/expenses/exchange-rate/?from=${from}&to=${to}`),
};

// ===== IMPORT =====
export const importApi = {
  upload: (groupId, formData) =>
    api.post(`/import/${groupId}/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  listReports: (groupId) => api.get(`/import/${groupId}/reports/`),
  getReport: (groupId, reportId) => api.get(`/import/${groupId}/reports/${reportId}/`),
  resolveAnomaly: (groupId, reportId, anomalyId, data) =>
    api.patch(`/import/${groupId}/reports/${reportId}/anomalies/${anomalyId}/`, data),
  approveAuto: (groupId, reportId) =>
    api.post(`/import/${groupId}/reports/${reportId}/approve-auto/`),
  finalize: (groupId, reportId, rowDecisions) =>
    api.post(`/import/${groupId}/reports/${reportId}/finalize/`, { row_decisions: rowDecisions }),
};

