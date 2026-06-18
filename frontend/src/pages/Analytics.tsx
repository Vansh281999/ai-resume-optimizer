import React from 'react';
import type { ElementType } from 'react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, Briefcase, ClipboardCheck, TrendingUp } from 'lucide-react';
import { useEffect } from 'react';
import { useTrendsQuery } from '../hooks/queries';
import { formatScore } from '../lib/utils';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';

const fallbackHistory = [
  { name: 'Week 1', ats: 64, match: 58 },
  { name: 'Week 2', ats: 69, match: 64 },
  { name: 'Week 3', ats: 72, match: 70 },
  { name: 'Week 4', ats: 78, match: 75 },
  { name: 'Week 5', ats: 83, match: 80 },
  { name: 'Week 6', ats: 86, match: 84 },
];

export function Analytics() {
  const { addToast } = useToast();
  const { isAuthenticated } = useAuth();
  const trendsQuery = useTrendsQuery();
  const trends = trendsQuery.data || {
    ats: { window_days: 30, count: 14, average: 78, min: 64, max: 92 },
    match: { window_days: 30, count: 10, average: 74, min: 58, max: 88 },
    history: fallbackHistory,
  };
  const chartData = trends.history.length ? trends.history : fallbackHistory;

  useEffect(() => {
    if (isAuthenticated) {
      trendsQuery.refetch();
    }
  }, [isAuthenticated]);

  const hasShownError = React.useRef(false);

  useEffect(() => {
    if (trendsQuery.error && !hasShownError.current) {
      addToast(trendsQuery.error, 'info');
      hasShownError.current = true;
    }
  }, [trendsQuery.error, addToast]);

  const summaryCards: { label: string; value: string | number; sublabel: string; icon: ElementType; tone: string; bg: string }[] = [
    { label: 'ATS scans', value: trends.ats.count, sublabel: `${trends.ats.window_days}-day window`, icon: ClipboardCheck, tone: 'text-primary-500', bg: 'bg-primary-500/10' },
    { label: 'Average ATS', value: formatScore(trends.ats.average), sublabel: `${formatScore(trends.ats.min)} - ${formatScore(trends.ats.max)}`, icon: TrendingUp, tone: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { label: 'Job matches', value: trends.match.count, sublabel: `${trends.match.window_days}-day window`, icon: Briefcase, tone: 'text-blue-500', bg: 'bg-blue-500/10' },
    { label: 'Average match', value: formatScore(trends.match.average), sublabel: `${formatScore(trends.match.min)} - ${formatScore(trends.match.max)}`, icon: Activity, tone: 'text-violet-500', bg: 'bg-violet-500/10' },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-[2rem] border border-primary-200 bg-gradient-to-br from-primary-600 to-indigo-700 p-8 text-white shadow-glow dark:border-primary-900">
        <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-100">Analytics</p>
        <h2 className="mt-3 text-4xl font-black tracking-tight">Track resume quality and job alignment over time.</h2>
        <p className="mt-4 max-w-3xl leading-8 text-primary-50">Use trend history to see whether your resume changes are improving ATS scores and role match quality.</p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {summaryCards.map((card) => (
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

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="glass-card">
          <div className="mb-6">
            <h3 className="text-xl font-black">ATS and match trend</h3>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Weekly score movement from recent history.</p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 8, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-40" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: number) => [formatScore(value), '']} />
                <Line type="monotone" dataKey="ats" name="ATS" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="match" name="Match" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card">
          <div className="mb-6">
            <h3 className="text-xl font-black">Score distribution</h3>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Latest average, minimum, and maximum values.</p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: 'ATS average', score: trends.ats.average },
                { name: 'ATS min', score: trends.ats.min },
                { name: 'ATS max', score: trends.ats.max },
                { name: 'Match average', score: trends.match.average },
                { name: 'Match min', score: trends.match.min },
                { name: 'Match max', score: trends.match.max },
              ]} margin={{ top: 10, right: 20, bottom: 8, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-40" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: number) => [formatScore(value), '']} />
                <Bar dataKey="score" fill="#6366f1" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}