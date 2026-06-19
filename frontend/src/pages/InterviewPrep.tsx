import { FormEvent, useMemo, useState } from 'react';
import type { ElementType } from 'react';
import { Brain, Building2, Lightbulb, MessageCircleQuestion, MessageSquare, Sparkles, Target, UserRound } from 'lucide-react';
import { useInterviewMutation } from '../hooks/mutations';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';
import type { InterviewResponse } from '../lib/api';
import { generateAnswer } from '../lib/api';

interface QuestionBlockProps {
  title: string;
  icon: ElementType;
  items: Array<{ question: string; answer?: string; hasAnswerLoaded: boolean }>;
  onGenerateSingle: (question: string) => void;
  onGenerateAll: () => void;
  singleGenerating: string | null;
  bulkGenerating: boolean;
}

function QuestionBlock({ title, icon: Icon, items, onGenerateSingle, onGenerateAll, singleGenerating, bulkGenerating }: QuestionBlockProps) {
  return (
    <div className="glass-card">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Icon className="size-6 text-primary-500" />
          <h3 className="text-xl font-black">{title}</h3>
        </div>
        <button
          type="button"
          onClick={onGenerateAll}
          disabled={bulkGenerating || items.length === 0}
          className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-primary-700 hover:border-primary-300 hover:bg-primary-50 disabled:cursor-wait disabled:opacity-70 dark:border-slate-800 dark:bg-slate-950 dark:text-primary-200 dark:hover:border-primary-700 dark:hover:bg-slate-900"
        >
          <Sparkles className="size-4" />
          {bulkGenerating ? 'Generating...' : 'Generate all answers'}
        </button>
      </div>

      {items.length > 0 ? (
        <div className="space-y-4">
          {items.map((item, index) => {
            const expanded = item.hasAnswerLoaded;
            const loading = singleGenerating === item.question && !expanded;
            return (
              <div
                key={`${title}-${index}`}
                className="rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950"
              >
                <div className="flex items-start gap-4 p-4">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-600 text-sm font-black text-white">
                    {index + 1}
                  </span>
                  <p className="flex-1 leading-7 text-slate-800 dark:text-slate-100">{item.question}</p>
                  <button
                    type="button"
                    onClick={() => {
                      if (expanded) {
                        return;
                      }
                      onGenerateSingle(item.question);
                    }}
                    disabled={loading}
                    className="shrink-0 inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-primary-700 hover:border-primary-300 hover:bg-primary-50 disabled:cursor-wait disabled:opacity-70 dark:border-slate-800 dark:bg-slate-950 dark:text-primary-200 dark:hover:border-primary-700 dark:hover:bg-slate-900"
                  >
                    {loading ? 'Generating...' : expanded ? 'Regenerate' : 'Generate answer'}
                  </button>
                </div>

                {expanded && item.answer ? (
                  <div className="border-t border-slate-200 bg-white/75 p-4 dark:border-slate-800 dark:bg-slate-900/60">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
                      <Lightbulb className="size-4" />
                      Suggested answer
                    </div>
                    <p className="mt-2 text-sm leading-7 text-slate-800 dark:text-slate-100">{item.answer}</p>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">
          No questions were returned.
        </p>
      )}
    </div>
  );
}

type Category = 'technical' | 'behavioral' | 'company';

type QuestionItem = { question: string; answer: string; hasAnswerLoaded: boolean };

export function InterviewPrep() {
  const { addToast } = useToast();
  const { user } = useAuth();
  const interview = useInterviewMutation();
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [singleGenerating, setSingleGenerating] = useState<string | null>(null);
  const [bulkGenerating, setBulkGenerating] = useState(false);

  const result = interview.data;

  const technicalQuestions = useMemo<QuestionItem[]>(() => normalize(result?.technical_questions), [result?.technical_questions]);
  const behavioralQuestions = useMemo<QuestionItem[]>(() => normalize(result?.behavioral_questions), [result?.behavioral_questions]);
  const companyQuestions = useMemo<QuestionItem[]>(() => normalize(result?.company_specific_questions), [result?.company_specific_questions]);

  const profileContext = useMemo(() => {
    if (!user) return '';
    const parts = [user.name, user.email].filter(Boolean);
    return parts.join(', ');
  }, [user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!company.trim() || !role.trim() || !jobDescription.trim()) {
      addToast('Enter company, role, and job description.', 'error');
      return;
    }
    setAnswers({});
    setSingleGenerating(null);
    setBulkGenerating(false);
    await interview.submit(company, role, jobDescription);
  };

  const candidateContext = [profileContext, resumeText].filter(Boolean).join('\n').slice(0, 4000);

  const generateSingleAnswer = async (question: string) => {
    if (!question) return;
    setSingleGenerating(question);
    try {
      const text = await generateAnswer(question, 'interview', {
        company,
        role,
        job_description: jobDescription,
        candidate_context: candidateContext,
      });
      setAnswers((current) => ({ ...current, [question]: text }));
      setSingleGenerating(null);
    } catch (error) {
      setSingleGenerating(null);
      const message = error instanceof Error ? error.message : 'Failed to generate answer.';
      addToast(message, 'error');
    }
  };

  const generateAllAnswers = async (questions: QuestionItem[], kind: string) => {
    setBulkGenerating(true);
    for (const item of questions) {
      if (!item.question) continue;
      setSingleGenerating(item.question);
      try {
        const text = await generateAnswer(item.question, kind, {
          company,
          role,
          job_description: jobDescription,
          candidate_context: candidateContext,
        });
        setAnswers((current) => ({ ...current, [item.question]: text }));
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to generate answer.';
        addToast(message, 'error');
      } finally {
        setSingleGenerating((current) => (current === item.question ? null : current));
      }
    }
    setBulkGenerating(false);
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(320px,0.45fr)_minmax(0,1.55fr)]">
      <form onSubmit={handleSubmit} className="glass-card space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Interview prep</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight">Generate targeted interview questions.</h2>
          <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">
            Use company, role, and job description context to practice technical, behavioral, and company-specific questions.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="interview-prep-company">Company</label>
            <div className="relative">
              <Building2 className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
              <input id="interview-prep-company" className="field-input pl-12" value={company} placeholder="Acme Labs" onChange={(event) => setCompany(event.target.value)} />
            </div>
          </div>
          <div>
            <label className="field-label" htmlFor="interview-prep-role">Role</label>
            <div className="relative">
              <UserRound className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
              <input id="interview-prep-role" className="field-input pl-12" value={role} placeholder="Frontend Engineer" onChange={(event) => setRole(event.target.value)} />
            </div>
          </div>
        </div>

        <div>
          <label className="field-label" htmlFor="interview-prep-jd">Job description</label>
          <textarea id="interview-prep-jd" className="field-textarea" value={jobDescription} placeholder="Paste the job description..." onChange={(event) => setJobDescription(event.target.value)} />
        </div>

        <div>
          <label className="field-label" htmlFor="interview-prep-resume">Your resume or profile highlights</label>
          <textarea
            id="interview-prep-resume"
            className="field-textarea"
            rows={5}
            value={resumeText}
            placeholder="Paste your resume, selected project outcomes, or profile highlights."
            onChange={(event) => setResumeText(event.target.value)}
          />
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Used only to tailor suggested answers in this session.</p>
        </div>

        <button className="btn-primary w-full" type="submit" disabled={interview.loading}>
          {interview.loading ? 'Generating questions...' : 'Generate interview prep'}
          {!interview.loading && <MessageCircleQuestion className="size-5" />}
        </button>

        <div className="rounded-2xl border border-primary-200 bg-primary-50 p-4 text-sm font-semibold text-primary-800 dark:border-primary-900 dark:bg-primary-950 dark:text-primary-100">
          {user?.email ? `Signed in as ${user.email}` : 'Preview mode — sign in to save answers and track progress.'}
        </div>

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
            <QuestionBlock
              title="Technical questions"
              icon={Target}
              items={technicalQuestions.map((item) => ({
                ...item,
                answer: answers[item.question] || '',
                hasAnswerLoaded: Boolean(answers[item.question]),
              }))}
              onGenerateSingle={(question) => generateSingleAnswer(question)}
              onGenerateAll={() => generateAllAnswers(technicalQuestions, 'technical')}
              singleGenerating={singleGenerating}
              bulkGenerating={bulkGenerating}
            />
            <QuestionBlock
              title="Behavioral questions"
              icon={MessageSquare}
              items={behavioralQuestions.map((item) => ({
                ...item,
                answer: answers[item.question] || '',
                hasAnswerLoaded: Boolean(answers[item.question]),
              }))}
              onGenerateSingle={(question) => generateSingleAnswer(question)}
              onGenerateAll={() => generateAllAnswers(behavioralQuestions, 'behavioral')}
              singleGenerating={singleGenerating}
              bulkGenerating={bulkGenerating}
            />
            <QuestionBlock
              title="Company-specific questions"
              icon={Building2}
              items={companyQuestions.map((item) => ({
                ...item,
                answer: answers[item.question] || '',
                hasAnswerLoaded: Boolean(answers[item.question]),
              }))}
              onGenerateSingle={(question) => generateSingleAnswer(question)}
              onGenerateAll={() => generateAllAnswers(companyQuestions, 'company')}
              singleGenerating={singleGenerating}
              bulkGenerating={bulkGenerating}
            />
            <div className="glass-card">
              <div className="mb-5 flex items-center gap-3">
                <Lightbulb className="size-6 text-amber-500" />
                <h3 className="text-xl font-black">Preparation tips</h3>
              </div>
              {result.preparation_tips.length > 0 ? (
                <ul className="space-y-3">
                  {result.preparation_tips.map((tip, index) => (
                    <li
                      key={index}
                      className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold leading-6 text-amber-950 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100"
                    >
                      {tip}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="rounded-2xl border border-slate-200 p-4 text-sm font-semibold text-slate-500 dark:border-slate-800 dark:text-slate-400">
                  No preparation tips were returned.
                </p>
              )}
            </div>
          </>
        ) : (
          <div className="glass-card">
            <div className="flex min-h-80 flex-col items-center justify-center text-center">
              <MessageCircleQuestion className="mb-5 size-16 text-slate-300 dark:text-slate-700" />
              <h3 className="text-2xl font-black">No questions yet</h3>
              <p className="mt-3 max-w-md leading-7 text-slate-500 dark:text-slate-400">
                Enter interview context to generate a tailored practice set across technical, behavioral, and company-specific categories.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function normalize(source: Array<string | { question?: string }> | undefined): QuestionItem[] {
  const raw = Array.isArray(source) ? source : [];
  return raw.map((item, idx) => {
    const text = typeof item === 'string' ? item : item?.question || '';
    return { id: `q-${idx}`, question: text, answer: '', hasAnswerLoaded: false };
  });
}
