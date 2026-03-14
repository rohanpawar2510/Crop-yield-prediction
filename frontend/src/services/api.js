import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export const getWeather = (location) =>
  API.get(`/weather?location=${encodeURIComponent(location)}`);

export const predictCrop = (data) =>
  API.post('/predict', data);

export const getRecommendations = (data) =>
  API.post('/recommend', data);

export const detectDisease = (formData) =>
  API.post('/detect-disease', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
