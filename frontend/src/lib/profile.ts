import axios from 'axios';
import { getErrorMessage } from '../utils';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('career_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function getProfile() {
  const response = await api.get('/profile');
  return response.data;
}

export async function updateProfile(data: Record<string, unknown>) {
  const response = await api.put('/profile', data);
  return response.data;
}

export async function completeOnboarding() {
  const response = await api.post('/profile/onboarding', { onboarded: true });
  return response.data;
}

export async function parseResume(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/profile/parse-resume', formData);
  return response.data;
}

export async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/profile/upload-resume', formData);
  return response.data;
}

export async function compareResume(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/profile/compare-resume', formData);
  return response.data;
}
