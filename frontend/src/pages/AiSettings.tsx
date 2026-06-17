import { useEffect, useState } from 'react';
import { CheckCircle2, Circle, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';

type ProviderStatus = {
  installed: boolean;
  configured: boolean;
  status: 'ok' | 'unavailable';
};

type AiHealth = {
  openai: ProviderStatus;
  anthropic: ProviderStatus;
  gemini: ProviderStatus;
  ollama: ProviderStatus;
  fallback: { available: boolean };
};

function StatusIcon({ status }: { status: ProviderStatus['status'] }) {
  if (status === 'ok') return <CheckCircle2 className="size-5 text-emerald-500" />;
  return <Circle className="size-5 text-slate-400" />;
}

export function AiSettings() {
  const [health, setHealth] = useState<AiHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get<AiHealth>('/health/ai');
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load AI status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const providers = [
    { key: 'openai', label: 'OpenAI', description: 'GPT-4o / GPT-4o-mini' },
    { key: 'anthropic', label: 'Anthropic', description: 'Claude 3.5 Haiku' },
    { key: 'gemini', label: 'Gemini', description: 'Google Gemini 2.0 Flash' },
    { key: 'ollama', label: 'Ollama', description: 'Local LLM runtime' },
  ] as const;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black">AI Provider Settings</h1>
        <p className="text-slate-600 dark:text-slate-300">Manage AI models and connectivity for interview prep and career roadmap features.</p>
      </div>

      <div className="glass-card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-black">Provider status</h2>
          <button onClick={load} className="btn-secondary">
            <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {error && <p className="text-sm text-rose-600">{error}</p>}

        {loading && !health && <p className="text-sm text-slate-500">Loading provider status...</p>}

        {health && (
          <div className="grid gap-4 md:grid-cols-2">
            {providers.map(({ key, label, description }) => {
              const status = health[key];
              return (
                <div key={key} className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-black">{label}</p>
                      <p className="text-sm text-slate-500">{description}</p>
                    </div>
                    <StatusIcon status={status.status} />
                  </div>
                  <div className="mt-3 flex gap-2">
                    <StatusBadge label="Installed" active={status.installed} />
                    <StatusBadge label="Configured" active={status.configured} />
                  </div>
                </div>
              );
            })}
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950">
              <p className="font-black">Fallback data</p>
              <p className="text-sm text-slate-500">Bundled sample results</p>
              <StatusBadge label="Available" active={health.fallback.available} />
            </div>
          </div>
        )}
      </div>

      <div className="glass-card space-y-3">
        <h2 className="text-xl font-black">How it works</h2>
        <p className="text-sm leading-7 text-slate-600 dark:text-slate-300">
          When a provider is unavailable, the platform uses deterministic fallback data so AI features stay functional without an API key.
          Add an <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold dark:bg-slate-800">OPENAI_API_KEY</code> to <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-semibold dark:bg-slate-800">.env</code> to enable live generation.
        </p>
      </div>
    </div>
  );
}

function StatusBadge({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        active
          ? 'border border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200'
          : 'border border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-800 dark:bg-slate-950'
      }`}
    >
      {label}
    </span>
  );
}
