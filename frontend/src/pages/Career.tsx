import { FormEvent, useState } from 'react';
import { ArrowUpRight, Clock, Map, Sparkles, Target, TrendingUp } from 'lucide-react';
import { useCareerRoadmapMutation } from '../hooks/mutations';
import { currency, parseCommaSeparated } from '../lib/utils';
import { useToast } from '../contexts/ToastContext';

function toPercent(value: number): number {
  if (value > 100) {
    return Math.min(100, value);
  }
  return Math.min(100, Math.round(value * 20));
}

export function Career() {
  const { addToast } = useToast();
  const roadmap = useCareerRoadmapMutation();
  const [skills, setSkills] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [context, setContext] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const currentSkills = parseCommaSeparated(skills);
    if (currentSkills.length === 0 || !targetRole.trim()) {
      addToast('Add at least one current skill and a target role.', 'error');
      return;
    }
    await roadmap.submit(currentSkills, targetRole, context);
  };

  const result = roadmap.data;

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form onSubmit={handleSubmit} className="glass-card space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Career roadmap</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight">Build a path to your next role.</h2>
          <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Enter your current skills, target role, and context to generate skill progressions, timeline, and salary movement.</p>
        </div>

        <div>
          <label className="field-label" htmlFor="skills">Current skills</label>
          <input id="skills" className="field-input" value={skills} placeholder="React, TypeScript, Node.js" onChange={(event) => setSkills(event.target.value)} />
        </div>

        <div>
          <label className="field-label" htmlFor="targetRole">Target role</label>
          <input id="targetRole" className="field-input" value={targetRole} placeholder="Senior Frontend Engineer" onChange={(event) => setTargetRole(event.target.value)} />
        </div>

        <div>
          <label className="field-label" htmlFor="context">Context</label>
          <textarea id="context" className="field-textarea" value={context} placeholder="Describe your experience, industry, constraints, or preferred learning style..." onChange={(event) => setContext(event.target.value)} />
        </div>

        <button className="btn-primary w-full" type="submit" disabled={roadmap.loading}>
          {roadmap.loading ? 'Building roadmap...' : 'Generate roadmap'}
          {!roadmap.loading && <Map className="size-5" />}
        </button>

        {roadmap.error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
            {roadmap.error}
          </div>
        )}
      </form>

      <div className="space-y-6">
        <div className="glass-card">
          <div className="flex items-center gap-4">
            <div className="flex size-14 items-center justify-center rounded-3xl bg-primary-500/10 text-primary-600 dark:text-primary-300">
              <Target className="size-7" />
            </div>
            <div>
              <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Roadmap</p>
              <h3 className="text-2xl font-black">{result ? `${result.current_role || 'Current role'} → ${result.target_role}` : 'Target role plan'}</h3>
            </div>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
              <Clock className="mb-3 size-6 text-primary-500" />
              <p className="text-sm font-bold text-slate-500 dark:text-slate-400">Estimated timeline</p>
              <p className="mt-2 text-3xl font-black">{result ? `${result.estimated_timeline_months} months` : '—'}</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
              <TrendingUp className="mb-3 size-6 text-emerald-500" />
              <p className="text-sm font-bold text-slate-500 dark:text-slate-400">Entry salary</p>
              <p className="mt-2 text-xl font-black">{result ? currency(result.salary_progression.entry, result.salary_progression.currency) : '—'}</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
              <ArrowUpRight className="mb-3 size-6 text-violet-500" />
              <p className="text-sm font-bold text-slate-500 dark:text-slate-400">Senior salary</p>
              <p className="mt-2 text-xl font-black">{result ? currency(result.salary_progression.senior, result.salary_progression.currency) : '—'}</p>
            </div>
          </div>
        </div>

        {result ? (
          <>
            <div className="glass-card">
              <div className="mb-5 flex items-center gap-3">
                <Map className="size-6 text-primary-500" />
                <h3 className="text-xl font-black">Skill progressions</h3>
              </div>
              <div className="space-y-5">
                {result.skill_progressions.map((progression) => {
                  const currentPercent = toPercent(progression.current_level);
                  const targetPercent = toPercent(progression.target_level);
                  return (
                    <div key={progression.skill} className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
                      <div className="mb-4 flex items-start justify-between gap-4">
                        <div>
                          <h4 className="text-lg font-black">{progression.skill}</h4>
                          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Current {progression.current_level} · Target {progression.target_level}</p>
                        </div>
                        <span className="rounded-full bg-primary-600 px-3 py-1 text-xs font-black text-white">Grow</span>
                      </div>
                      <div className="mb-4 h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                        <div className="h-full rounded-full bg-primary-500" style={{ width: `${targetPercent}%` }}></div>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                        <div className="h-full rounded-full bg-emerald-500" style={{ width: `${currentPercent}%` }}></div>
                      </div>
<ul className="mt-4 space-y-2">
                         {(progression.recommended_actions || []).map((action) => (
                           <li key={action} className="flex items-start gap-3 text-sm font-semibold leading-6 text-slate-700 dark:text-slate-200">
                             <Sparkles className="mt-0.5 size-4 shrink-0 text-primary-500" />
                             {action}
                           </li>
                         ))}
                       </ul>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="glass-card">
              <div className="mb-5 flex items-center gap-3">
                <TrendingUp className="size-6 text-emerald-500" />
                <h3 className="text-xl font-black">Salary progression</h3>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                {[
                  ['Entry', result.salary_progression.entry],
                  ['Mid', result.salary_progression.mid],
                  ['Senior', result.salary_progression.senior],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-900 dark:bg-emerald-950">
                    <p className="text-sm font-bold text-emerald-800 dark:text-emerald-200">{label}</p>
                    <p className="mt-2 text-2xl font-black text-emerald-950 dark:text-emerald-50">{currency(value, result.salary_progression.currency)}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="glass-card">
            <div className="flex min-h-80 flex-col items-center justify-center text-center">
              <Map className="mb-5 size-16 text-slate-300 dark:text-slate-700" />
              <h3 className="text-2xl font-black">No roadmap yet</h3>
              <p className="mt-3 max-w-md leading-7 text-slate-500 dark:text-slate-400">Submit your skills and target role to generate a personalized progression plan with timelines and salary expectations.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
