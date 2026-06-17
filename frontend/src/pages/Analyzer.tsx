import { FormEvent, useRef, useState } from 'react';
import { AlertTriangle, CheckCircle2, ClipboardCheck, FileUp, ListChecks, Sparkles, UploadCloud } from 'lucide-react';
import { useAtsScoreMutation } from '../hooks/mutations';
import { formatScore, parseCommaSeparated } from '../lib/utils';
import { useToast } from '../contexts/ToastContext';

export function Analyzer() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useToast();
  const atsMutation = useAtsScoreMutation();
  const [resumeText, setResumeText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [keywords, setKeywords] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile && !resumeText.trim()) {
      addToast('Paste resume text or upload a resume file before scoring.', 'error');
      return;
    }
    await atsMutation.submit(resumeText, selectedFile, parseCommaSeparated(keywords));
  };

  const result = atsMutation.data;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <form onSubmit={handleSubmit} className="glass-card space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">ATS analyzer</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight">Score your resume against ATS requirements.</h2>
          <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Paste your resume text or upload a file, then add target job keywords to get missing sections, risks, and improvement suggestions.</p>
        </div>

        <div>
          <label className="field-label" htmlFor="resumeText">Resume text</label>
          <textarea
            id="resumeText"
            className="field-textarea"
            value={resumeText}
            placeholder="Paste your resume text here..."
            onChange={(event) => setResumeText(event.target.value)}
          />
        </div>

        <div>
          <label className="field-label">Resume file</label>
          <button
            type="button"
            className="btn-secondary mt-2 w-full"
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud className="size-5" />
            {selectedFile ? `Replace ${selectedFile.name}` : 'Upload resume'}
          </button>
          <input
            ref={fileInputRef}
            className="sr-only"
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
          />
          {selectedFile && <p className="mt-3 text-sm font-semibold text-slate-500 dark:text-slate-400">Selected: {selectedFile.name}</p>}
        </div>

        <div>
          <label className="field-label" htmlFor="keywords">Target job keywords</label>
          <input
            id="keywords"
            className="field-input"
            value={keywords}
            placeholder="React, TypeScript, AWS, CI/CD"
            onChange={(event) => setKeywords(event.target.value)}
          />
          <p className="mt-2 text-xs font-semibold text-slate-500 dark:text-slate-400">Separate keywords with commas. This field is optional.</p>
        </div>

        <button className="btn-primary w-full" type="submit" disabled={atsMutation.loading}>
          {atsMutation.loading ? 'Analyzing resume...' : 'Run ATS analysis'}
          {!atsMutation.loading && <ClipboardCheck className="size-5" />}
        </button>

        {atsMutation.error && (
          <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
            <AlertTriangle className="mt-0.5 size-5 shrink-0" />
            {atsMutation.error}
          </div>
        )}
      </form>

      <div className="space-y-6">
        <div className="glass-card">
          <div className="flex items-center gap-4">
            <div className="flex size-14 items-center justify-center rounded-3xl bg-primary-500/10 text-primary-600 dark:text-primary-300">
              <FileUp className="size-7" />
            </div>
            <div>
              <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Current analysis</p>
              <h3 className="text-2xl font-black">Resume readiness report</h3>
            </div>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {[
              ['Overall ATS', result?.overall_score],
              ['Keyword density', result?.keyword_density_score],
              ['Formatting risk', result?.formatting_risk_score],
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
                <ListChecks className="size-6 text-emerald-500" />
                <h3 className="text-xl font-black">Found sections</h3>
              </div>
              {result.found_sections.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {result.found_sections.map((section) => (
                    <div key={section} className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 font-semibold text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">
                      <CheckCircle2 className="size-5 shrink-0" />
                      {section}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">No found sections were returned.</p>
              )}
            </div>

            <div className="glass-card">
              <div className="mb-5 flex items-center gap-3">
                <AlertTriangle className="size-6 text-amber-500" />
                <h3 className="text-xl font-black">Missing sections</h3>
              </div>
              {result.missing_sections.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {result.missing_sections.map((section) => (
                    <div key={section} className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 font-semibold text-amber-950 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
                      <AlertTriangle className="size-5 shrink-0" />
                      {section}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 font-semibold text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">All expected sections were found.</p>
              )}
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="glass-card">
                <div className="mb-5 flex items-center gap-3">
                  <AlertTriangle className="size-6 text-rose-500" />
                  <h3 className="text-xl font-black">Critical issues</h3>
                </div>
                {result.critical_issues.length > 0 ? (
                  <ul className="space-y-3">
                    {result.critical_issues.map((issue) => (
                      <li key={issue} className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold leading-6 text-rose-900 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-100">
                        {issue}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">No critical issues detected.</p>
                )}
              </div>

              <div className="glass-card">
                <div className="mb-5 flex items-center gap-3">
                  <Sparkles className="size-6 text-primary-500" />
                  <h3 className="text-xl font-black">Improvement suggestions</h3>
                </div>
                {result.improvement_suggestions.length > 0 ? (
                  <ul className="space-y-3">
                    {result.improvement_suggestions.map((suggestion) => (
                      <li key={suggestion} className="rounded-2xl border border-primary-200 bg-primary-50 p-4 text-sm font-semibold leading-6 text-primary-950 dark:border-primary-900 dark:bg-primary-950 dark:text-primary-100">
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">No suggestions were returned.</p>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="glass-card">
            <div className="flex min-h-80 flex-col items-center justify-center text-center">
              <ClipboardCheck className="mb-5 size-16 text-slate-300 dark:text-slate-700" />
              <h3 className="text-2xl font-black">No analysis yet</h3>
              <p className="mt-3 max-w-md leading-7 text-slate-500 dark:text-slate-400">Submit your resume to receive an ATS score, section audit, critical issues, and actionable improvement suggestions.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
