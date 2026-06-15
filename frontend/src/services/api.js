import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
  timeout: 30000,
});


// ── Auth token injection ──────────────────────────────────────────────────────
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});


// ── Auto logout on 401 ───────────────────────────────────────────────────────
API.interceptors.response.use(
  (res) => res,

  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');

      window.location.href = '/login';
    }

    return Promise.reject(err);
  }
);


// ── Existing endpoints ────────────────────────────────────────────────────────

export const getWeather = (location) =>
  API.get(`/weather?location=${encodeURIComponent(location)}`);


export const predictCrop = (data) =>
  API.post('/predict', data);


export const getRecommendations = (data) =>
  API.post('/recommend', data);


export const detectDisease = (formData) =>
  API.post('/detect-disease', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });


// ── Auth endpoints ────────────────────────────────────────────────────────────

export const register = (data) =>
  API.post('/auth/register', data);


export const login = (data) =>
  API.post('/auth/login', data);


export const getMe = () =>
  API.get('/auth/me');


// ── Prediction History endpoints ──────────────────────────────────────────────

export const getPredictions = (
  limit = 20,
  offset = 0
) =>
  API.get(`/history/predictions?limit=${limit}&offset=${offset}`);


export const getPrediction = (id) =>
  API.get(`/history/predictions/${id}`);


export const deletePrediction = (id) =>
  API.delete(`/history/predictions/${id}`);


// ── Recommendation History endpoints ──────────────────────────────────────────

export const getRecommendationsList = (
  limit = 20,
  offset = 0
) =>
  API.get(`/history/recommendations?limit=${limit}&offset=${offset}`);


export const getRecommendationById = (id) =>
  API.get(`/history/recommendations/${id}`);


export const deleteRecommendation = (id) =>
  API.delete(`/history/recommendations/${id}`);


// ── Disease History endpoints ─────────────────────────────────────────────────

export const getDiseaseHistory = (
  limit = 20,
  offset = 0
) =>
  API.get(`/history/disease?limit=${limit}&offset=${offset}`);


export const getDiseaseDetection = (id) =>
  API.get(`/history/disease/${id}`);


export const deleteDiseaseDetection = (id) =>
  API.delete(`/history/disease/${id}`);


// ── Stats ─────────────────────────────────────────────────────────────────────

export const getStats = () =>
  API.get('/history/stats');


// ── Auth helpers ──────────────────────────────────────────────────────────────

export const saveAuth = (data) => {
  localStorage.setItem('token', data.access_token);

  localStorage.setItem(
    'user',
    JSON.stringify({
      id: data.user_id,
      name: data.name,
      email: data.email,
      district: data.district,
    })
  );
};


export const clearAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};


export const getUser = () => {
  try {
    return JSON.parse(localStorage.getItem('user'));
  } catch {
    return null;
  }
};


export const isLoggedIn = () =>
  !!localStorage.getItem('token');