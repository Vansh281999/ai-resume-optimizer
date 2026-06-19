import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Upload, User, Briefcase, Code, FolderGit2, GraduationCap, Award, Target, Plus, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { getProfile, updateProfile, uploadResume, compareResume, getResumeHistory, addEducation, addExperience, addProject, addSkill, addCertification, updateJobPreferences } from '../lib/profile';
import ReactMarkdown from 'react-markdown';

type Tab = 'personal' | 'education' | 'experience' | 'projects' | 'skills' | 'certifications' | 'preferences' | 'resume';

export default function ProfileSettings() {
  const { user, setUser } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('personal');
  const [profile, setProfile] = useState<any>(null);
  const [education, setEducation] = useState<any[]>([]);
  const [experience, setExperience] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [certifications, setCertifications] = useState<any[]>([]);
  const [jobPrefs, setJobPrefs] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [resumeHistory, setResumeHistory] = useState<any[]>([]);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadProfile();
  }, []);

  const validateEmail = (value: string) => {
    if (!value) return '';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Invalid email';
    return '';
  };

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await getProfile();
      setProfile(data.profile);
      setEducation(data.education || []);
      setExperience(data.experience || []);
      setProjects(data.projects || []);
      setSkills(data.skills || []);
      setCertifications(data.certifications || []);
      setJobPrefs(data.job_preferences);
      const history = await getResumeHistory();
      setResumeHistory(history.history || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to load profile', 'error');
    } finally {
      setLoading(false);
    }
  };

  const validate = (section: string, values: Record<string, unknown>) => {
    const next: Record<string, string> = {};
    if (section === 'personal') {
      const emailErr = validateEmail((values.email as string) || '');
      if (emailErr) next.email = emailErr;
      if (!(values.full_name as string)?.trim()) next.full_name = 'Required';
      if (!(values.email as string)?.trim()) next.email = 'Required';
    }
    if (section === 'education') {
      if (!(values.degree as string)?.trim()) next.degree = 'Required';
      if (!(values.institution as string)?.trim()) next.institution = 'Required';
    }
    if (section === 'experience') {
      if (!(values.title as string)?.trim()) next.title = 'Required';
      if (!(values.company as string)?.trim()) next.company = 'Required';
    }
    if (section === 'projects') {
      if (!(values.project_name as string)?.trim()) next.project_name = 'Required';
    }
    if (section === 'skills') {
      if (!(values.skill_name as string)?.trim()) next.skill_name = 'Required';
      if (!(values.category as string)?.trim()) next.category = 'Required';
    }
    if (section === 'certifications') {
      if (!(values.certification_name as string)?.trim()) next.certification_name = 'Required';
    }
    setFormErrors(next);
    return Object.keys(next).length === 0;
  };

  const saveSection = async (section: string, payload: Record<string, unknown>) => {
    if (!validate(section, payload)) return;
    setLoading(true);
    try {
      const data = await updateProfile(payload);
      setProfile(data.profile);
      addToast('Saved', 'success');
      setFormErrors({});
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to save', 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveSubResource = async (section: string, payload: Record<string, unknown>) => {
    if (!validate(section, payload)) return;
    setLoading(true);
    try {
      switch (section) {
        case 'education':
          await addEducation(payload);
          setEducation((current) => [...current, { ...(payload as any), id: `edu_${Date.now()}` }]);
          break;
        case 'experience':
          await addExperience(payload);
          setExperience((current) => [...current, { ...(payload as any), id: `exp_${Date.now()}` }]);
          break;
        case 'projects':
          await addProject(payload);
          setProjects((current) => [...current, { ...(payload as any), id: `proj_${Date.now()}` }]);
          break;
        case 'skills':
          await addSkill(payload);
          setSkills((current) => [...current, { ...(payload as any), id: `skill_${Date.now()}` }]);
          break;
        case 'certifications':
          await addCertification(payload);
          setCertifications((current) => [...current, { ...(payload as any), id: `cert_${Date.now()}` }]);
          break;
        case 'preferences':
          await updateJobPreferences(payload);
          setJobPrefs({ ...(jobPrefs || {}), ...(payload as Record<string, unknown>) });
          break;
        default:
          break;
      }
      addToast('Saved', 'success');
      setFormErrors({});
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to save', 'error');
    } finally {
      setLoading(false);
    }
  };

  const removeItem = (section: string, id?: string) => {
    if (!id) return;
    const setter = (fn: (items: any[]) => any[]) => fn((current) => current.filter((item: any) => item.id !== id));
    switch (section) {
      case 'education': setEducation((current) => current.filter((item) => (item.id || item.id) !== id)); break;
      case 'experience': setExperience((current) => current.filter((item) => (item.id || item.id) !== id)); break;
      case 'projects': setProjects((current) => current.filter((item) => (item.id || item.id) !== id)); break;
      case 'skills': setSkills((current) => current.filter((item) => (item.id || item.id) !== id)); break;
      case 'certifications': setCertifications((current) => current.filter((item) => (item.id || item.id) !== id)); break;
      default: break;
    }
    addToast('Removed (refresh to sync)', 'info');
  };

  const handleResumeUpload = async (file: File) => {
    setLoading(true);
    try {
      await uploadResume(file);
      addToast('Resume uploaded', 'success');
      await loadProfile();
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Upload failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResumeCompare = async (file: File) => {
    setLoading(true);
    try {
      const data = await compareResume(file);
      setCompareResult(data);
      addToast('Comparison ready', 'success');
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Compare failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: Tab; label: string; icon: typeof User }[] = [
    { id: 'personal', label: 'Personal', icon: User },
    { id: 'education', label: 'Education', icon: GraduationCap },
    { id: 'experience', label: 'Experience', icon: Briefcase },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    { id: 'skills', label: 'Skills', icon: Code },
    { id: 'certifications', label: 'Certifications', icon: Award },
    { id: 'preferences', label: 'Preferences', icon: Target },
    { id: 'resume', label: 'Resume', icon: FileText },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Profile</p>
        <h1 className="mt-2 text-3xl font-black tracking-tight">Profile settings</h1>
        <p className="mt-2 text-slate-600 dark:text-slate-300">Manage your career profile</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-semibold transition ${
              tab === t.id ? 'bg-primary-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-950 dark:text-slate-200'
            }`}
          >
            <t.icon className="size-4" />
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="glass-card py-10 text-center text-sm font-semibold text-slate-500">Loading...</div>
      ) : (
        <div className="glass-card space-y-5">
          {tab === 'personal' && (
            <div className="grid gap-5 sm:grid-cols-2">
              {[
                { key: 'full_name', label: 'Full name' },
                { key: 'email', label: 'Email' },
                { key: 'phone', label: 'Phone' },
                { key: 'location', label: 'Location' },
                { key: 'linkedin_url', label: 'LinkedIn' },
                { key: 'github_url', label: 'GitHub' },
                { key: 'portfolio_url', label: 'Portfolio' },
              ].map((field) => (
                <div key={field.key}>
                  <label className="field-label" htmlFor={`profile-${field.key}`}>{field.label}</label>
                  <input
                    id={`profile-${field.key}`}
                    className="field-input"
                    value={(profile as any)?.[field.key] || ''}
                    onChange={(e) => setProfile({ ...(profile || {}), [field.key]: e.target.value })}
                  />
                </div>
              ))}
              {[
                { key: 'headline', label: 'Headline', textarea: true },
                { key: 'summary', label: 'Summary', textarea: true },
                { key: 'career_objective', label: 'Career objective', textarea: true },
              ].map((field) => (
                <div key={field.key} className="sm:col-span-2">
                  <label className="field-label" htmlFor={`profile-${field.key}`}>{field.label}</label>
                  <textarea
                    id={`profile-${field.key}`}
                    className="field-textarea"
                    value={(profile as any)?.[field.key] || ''}
                    onChange={(e) => setProfile({ ...(profile || {}), [field.key]: e.target.value })}
                  />
                </div>
              ))}
              <div className="sm:col-span-2">
                <button className="btn-primary" disabled={loading} onClick={() => saveSection('personal', profile)}>Save personal info</button>
              </div>
            </div>
          )}

          {tab === 'education' && (
            <div className="space-y-4">
              {education.map((item, idx) => (
                <div key={item.id || idx} className="grid gap-4 rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                  <p className="font-semibold">{item.degree} — {item.institution}</p>
                  <p className="text-sm text-slate-600">{item.start_date} to {item.end_date}</p>
                </div>
              ))}
              <p className="text-sm text-slate-500">Education management form coming soon. Use onboarding for now.</p>
            </div>
          )}

          {tab === 'experience' && (
            <div className="space-y-4">
              {experience.map((item, idx) => (
                <div key={item.id || idx} className="grid gap-4 rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                  <p className="font-semibold">{item.title} at {item.company}</p>
                  <p className="text-sm text-slate-600">{item.start_date} to {item.end_date}</p>
                </div>
              ))}
              <p className="text-sm text-slate-500">Experience management form coming soon.</p>
            </div>
          )}

          {tab === 'projects' && (
            <div className="space-y-4">
              {projects.map((item, idx) => (
                <div key={item.id || idx} className="grid gap-4 rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                  <p className="font-semibold">{item.project_name}</p>
                  <p className="text-sm text-slate-600">{item.technologies}</p>
                </div>
              ))}
              <p className="text-sm text-slate-500">Projects management form coming soon.</p>
            </div>
          )}

          {tab === 'skills' && (
            <div className="space-y-4">
              {skills.map((item, idx) => (
                <div key={item.id || idx} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                  <p className="font-semibold">{item.skill_name}</p>
                  <p className="text-xs uppercase tracking-wide text-slate-500">{item.category}</p>
                </div>
              ))}
              <p className="text-sm text-slate-500">Skills management form coming soon.</p>
            </div>
          )}

          {tab === 'certifications' && (
            <div className="space-y-4">
              {certifications.map((item, idx) => (
                <div key={item.id || idx} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                  <p className="font-semibold">{item.certification_name}</p>
                  <p className="text-xs uppercase tracking-wide text-slate-500">{item.issuer}</p>
                </div>
              ))}
              <p className="text-sm text-slate-500">Certifications management form coming soon.</p>
            </div>
          )}

          {tab === 'preferences' && (
            <div className="grid gap-5 sm:grid-cols-2">
              {[
                { key: 'preferred_roles', label: 'Preferred roles' },
                { key: 'preferred_locations', label: 'Preferred locations' },
                { key: 'work_mode', label: 'Work mode' },
              ].map((field) => (
                <div key={field.key}>
                  <label className="field-label" htmlFor={`job-${field.key}`}>{field.label}</label>
                  <input
                    id={`job-${field.key}`}
                    className="field-input"
                    value={(jobPrefs as any)?.[field.key] || ''}
                    onChange={(e) => setJobPrefs({ ...(jobPrefs || {}), [field.key]: e.target.value })}
                  />
                </div>
              ))}
              <div className="sm:col-span-2">
                <button className="btn-primary" disabled={loading} onClick={() => saveSection('preferences', jobPrefs)}>Save preferences</button>
              </div>
            </div>
          )}

          {tab === 'resume' && (
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="glass-card flex cursor-pointer flex-col items-center gap-3 py-8">
                  <Upload className="size-8 text-primary-600" />
                  <span className="font-semibold">Upload new resume</span>
                  <span className="text-xs text-slate-500">PDF, DOCX, DOC</span>
                  <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={(e) => e.target.files?.[0] && handleResumeUpload(e.target.files[0])} />
                </label>
                <label className="glass-card flex cursor-pointer flex-col items-center gap-3 py-8">
                  <FileText className="size-8 text-primary-600" />
                  <span className="font-semibold">Compare with current profile</span>
                  <span className="text-xs text-slate-500">See suggested changes</span>
                  <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={(e) => e.target.files?.[0] && handleResumeCompare(e.target.files[0])} />
                </label>
              </div>

              {compareResult && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                  <p className="mb-2 font-semibold">Suggested changes</p>
                  <div className="prose prose-slate max-w-none text-sm dark:prose-invert">
                    <ReactMarkdown>{JSON.stringify(compareResult.changes, null, 2)}</ReactMarkdown>
                  </div>
                </div>
              )}

              <div>
                <p className="mb-2 font-semibold">Upload history</p>
                {resumeHistory.length === 0 ? (
                  <p className="text-sm text-slate-500">No resumes uploaded yet.</p>
                ) : (
                  <ul className="space-y-2">
                    {resumeHistory.map((version: any) => (
                      <li key={version.id} className="flex items-center justify-between rounded-2xl border border-slate-200 p-3 dark:border-slate-800">
                        <span className="text-sm font-semibold">{version.original_filename || 'resume'}</span>
                        <span className="text-xs text-slate-500">v{version.version_number}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
