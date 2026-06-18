import { useState } from 'react';
import { BarChart3, TrendingUp, Briefcase, Brain, AlertCircle } from 'lucide-react';
import { getMarketSkills, getMarketTrends, SkillDemand, MarketTrend, MarketResponse } from '../lib/api';
import { useToast } from '../contexts/ToastContext';

export function MarketIntelligence() {
  const { addToast } = useToast();
  const [role, setRole] = useState('');
  const [skillsData, setSkillsData] = useState<MarketResponse<Record<string, SkillDemand>> | null>(null);
  const [trendsData, setTrendsData] = useState<MarketResponse<MarketTrend> | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchMarketData = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!role.trim()) {
      addToast('Enter a role to search market data', 'error');
      return;
    }
    setLoading(true);
    try {
      const [skills, trends] = await Promise.all([
        getMarketSkills(role),
        getMarketTrends(role),
      ]);
      setSkillsData(skills);
      setTrendsData(trends);
    } catch (error) {
      addToast('Failed to fetch market data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const topSkills = skillsData?.data ? Object.entries(skillsData.data).slice(0, 10) : [];

  return (
    <div className="space-y-6">
      <div className="glass-card">
        <div className="flex items-center gap-4">
          <div className="flex size-14 items-center justify-center rounded-3xl bg-primary-500/10 text-primary-600 dark:text-primary-300">
            <BarChart3 className="size-7" />
          </div>
          <div>
            <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Market Intelligence</p>
            <h2 className="mt-3 text-3xl font-black tracking-tight">Real-time skill demand analytics</h2>
          </div>
        </div>
        
        <form onSubmit={fetchMarketData} className="mt-6 flex gap-3">
          <input
            className="field-input flex-1"
            placeholder="Enter role (e.g., frontend developer, data engineer)"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? 'Loading...' : 'Analyze'}
          </button>
        </form>
      </div>

      {skillsData?.error && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          <AlertCircle className="inline-block size-4 mr-2" />
          {skillsData.error} - Data is live from RemoteOK API
        </div>
      )}

      {skillsData && !skillsData.error && (
        <div className="glass-card">
          <div className="mb-5 flex items-center gap-3">
            <Brain className="size-6 text-primary-500" />
            <h3 className="text-xl font-black">Top demanded skills for "{role}"</h3>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            Source: {skillsData.source.join(', ')} &middot; Confidence: {skillsData.confidence * 100}% &middot; Fetched: {new Date(skillsData.fetched_at).toLocaleTimeString()}
          </p>
          <div className="space-y-4">
            {topSkills.map(([skill, data]) => (
              <div key={skill} className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-black text-lg">{skill}</span>
                  <span className="rounded-full bg-primary-600 px-3 py-1 text-xs font-black text-white">{data.demand_score}%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div className="h-full rounded-full bg-primary-500 transition-all duration-500" style={{ width: `${data.demand_score}%` }}></div>
                </div>
                <p className="mt-2 text-xs text-slate-500">Mentioned in {data.job_count} jobs &middot; Trend: {data.trend}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {trendsData?.data && (
        <div className="glass-card">
          <div className="mb-5 flex items-center gap-3">
            <TrendingUp className="size-6 text-emerald-500" />
            <h3 className="text-xl font-black">Market trends for "{role}"</h3>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            Source: {trendsData.source.join(', ')} &middot; Sample size: {trendsData.data.sample_size} jobs
          </p>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-900 dark:bg-emerald-950">
              <p className="text-sm font-bold text-emerald-800 dark:text-emerald-200">Avg Salary</p>
              <p className="mt-2 text-2xl font-black text-emerald-950 dark:text-emerald-50">
                {trendsData.data.avg_salary ? `$${Math.round(trendsData.data.avg_salary / 1000)}k` : 'N/A'}
              </p>
            </div>
            <div className="rounded-3xl border border-violet-200 bg-violet-50 p-5 dark:border-violet-900 dark:bg-violet-950">
              <p className="text-sm font-bold text-violet-800 dark:text-violet-200">Demand Score</p>
              <p className="mt-2 text-2xl font-black text-violet-950 dark:text-violet-50">{trendsData.data.demand_score}</p>
            </div>
            <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5 dark:border-amber-900 dark:bg-amber-950">
              <p className="text-sm font-bold text-amber-800 dark:text-amber-200">Jobs Analyzed</p>
              <p className="mt-2 text-2xl font-black text-amber-950 dark:text-amber-50">{trendsData.data.sample_size}</p>
            </div>
          </div>
        </div>
      )}

      {!skillsData && !loading && (
        <div className="glass-card">
          <div className="flex min-h-80 flex-col items-center justify-center text-center">
            <Briefcase className="mb-5 size-16 text-slate-300 dark:text-slate-700" />
            <h3 className="text-2xl font-black">No market data yet</h3>
            <p className="mt-3 max-w-md leading-7 text-slate-500 dark:text-slate-400">
              Enter a role to analyze real-time job market data from RemoteOK and see which skills are most in demand.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}