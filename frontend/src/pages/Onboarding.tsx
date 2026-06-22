import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Upload, UserRound } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { getProfile, completeOnboarding, parseResume, updateProfile, addEducation, addExperience, addProject, addSkill } from '../lib/profile';
import { ResumeDropzone } from '../components/ResumeDropzone';
import type { User } from '../lib/api';

export default function Onboarding() {
  const { user, setUser } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'choose' | 'upload' | 'manual'>('choose');
  const [form, setForm] = useState({
    full_name: '', email: '', phone: '', location: '', linkedin_url: '', github_url: '', portfolio_url: '', headline: '', summary: '', career_objective: '',
  });
  const [loading, setLoading] = useState(false);
  const [parsedData, setParsedData] = useState<any>(null);

  useEffect(() => {
    if (user?.onboarded) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const saveParsedSections = async (data: any) => {
    const token = localStorage.getItem('career_token');
    if (!token || !data) return;

    const extractValue = (field: any) => typeof field === 'object' && field?.value !== undefined ? field.value : (field || '');

    const savePromises: Promise<any>[] = [];

    if (Array.isArray(data.education)) {
      for (const edu of data.education) {
        if (edu.degree || edu.institution) {
          savePromises.push(
            fetch(`${import.meta.env.VITE_API_URL || '/api'}/profile/education`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                degree: extractValue(edu.degree),
                specialization: extractValue(edu.specialization),
                institution: extractValue(edu.institution),
                start_date: extractValue(edu.start_date),
                end_date: extractValue(edu.end_date),
                cgpa: extractValue(edu.cgpa),
                description: extractValue(edu.description),
              }),
            }).then(r => r.json()).catch(() => null)
          );
        }
      }
    }

    if (Array.isArray(data.experience)) {
      for (const exp of data.experience) {
        if (exp.title || exp.company) {
          savePromises.push(
            fetch(`${import.meta.env.VITE_API_URL || '/api'}/profile/experience`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                title: extractValue(exp.title),
                company: extractValue(exp.company),
                location: extractValue(exp.location),
                start_date: extractValue(exp.start_date),
                end_date: extractValue(exp.end_date),
                responsibilities: extractValue(exp.responsibilities),
                achievements: extractValue(exp.achievements),
              }),
            }).then(r => r.json()).catch(() => null)
          );
        }
      }
    }

    if (Array.isArray(data.projects)) {
      for (const proj of data.projects) {
        if (proj.project_name) {
          savePromises.push(
            fetch(`${import.meta.env.VITE_API_URL || '/api'}/profile/projects`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                project_name: extractValue(proj.project_name),
                description: extractValue(proj.description),
                technologies: extractValue(proj.technologies),
                github_url: extractValue(proj.github_url),
                live_url: extractValue(proj.live_url),
                start_date: extractValue(proj.start_date),
                end_date: extractValue(proj.end_date),
              }),
            }).then(r => r.json()).catch(() => null)
          );
        }
      }
    }

    const skills = data.skills || {};
    if (typeof skills === 'object' && !Array.isArray(skills)) {
      const skillEntries = Object.entries(skills).flatMap(([category, items]: [string, any]) =>
        (Array.isArray(items) ? items : []).map((name: string) => ({ skill_name: name, category }))
      );
      for (const skill of skillEntries) {
        if (skill.skill_name) {
          savePromises.push(
            fetch(`${import.meta.env.VITE_API_URL || '/api'}/profile/skills`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
              body: JSON.stringify(skill),
            }).then(r => r.json()).catch(() => null)
          );
        }
      }
    }

    if (savePromises.length > 0) {
      addToast(`Auto-saving ${savePromises.length} parsed items...`, 'info');
      await Promise.allSettled(savePromises);
    }
  };

  const handleFile = async (file: File) => {
    setLoading(true);
    try {
      const data = await parseResume(file);
      const parsed = data?.parsed || {};
      setParsedData(parsed);
      const getFieldValue = (field: any) => typeof field === 'object' && field?.value !== undefined ? field.value : (field || '');
      setForm({
        full_name: getFieldValue(parsed.personal_info?.full_name) || user?.name || '',
        email: getFieldValue(parsed.personal_info?.email) || user?.email || '',
        phone: getFieldValue(parsed.personal_info?.phone) || '',
        location: getFieldValue(parsed.personal_info?.location) || '',
        linkedin_url: getFieldValue(parsed.personal_info?.linkedin_url) || '',
        github_url: getFieldValue(parsed.personal_info?.github_url) || '',
        portfolio_url: getFieldValue(parsed.personal_info?.portfolio_url) || '',
        headline: getFieldValue(parsed.headline) || '',
        summary: getFieldValue(parsed.summary) || '',
        career_objective: getFieldValue(parsed.career_objective) || '',
      });
      setMode('manual');
      addToast('Resume parsed. Review and update the fields.', 'success');
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to parse resume', 'error');
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    setLoading(true);
    try {
      await updateProfile({ ...form });
      if (parsedData) {
        await saveParsedSections(parsedData);
      }
      await completeOnboarding();
      const updated = { ...(user || { id: Date.now(), name: '', email: '' } as User), onboarded: true } as User;
      setUser(updated);
      addToast('Profile saved', 'success');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to save profile', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (mode === 'choose') {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Onboarding</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight">Build your career profile</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-300">Choose how you'd like to get started.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <button
            onClick={() => setMode('upload')}
            className="glass-card flex items-center gap-4 text-left hover:border-primary-300"
          >
            <span className="flex size-12 items-center justify-center rounded-2xl bg-primary-500/10 text-primary-600"><Upload /></span>
            <span>
              <span className="block text-lg font-black">Upload Resume</span>
              <span className="text-sm text-slate-600 dark:text-slate-300">PDF, DOCX, or TXT</span>
            </span>
          </button>
          <button
            onClick={() => setMode('manual')}
            className="glass-card flex items-center gap-4 text-left hover:border-primary-300"
          >
            <span className="flex size-12 items-center justify-center rounded-2xl bg-primary-500/10 text-primary-600"><UserRound /></span>
            <span>
              <span className="block text-lg font-black">Fill Manually</span>
              <span className="text-sm text-slate-600 dark:text-slate-300">Enter your details</span>
            </span>
          </button>
        </div>
      </div>
    );
  }

  if (mode === 'upload') {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Onboarding</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight">Upload your resume</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-300">We'll extract and structure your profile.</p>
        </div>
        <ResumeDropzone
          onFile={handleFile}
          title="Drop resume or click to upload"
          description="PDF, DOCX, DOC, or TXT up to 10MB"
          accepted=".pdf,.docx,.doc,.txt"
          loading={loading}
        />
        <button className="btn-secondary w-full" onClick={() => setMode('choose')}>Back</button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Onboarding</p>
        <h1 className="mt-2 text-3xl font-black tracking-tight">Complete your profile</h1>
        <p className="mt-2 text-slate-600 dark:text-slate-300">Fill in the essentials. You can update later.</p>
      </div>
      <div className="glass-card space-y-5">
<div className="grid gap-5 sm:grid-cols-2">
           <Field name="full_name" label="Full Name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} />
           <Field name="email" label="Email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
           <Field name="phone" label="Phone" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
           <Field name="location" label="Location" value={form.location} onChange={(v) => setForm({ ...form, location: v })} />
           <Field name="linkedin_url" label="LinkedIn URL" value={form.linkedin_url} onChange={(v) => setForm({ ...form, linkedin_url: v })} />
           <Field name="github_url" label="GitHub URL" value={form.github_url} onChange={(v) => setForm({ ...form, github_url: v })} />
           <Field name="portfolio_url" label="Portfolio" value={form.portfolio_url} onChange={(v) => setForm({ ...form, portfolio_url: v })} />
        </div>
        <Field name="headline" label="Headline" value={form.headline} onChange={(v) => setForm({ ...form, headline: v })} textarea />
        <Field name="summary" label="Professional Summary" value={form.summary} onChange={(v) => setForm({ ...form, summary: v })} textarea />
        <Field name="career_objective" label="Career Objective" value={form.career_objective} onChange={(v) => setForm({ ...form, career_objective: v })} textarea />
        <div className="flex gap-3">
          <button className="btn-primary" disabled={loading} onClick={submit}>{loading ? 'Saving...' : 'Save and continue'}</button>
          <button className="btn-secondary" onClick={() => setMode('choose')} disabled={loading}>Back</button>
        </div>
      </div>
    </div>
  );
}

