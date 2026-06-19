import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, FileText, UserRound, Upload } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { getProfile, completeOnboarding, parseResume, updateProfile } from '../lib/profile';
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

  useEffect(() => {
    if (user?.onboarded) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const handleFile = async (file: File) => {
    setLoading(true);
    try {
      const data = await parseResume(file);
      const parsed = data?.parsed || {};
      setForm({
        full_name: parsed.personal_info?.full_name || user?.name || '',
        email: parsed.personal_info?.email || user?.email || '',
        phone: parsed.personal_info?.phone || '',
        location: parsed.personal_info?.location || '',
        linkedin_url: parsed.personal_info?.linkedin_url || '',
        github_url: parsed.personal_info?.github_url || '',
        portfolio_url: parsed.personal_info?.portfolio_url || '',
        headline: parsed.headline || '',
        summary: parsed.summary || '',
        career_objective: parsed.career_objective || '',
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
              <span className="text-sm text-slate-600 dark:text-slate-300">PDF, DOCX, or DOC</span>
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
        <label className="glass-card flex cursor-pointer flex-col items-center gap-3 py-10">
          <FileText className="size-10 text-slate-400" />
          <span className="font-semibold text-slate-700 dark:text-slate-200">Click to upload resume</span>
          <span className="text-xs text-slate-500">PDF, DOCX, DOC up to 10MB</span>
          <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
        </label>
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
          < Field name="full_name" label="Full Name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} />
          < Field name="email" label="Email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
          < Field name="phone" label="Phone" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
          < Field name="location" label="Location" value={form.location} onChange={(v) => setForm({ ...form, location: v })} />
          < Field name="linkedin_url" label="LinkedIn URL" value={form.linkedin_url} onChange={(v) => setForm({ ...form, linkedin_url: v })} />
          < Field name="github_url" label="GitHub URL" value={form.github_url} onChange={(v) => setForm({ ...form, github_url: v })} />
          < Field name="portfolio_url" label="Portfolio" value={form.portfolio_url} onChange={(v) => setForm({ ...form, portfolio_url: v })} />
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

function Field({ name, label, value, onChange, textarea = false }: { name: string; label: string; value: string; onChange: (v: string) => void; textarea?: boolean }) {
  const input = (
    <input
      id={name}
      className="field-input"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={label}
    />
  );
  return (
    <div>
      <label className="field-label" htmlFor={name}>{label}</label>
      {textarea ? <textarea id={name} className="field-textarea" value={value} onChange={(e) => onChange(e.target.value)} /> : input}
    </div>
  );
}
