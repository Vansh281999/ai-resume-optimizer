import { api } from './api';

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

export async function getResumeHistory() {
  const response = await api.get('/profile/resume-history');
  return response.data;
}

export async function addEducation(payload: Record<string, unknown>) {
  const response = await api.post('/profile/education', payload);
  return response.data;
}

export async function addExperience(payload: Record<string, unknown>) {
  const response = await api.post('/profile/experience', payload);
  return response.data;
}

export async function addProject(payload: Record<string, unknown>) {
  const response = await api.post('/profile/projects', payload);
  return response.data;
}

export async function addSkill(payload: Record<string, unknown>) {
  const response = await api.post('/profile/skills', payload);
  return response.data;
}

export async function addCertification(payload: Record<string, unknown>) {
  const response = await api.post('/profile/certifications', payload);
  return response.data;
}

export async function updateJobPreferences(payload: Record<string, unknown>) {
  const response = await api.post('/profile/job-preferences', payload);
  return response.data;
}
