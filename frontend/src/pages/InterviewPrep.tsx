import { FormEvent, useState } from 'react';
import type { ElementType } from 'react';
import { Brain, Building2, MessageCircleQuestion, MessageSquare, Sparkles, Target, UserRound } from 'lucide-react';
import { useInterviewMutation } from '../hooks/mutations';
import { useToast } from '../contexts/ToastContext';

interface QuestionBlockProps {
  title: string;
  icon: ElementType;
  questions: string[];
}

function QuestionBlock({ title, icon: Icon, questions }: QuestionBlockProps) {
  return (
    <div className="glass-card">
      <div className="mb-5 flex items-center gap-3">
        <Icon className="size-6 text-primary-500" />
        <h3 className="text-xl font-black">{title}</h3>
      </div>
      {questions.length > 0 ? (
        <ol className="space-y-4">
          {questions.map((question, index) => (
            <li key={question} className="flex gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
              <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-600 text-sm font-black text-white">{index + 1}</span>
              <p className="font-semibold leading-7 text-slate-800 dark:text-slate-100">{question}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">No questions were returned.</p>
      )}
    </div>
  );
}

export function InterviewPrep() {
  const { addToast } = useToast();
  const interview = useInterviewMutation();
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!company.trim() || !role.trim() || !jobDescription.trim()) {
      addToast('Enter company, role, and job description.', 'error');
      return;
    }
    await interview.submit(company, role, jobDescription);
  };

  const result = interview.data;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form onSubmit={handleSubmit} className="glass-card space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Interview prep</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight">Generate targeted interview questions.</h2>
          <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Use company, role, and job description context to practice technical, behavioral, and company-specific questions.</p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="company">Company</label>
            <div className="relative">
              <Building2 className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
              <input id="company" className="field-input pl-12" value={company} placeholder="Acme Labs" onChange={(event) => setCompany(event.target.value)} />
            </div>
          </div>
          <div>
            <label className="field-label" htmlFor="role">Role</label>
            <div className="relative">
              <UserRound className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
              <input id="role" className="field-input pl-12" value={role} placeholder="Frontend Engineer" onChange={(event) => setRole(event.target.value)} />
            </div>
          </div>
        </div>

        <div>
          <label className="field-label" htmlFor="jd">Job description</label>
          <textarea id="jd" className="field-textarea" value={jobDescription} placeholder="Paste the job description..." onChange={(event) => setJobDescription(event.target.value)} />
        </div>

        <button className="btn-primary w-full" type="submit" disabled={interview.loading}>
          {interview.loading ? 'Generating questions...' : 'Generate interview prep'}
          {!interview.loading && <MessageCircleQuestion className="size-5" />}
        </button>

        {interview.error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
            {interview.error}
          </div>
        )}
      </form>

      <div className="space-y-6">
        <div className="glass-card">
          <div className="flex items-center gap-4">
            <div className="flex size-14 items-center justify-center rounded-3xl bg-primary-500/10 text-primary-600 dark:text-primary-300">
              <Brain className="size-7" />
            </div>
            <div>
              <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Practice set</p>
              <h3 className="text-2xl font-black">{result ? `${result.company} · ${result.role}` : 'AI interview questions'}</h3>
            </div>
          </div>
        </div>

        {result ? (
          <>
            <QuestionBlock title="Technical questions" icon={Target} questions={Array.isArray(result.technical_questions) ? result.technical_questions.map((q: string | { question: string }) => typeof q === 'string' ? q : (q && q.question) || '') : []} />
            <QuestionBlock title="Behavioral questions" icon={MessageSquare} questions={Array.isArray(result.behavioral_questions) ? result.behavioral_questions.map((q: string | { question: string }) => typeof q === 'string' ? q : (q && q.question) || '') : []} />
            <QuestionBlock title="Company-specific questions" icon={Building2} questions={Array.isArray(result.company_specific_questions) ? result.company_specific_questions.map((q: string | { question: string }) => typeof q === 'string' ? q : (q && q.question) || '') : []} />
            <div className="glass-card">
              <div className="mb-5 flex items-center gap-3">
                <Sparkles className="size-6 text-emerald-500" />
                <h3 className="text-xl font-black">Preparation tips</h3>
              </div>
              {result.preparation_tips.length > 0 ? (
                <ul className="space-y-3">
                  {result.preparation_tips.map((tip) => (
                    <li key={tip} className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold leading-6 text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">
                      {tip}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">No preparation tips were returned.</p>
              )}
            </div>
          </>
        ) : (
          <div className="glass-card">
            <div className="flex min-h-80 flex-col items-center justify-center text-center">
              <MessageCircleQuestion className="mb-5 size-16 text-slate-300 dark:text-slate-700" />
              <h3 className="text-2xl font-black">No questions yet</h3>
              <p className="mt-3 max-w-md leading-7 text-slate-500 dark:text-slate-400">Enter interview context to generate a tailored practice set across technical, behavioral, and company-specific categories.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
