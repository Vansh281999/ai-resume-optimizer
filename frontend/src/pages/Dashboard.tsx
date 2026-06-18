import { useNavigate } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, Briefcase, ClipboardCheck, TrendingUp } from 'lucide-react';
import { useTrendsQuery, useFocusAreasQuery } from '../hooks/queries';
import { formatScore } from '../lib/utils';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';

export function Dashboard() {
  const { addToast } = useToast();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const trendsQuery = useTrendsQuery();
  const focusAreasQuery = useFocusAreasQuery();
  const [trendsError, setTrendsError] = useState<string | null>(null);
  const [focusAreasError, setFocusAreasError] = useState<string | null>(null);

  const trends = trendsQuery.data;
  const chartData = trends?.history?.length ? trends.history : [];
  const focusAreas = focusAreasQuery.data?.focus_areas?.length ? focusAreasQuery.data.focus_areas : [];

  useEffect(() => {
    if (isAuthenticated) {
      trendsQuery.refetch();
      focusAreasQuery.refetch();
    }
  }, [isAuthenticated]);

  const trendsHasShownError = useRef(false);
  const focusHasShownError = useRef(false);

  useEffect(() => {
    if (trendsQuery.error && !trendsHasShownError.current) {
      setTrendsError(trendsQuery.error);
      addToast(trendsQuery.error, 'info');
      trendsHasShownError.current = true;
    }
    if (!trendsQuery.error && trendsHasShownError.current) {
      trendsHasShownError.current = false;
      setTrendsError(null);
    }
  }, [trendsQuery.error, addToast]);

  useEffect(() => {
    if (focusAreasQuery.error && !focusHasShownError.current) {
      setFocusAreasError(focusAreasQuery.error);
      addToast(focusAreasQuery.error, 'info');
      focusHasShownError.current = true;
    }
    if (!focusAreasQuery.error && focusHasShownError.current) {
      focusHasShownError.current = false;
      setFocusAreasError(null);
    }
  }, [focusAreasQuery.error, addToast]);

  const emptyTrends = {
    ats: { window_days: 30, count: 0, average: 0, min: 0, max: 0 },
    match: { window_days: 30, count: 0, average: 0, min: 0, max: 0 },
    history: [],
  };
  const safeTrends = trends || emptyTrends;

  const cards = [
    { label: 'Average ATS Score', value: safeTrends.ats.count ? formatScore(safeTrends.ats.average) : '—', sublabel: `${safeTrends.ats.count} scans in ${safeTrends.ats.window_days} days`, icon: ClipboardCheck, tone: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { label: 'Average Job Match', value: safeTrends.match.count ? formatScore(safeTrends.match.average) : '—', sublabel: `${safeTrends.match.count} matches in ${safeTrends.match.window_days} days`, icon: Briefcase, tone: 'text-primary-500', bg: 'bg-primary-500/10' },
    { label: 'Best ATS Score', value: safeTrends.ats.count ? formatScore(safeTrends.ats.max) : '—', sublabel: safeTrends.ats.count ? `Lowest: ${formatScore(safeTrends.ats.min)}` : 'No scans yet', icon: TrendingUp, tone: 'text-blue-500', bg: 'bg-blue-500/10' },
    { label: 'Best Match Score', value: safeTrends.match.count ? formatScore(safeTrends.match.max) : '—', sublabel: safeTrends.match.count ? `Lowest: ${formatScore(safeTrends.match.min)}` : 'No matches yet', icon: Activity, tone: 'text-violet-500', bg: 'bg-violet-500/10' },
  ];

  const showNoTrendsData = !trendsQuery.loading && !trends && !trendsError;
  const showNoFocusAreasData = !focusAreasQuery.loading && focusAreas.length === 0 && !focusAreasError;

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
            {trendsError && (
              <button onClick={() => trendsQuery.refetch()} className="btn-secondary text-xs">Retry</button>
            )}
          </div>
          {showNoTrendsData ? (
            <div className="flex min-h-80 flex-col items-center justify-center text-center">
              <ClipboardCheck className="mb-4 size-12 text-slate-300 dark:text-slate-700" />
              <p className="text-sm font-black text-slate-500">No scan history yet</p>
              <p className="mt-1 text-sm text-slate-400">Run your first ATS analysis to start tracking trends.</p>
              <button onClick={() => navigate('/analyzer')} className="btn-primary mt-4">Go to Analyzer</button>
            </div>
          ) : (
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
          )}
        </div>

        <div className="space-y-5">
          <div className="glass-card">
            <h3 className="text-xl font-black">Recommended next step</h3>
            <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Run the ATS analyzer on your latest resume, then compare it against your highest-priority job description.</p>
          </div>
          <div className="glass-card">
            <h3 className="text-xl font-black">Focus areas</h3>
            {focusAreasQuery.loading && <p className="text-sm text-slate-500">Loading focus areas...</p>}
            {focusAreasError && <p className="text-sm text-rose-600">{focusAreasError}</p>}
            {showNoFocusAreasData ? (
              <div className="py-6 text-center">
                <p className="text-sm font-black text-slate-500">No focus area data yet</p>
                <p className="mt-1 text-sm text-slate-400">Run an analysis to see where you can improve.</p>
                <button onClick={() => navigate('/analyzer')} className="btn-secondary mt-4">Run Analysis</button>
              </div>
            ) : (
              <div className="mt-4 space-y-3">
                {focusAreas.map((item) => (
                  <div key={item.name}>
                    <div className="mb-2 flex items-center justify-between text-sm font-bold">
                      <span>{item.name}</span>
                      <span>{formatScore(item.score)}%</span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                      <div className="h-full rounded-full bg-primary-500" style={{ width: `${item.score}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