type FieldWithConfidence = string | { value: string; confidence: number };

interface FieldProps {
  name: string;
  label: string;
  value: FieldWithConfidence;
  confidence?: number;
  onChange: (v: string) => void;
  textarea?: boolean;
}

function ConfidenceDot({ confidence }: { confidence?: number }) {
  if (confidence === undefined) return null;
  const getColor = (conf: number) => {
    if (conf >= 0.9) return 'bg-green-500';
    if (conf >= 0.7) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  const getLabel = (conf: number) => {
    if (conf >= 0.9) return 'High confidence';
    if (conf >= 0.7) return 'Medium confidence';
    return 'Low confidence';
  };
  return (
    <span className={`inline-block size-2 rounded-full ${getColor(confidence)}`} title={getLabel(confidence)} />
  );
}

function Field({ name, label, value, confidence, onChange, textarea = false }: FieldProps) {
  const stringValue = typeof value === 'object' && value?.value !== undefined ? value.value : value;
  const fieldConfidence = typeof value === 'object' && value?.confidence !== undefined ? value.confidence : confidence;
  
  const input = (
    <div className="relative">
      <input
        id={name}
        className="field-input pr-8"
        value={stringValue}
        onChange={(e) => onChange(e.target.value)}
        placeholder={label}
      />
      {fieldConfidence !== undefined && (
        <span className="absolute right-2 top-1/2 -translate-y-1/2">
          <ConfidenceDot confidence={fieldConfidence} />
        </span>
      )}
    </div>
  );
  
  return (
    <div>
      <label className="field-label" htmlFor={name}>{label}</label>
      {textarea ? (
        <textarea 
          id={name} 
          className="field-textarea" 
          value={stringValue} 
          onChange={(e) => onChange(e.target.value)} 
        />
      ) : input}
    </div>
  );
}
