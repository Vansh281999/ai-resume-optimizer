import { useEffect, useState } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';

type ProviderHealth = Record<string, { status: string }>;

export function HealthDashboard() {
  const [health, setHealth] = useState<{ status: string } | null>(null);
  const [ai, setAi] = useState<ProviderHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [base, aiHealth] = await Promise.all([
        api.get('/api/health'),
        api.get('/api/health/ai'),
      ]);
      setHealth(base.data);
      setAi(aiHealth.data as ProviderHealth);
    } catch (err) {
      setHealth({ status: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const statusColor = (s?: string) => {
    if (s === 'ok') return 'bg-emerald-500';
    if (s === 'unavailable') return 'bg-amber-500';
    if (s === 'error') return 'bg-rose-500';
    return 'bg-slate-400';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black">System Status</h1>
        <p className="text-slate-600 dark:text-slate-300">Backend health and AI provider connectivity.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="glass-card">
          <div className="flex items-center gap-3">
            <div className={`size-3 rounded-full ${statusColor(health?.status)}`} />
            <p className="font-black">API Server</p>
          </div>
          <p className="mt-2 text-2xl font-black">{loading ? '...' : (health?.status || 'unknown')}</p>
        </div>
        {ai &&
          Object.entries(ai).map(([key, value]) => (
            <div key={key} className="glass-card">
              <div className="flex items-center gap-3">
                <div className={`size-3 rounded-full ${statusColor((value as any)?.status)}`} />
                <p className="font-black capitalize">{key}</p>
              </div>
              <p className="mt-2 text-sm text-slate-500">{(value as any)?.status}</p>
            </div>
          ))}
      </div>

      <button onClick={load} className="btn-secondary">
        <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
        Refresh health
      </button>
    </div>
  );
}
