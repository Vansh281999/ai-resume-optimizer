import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

export interface User {
  id: number | string;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AtsScoreResponse {
  overall_score: number;
  keyword_density_score: number;
  formatting_risk_score: number;
  missing_sections: string[];
  found_sections: string[];
  critical_issues: string[];
  improvement_suggestions: string[];
  focus_areas: Array<{ name: string; score: number }>;
}

export interface JobMatchResponse {
  overall_match_score: number;
  skill_match_score: number;
  experience_match_score: number;
  missing_skills: string[];
  recommended_keywords: string[];
  match_details: Record<string, number>;
}

export interface InterviewQuestion {
  question: string;
  category?: string;
  difficulty?: string;
}

export interface InterviewResponse {
  company: string;
  role: string;
  technical_questions: (string | InterviewQuestion)[];
  behavioral_questions: (string | InterviewQuestion)[];
  company_specific_questions: (string | InterviewQuestion)[];
  preparation_tips: string[];
}

export interface SkillProgression {
  skill_name: string;
  current_level: number;
  target_level: number;
  learning_resources: string[];
  estimated_months?: number;
}

export interface CareerRoadmapResponse {
  current_role: string;
  target_role: string;
  skill_progressions: SkillProgression[];
  estimated_timeline_months: number;
  salary_progression: { entry?: number; mid?: number; senior?: number; currency?: string };
}

export interface MetricWindow {
  window_days: number;
  count: number;
  average: number;
  min: number;
  max: number;
}

export interface TrendHistoryItem {
  date: string;
  score: number;
  type?: 'ats' | 'match';
}

export interface AnalyticsTrendsResponse {
  ats: MetricWindow;
  match: MetricWindow;
  history: TrendHistoryItem[];
}

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('career_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    const message = error.response?.data?.detail || error.response?.data?.message || error.message;
    return Promise.reject(new Error(message));
  },
);

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/auth/login', { email, password });
  return response.data;
}

export async function signup(name: string, email: string, password: string): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/auth/signup', { name, email, password });
  return response.data;
}

export async function updateProfile(name: string, email: string): Promise<{ id: string; name: string; email: string; created_at: string }> {
  const response = await api.patch('/auth/me', { name, email });
  return response.data;
}


export async function scoreResume(resumeText: string, jobKeywords?: string[]): Promise<AtsScoreResponse> {
  const response = await api.post<AtsScoreResponse>('/ats/score', { resume_text: resumeText, job_keywords: jobKeywords });
  return response.data;
}

export async function uploadResume(file: File, additionalText?: string, keywords?: string[]): Promise<AtsScoreResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (additionalText) {
    formData.append('additional_text', additionalText);
  }
  if (keywords && keywords.length > 0) {
    formData.append('keywords', keywords.join(','));
  }
  const response = await api.post<AtsScoreResponse>('/ats/upload', formData);
  return response.data;
}

export async function matchJob(
  resumeText: string,
  jobDescription: string,
  jobKeywords?: string[],
): Promise<JobMatchResponse> {
  const response = await api.post<JobMatchResponse>('/jobs/match', {
    resume_text: resumeText,
    job_description: jobDescription,
    job_keywords: jobKeywords,
  });
  return response.data;
}

export async function generateInterview(
  company: string,
  role: string,
  jobDescription: string,
): Promise<InterviewResponse> {
  const response = await api.post<InterviewResponse>('/interview/generate', {
    company,
    role,
    job_description: jobDescription,
  });
  return response.data;
}

export async function generateAnswer(
  question: string,
  category: 'technical' | 'behavioral' | 'company' | 'interview',
  context?: Record<string, string>,
): Promise<string> {
  const response = await api.post<{ answer: string }>('/interview/answer', {
    question,
    category,
    context,
  });
  return response.data.answer;
}

export async function getCareerRoadmap(
  currentSkills: string[],
  targetRole: string,
  context: string,
): Promise<CareerRoadmapResponse> {
  const response = await api.post<CareerRoadmapResponse>('/career/roadmap', {
    current_skills: currentSkills,
    target_role: targetRole,
    context,
  });
  return response.data;
}

export async function getTrends(): Promise<AnalyticsTrendsResponse> {
  const response = await api.get<AnalyticsTrendsResponse>('/analytics/trends');
  return response.data;
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>('/auth/forgot-password', { email });
  return response.data;
}

export async function resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>('/auth/reset-password', { token, new_password: newPassword });
  return response.data;
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
  const response = await api.patch<{ message: string }>('/auth/change-password', { current_password: currentPassword, new_password: newPassword });
  return response.data;
}


export async function scanSecrets(text: string): Promise<{ findings_count: number; redacted_length: number }> {
  const response = await api.post<{ findings_count: number; redacted_length: number }>('/security/scan', { text });
  return response.data;
}

export async function getFocusAreas(): Promise<{ focus_areas: Array<{ name: string; score: number }> }> {
  const response = await api.get<{ focus_areas: Array<{ name: string; score: number }> }>('/analytics/focus-areas');
  return response.data;
}

export async function getHealth(): Promise<{ status: string; timestamp: string }> {
  const response = await api.get<{ status: string; timestamp: string }>('/health');
  return response.data;
}

export interface AiProviderStatus {
  installed: boolean;
  configured: boolean;
  status: string;
}

export interface AiHealthResponse {
  openai: AiProviderStatus;
  anthropic: AiProviderStatus;
  gemini: AiProviderStatus;
  ollama: AiProviderStatus;
  openrouter: AiProviderStatus;
  groq: AiProviderStatus;
}

export async function getAiHealth(): Promise<AiHealthResponse> {
  const response = await api.get<AiHealthResponse>('/health/ai');
  return response.data;
}

export interface JobPosting {
  id: string;
  source: string;
  title: string;
  company: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  skills: string[];
  experience_level?: string;
  remote: boolean;
  posted_at?: string;
  url?: string;
}

export interface SkillDemand {
  skill: string;
  demand_score: number;
  job_count: number;
  sources: string[];
  period: string;
  trend: string;
}

export interface MarketTrend {
  role: string;
  avg_salary: number | null;
  demand_score: number;
  growth_rate: number;
  sample_size: number;
}

export interface MarketResponse<T> {
  source: string[];
  fetched_at: string;
  confidence: number;
  data: T;
  error: string | null;
}

export async function getMarketJobs(title: string): Promise<MarketResponse<JobPosting[]>> {
  const response = await api.get<MarketResponse<JobPosting[]>>('/market/jobs', { params: { title } });
  return response.data;
}

export async function getMarketSkills(title: string): Promise<MarketResponse<Record<string, SkillDemand>>> {
  const response = await api.get<MarketResponse<Record<string, SkillDemand>>>('/market/skills', { params: { title } });
  return response.data;
}

export async function getMarketTrends(title: string): Promise<MarketResponse<MarketTrend>> {
  const response = await api.get<MarketResponse<MarketTrend>>('/market/trends', { params: { title } });
  return response.data;
}
