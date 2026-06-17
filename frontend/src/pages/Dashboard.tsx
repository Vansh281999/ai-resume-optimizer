import { useEffect } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, Briefcase, ClipboardCheck, TrendingUp } from 'lucide-react';
import { useTrendsQuery } from '../hooks/queries';
import { formatScore } from '../lib/utils';
import { useToast } from '../contexts/ToastContext';

const fallbackHistory = [
  { name: 'Mon', ats: 72, match: 68 },
  { name: 'Tue', ats: 76, match: 71 },
  { name: 'Wed', ats: 74, match: 74 },
  { name: 'Thu', ats: 82, match: 79 },
  { name: 'Fri', ats: 86, match: 83 },
  { name: 'Sat', ats: 88, match: 85 },
  { name: 'Sun', ats: 91, match: 88 },
];

export function Dashboard() {
  const { addToast } = useToast();
  const trendsQuery = useTrendsQuery();
  const trends = trendsQuery.data || {
    ats: { window_days: 30, count: 12, average: 81, min: 68, max: 94 },
    match: { window_days: 30, count: 9, average: 76, min: 61, max: 90 },
    history: fallbackHistory,
  };
  const chartData = trends.history.length ? trends.history : fallbackHistory;

  useEffect(() => {
    trendsQuery.refetch();
  }, []);

  useEffect(() => {
    if (trendsQuery.error) {
      addToast(trendsQuery.error, 'info');
    }
  }, [trendsQuery.error, addToast]);

  const cards = [
    { label: 'Average ATS Score', value: formatScore(trends.ats.average), sublabel: `${trends.ats.count} scans in ${trends.ats.window_days} days`, icon: ClipboardCheck, tone: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { label: 'Average Job Match', value: formatScore(trends.match.average), sublabel: `${trends.match.count} matches in ${trends.match.window_days} days`, icon: Briefcase, tone: 'text-primary-500', bg: 'bg-primary-500/10' },
    { label: 'Best ATS Score', value: formatScore(trends.ats.max), sublabel: `Lowest: ${formatScore(trends.ats.min)}`, icon: TrendingUp, tone: 'text-blue-500', bg: 'bg-blue-500/10' },
    { label: 'Best Match Score', value: formatScore(trends.match.max), sublabel: `Lowest: ${formatScore(trends.match.min)}`, icon: Activity, tone: 'text-violet-500', bg: 'bg-violet-500/10' },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-[2rem] border border-primary-200 bg-gradient-to-br from-primary-600 to-indigo-700 p-8 text-white shadow-glow dark:border-primary-900">
        <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-100">Career intelligence</p>
        <h2 className="mt-3 max-w-3xl text-4xl font-black tracking-tight">Your job search performance at a glance.</h2>
        <p className="mt-4 max-w-2xl leading-8 text-primary-50">Review ATS readiness, job alignment, and weekly trends before you apply.</p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="glass-card">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-bold text-slate-500 dark:text-slate-400">{card.label}</p>
                <p className="mt-2 text-4xl font-black tracking-tight">{card.value}</p>
              </div>
              <div className={`flex size-12 items-center justify-center rounded-2xl ${card.bg}`}>
                <card.icon className={`size-6 ${card.tone}`} />
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">{card.sublabel}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
        <div className="glass-card">
          <div className="mb-6 flex items-center justify-between gap-4">
            <div>
              <h3 className="text-xl font-black">Score trends</h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">ATS and job match movement over recent activity.</p>
            </div>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 8, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-40" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ borderRadius: 16, border: '1px solid #e2e8f0' }}
                  formatter={(value: number) => [formatScore(value), '']}
                />
                <Bar dataKey="ats" name="ATS" fill="#6366f1" radius={[10, 10, 0, 0]} />
                <Bar dataKey="match" name="Match" fill="#10b981" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-5">
          <div className="glass-card">
            <h3 className="text-xl font-black">Recommended next step</h3>
            <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Run the ATS analyzer on your latest resume, then compare it against your highest-priority job description.</p>
          </div>
          <div className="glass-card">
            <h3 className="text-xl font-black">Focus areas</h3>
            <div className="mt-4 space-y-3">
              {[
                ['Keyword alignment', 82],
                ['Section completeness', 76],
                ['Role-specific impact', 69],
              ].map((item) => (
                <div key={item[0]}>
                  <div className="mb-2 flex items-center justify-between text-sm font-bold">
                    <span>{item[0]}</span>
                    <span>{item[1]}%</span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div className="h-full rounded-full bg-primary-500" style={{ width: `${item[1]}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
