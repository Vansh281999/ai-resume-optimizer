import { FormEvent, useState } from 'react';
import { AlertTriangle, Briefcase, CheckCircle2, Search, Sparkles, Target } from 'lucide-react';
import { useJobMatchMutation } from '../hooks/mutations';
import { formatScore, parseCommaSeparated } from '../lib/utils';
import { useToast } from '../contexts/ToastContext';

export function JobMatch() {
  const { addToast } = useToast();
  const jobMatch = useJobMatchMutation();
  const [resumeText, setResumeText] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [keywords, setKeywords] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!resumeText.trim() || !jobDescription.trim()) {
      addToast('Paste both resume text and the job description.', 'error');
      return;
    }
    await jobMatch.submit(resumeText, jobDescription, parseCommaSeparated(keywords));
  };

  const result = jobMatch.data;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form onSubmit={handleSubmit} className="glass-card space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Job match</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight">Compare your resume to a target role.</h2>
          <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Paste a job description to reveal match strength, missing skills, recommended keywords, and detailed match notes.</p>
        </div>

        <div>
          <label className="field-label" htmlFor="resume">Resume text</label>
          <textarea
            id="resume"
            className="field-textarea"
            value={resumeText}
            placeholder="Paste your resume text..."
            onChange={(event) => setResumeText(event.target.value)}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="jd">Job description</label>
          <textarea
            id="jd"
            className="field-textarea"
            value={jobDescription}
            placeholder="Paste the job description..."
            onChange={(event) => setJobDescription(event.target.value)}
          />
        </div>

        <div>
          <label className="field-label" htmlFor="keywords">Additional job keywords</label>
          <input
            id="keywords"
            className="field-input"
            value={keywords}
            placeholder="Kubernetes, Python, stakeholder management"
            onChange={(event) => setKeywords(event.target.value)}
          />
        </div>

        <button className="btn-primary w-full" type="submit" disabled={jobMatch.loading}>
          {jobMatch.loading ? 'Matching role...' : 'Analyze job match'}
          {!jobMatch.loading && <Search className="size-5" />}
        </button>

        {jobMatch.error && (
          <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
            <AlertTriangle className="mt-0.5 size-5 shrink-0" />
            {jobMatch.error}
          </div>
        )}
      </form>

      <div className="space-y-6">
        <div className="glass-card">
          <div className="flex items-center gap-4">
            <div className="flex size-14 items-center justify-center rounded-3xl bg-primary-500/10 text-primary-600 dark:text-primary-300">
              <Briefcase className="size-7" />
            </div>
            <div>
              <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Match report</p>
              <h3 className="text-2xl font-black">Resume vs. job description</h3>
            </div>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {[
              ['Overall match', result?.overall_match_score],
              ['Skill match', result?.skill_match_score],
              ['Experience match', result?.experience_match_score],
            ].map(([label, value]) => (
              <div key={label} className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
                <p className="text-sm font-bold text-slate-500 dark:text-slate-400">{label}</p>
                <p className="mt-2 text-4xl font-black">{formatScore(value)}</p>
              </div>
            ))}
          </div>
        </div>

        {result ? (
          <>
            <div className="glass-card">
              <div className="mb-5 flex items-center gap-3">
                <AlertTriangle className="size-6 text-amber-500" />
                <h3 className="text-xl font-black">Missing skills</h3>
              </div>
              {result.missing_skills.length > 0 ? (
                <div className="flex flex-wrap gap-3">
                  {result.missing_skills.map((skill) => (
                    <span key={skill} className="rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-black text-amber-950 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 font-semibold text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">No missing skills detected.</p>
              )}
            </div>

            <div className="glass-card">
              <div className="mb-5 flex items-center gap-3">
                <Sparkles className="size-6 text-primary-500" />
                <h3 className="text-xl font-black">Recommended keywords</h3>
              </div>
              {result.recommended_keywords.length > 0 ? (
                <div className="flex flex-wrap gap-3">
                  {result.recommended_keywords.map((keyword) => (
                    <span key={keyword} className="rounded-full border border-primary-200 bg-primary-50 px-4 py-2 text-sm font-black text-primary-950 dark:border-primary-900 dark:bg-primary-950 dark:text-primary-100">
                      {keyword}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">No recommended keywords were returned.</p>
              )}
            </div>

              <div className="glass-card">
                <div className="mb-5 flex items-center gap-3">
                  <Target className="size-6 text-emerald-500" />
                  <h3 className="text-xl font-black">Match details</h3>
                </div>
                {result.match_details && Object.keys(result.match_details).length > 0 ? (
                  <ul className="space-y-3">
                    {Object.entries(result.match_details).map(([key, value]) => (
                      <li key={key} className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm font-semibold leading-6 dark:border-slate-800 dark:bg-slate-950">
                        <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-500" />
                        <span className="flex-1">{key}</span>
                        <span className="text-emerald-700 dark:text-emerald-300">{typeof value === 'number' ? value.toFixed(1) : value}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">No match details were returned.</p>
                )}
              </div>
          </>
        ) : (
          <div className="glass-card">
            <div className="flex min-h-80 flex-col items-center justify-center text-center">
              <Briefcase className="mb-5 size-16 text-slate-300 dark:text-slate-700" />
              <h3 className="text-2xl font-black">No match report yet</h3>
              <p className="mt-3 max-w-md leading-7 text-slate-500 dark:text-slate-400">Submit your resume and a job description to get a tailored match score and application recommendations.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
