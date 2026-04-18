import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:8000';
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('promanage_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('promanage_token');
      localStorage.removeItem('promanage_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// Auth
export const authAPI = {
  login: (identifier, password) => api.post('/auth/login', { identifier, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

// Users
export const usersAPI = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  changePassword: (id, data) => api.put(`/users/${id}/password`, data),
  delete: (id) => api.delete(`/users/${id}`),
  getByRole: (role) => api.get('/users/role', { params: { role } }),
};

// Projects
export const projectsAPI = {
  getAll: () => api.get('/projects'),
  getById: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

// Tasks
export const tasksAPI = {
  getAll: (projectId) => api.get('/tasks', { params: projectId ? { projectId } : {} }),
  create: (data) => api.post('/tasks', data),
  update: (id, data) => api.patch(`/tasks/${id}`, data),
};

// Subtasks
export const subtasksAPI = {
  getAll: (taskId) => api.get('/subtasks', { params: taskId ? { taskId } : {} }),
  create: (data) => api.post('/subtasks', data),
  update: (id, data) => api.put(`/subtasks/${id}`, data),
  delete: (id) => api.delete(`/subtasks/${id}`),
};

// Comments
export const commentsAPI = {
  getByTask: (taskId) => api.get('/comments', { params: { taskId } }),
  create: (data) => api.post('/comments', data),
};

// Notifications
export const notificationsAPI = {
  getAll: () => api.get('/notifications'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
};

// WhatsApp
export const whatsappAPI = {
  getStatus: () => api.get('/whatsapp/status'),
};

// Stats
export const statsAPI = {
  get: () => api.get('/stats'),
};

export default api;
