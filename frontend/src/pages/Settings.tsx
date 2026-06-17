import { FormEvent, useState } from 'react';
import type { ElementType } from 'react';
import { Bell, CreditCard, Globe, KeyRound, LayoutTemplate, Mail, Moon, ShieldCheck, Sun, UserRound } from 'lucide-react';
import { API_BASE_URL } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../contexts/ToastContext';

export function Settings() {
  const { user, logout } = useAuth();
  const { theme, setTheme, toggleTheme } = useTheme();
  const { addToast } = useToast();
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const updatedUser = { ...(user || { id: '' }), name, email };
    localStorage.setItem('career_user', JSON.stringify(updatedUser));
    addToast('Profile settings saved locally.', 'success');
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <form onSubmit={handleSubmit} className="glass-card space-y-6">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Profile</p>
          <h2 className="mt-3 text-3xl font-black tracking-tight">Manage your workspace profile.</h2>
          <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Update the local profile information used by the frontend session.</p>
        </div>

        <div>
          <label className="field-label" htmlFor="name">Display name</label>
          <div className="relative">
            <UserRound className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
            <input id="name" className="field-input pl-12" value={name} onChange={(event) => setName(event.target.value)} required />
          </div>
        </div>

        <div>
          <label className="field-label" htmlFor="email">Email address</label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
            <input id="email" className="field-input pl-12" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>
        </div>

        <button className="btn-primary w-full" type="submit">
          Save profile
        </button>
      </form>

      <div className="space-y-6">
        <div className="glass-card">
          <div className="flex items-center gap-4">
            <div className="flex size-14 items-center justify-center rounded-3xl bg-primary-500/10 text-primary-600 dark:text-primary-300">
              <LayoutTemplate className="size-7" />
            </div>
            <div>
              <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600 dark:text-primary-400">Appearance</p>
              <h3 className="text-2xl font-black">Theme preferences</h3>
            </div>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <button onClick={() => setTheme('light')} className={themeButtonClass(theme === 'light')}>
              <Sun className="size-6 text-amber-500" />
              <span className="font-black">Light mode</span>
              <span className="text-sm text-slate-500 dark:text-slate-400">Use a bright interface with high contrast.</span>
            </button>
            <button onClick={() => setTheme('dark')} className={themeButtonClass(theme === 'dark')}>
              <Moon className="size-6 text-primary-500" />
              <span className="font-black">Dark mode</span>
              <span className="text-sm text-slate-500 dark:text-slate-400">Use a low-light interface for focus.</span>
            </button>
          </div>
          <button onClick={toggleTheme} className="btn-secondary mt-5 w-full">
            Toggle theme
          </button>
        </div>

        <div className="glass-card">
          <div className="mb-5 flex items-center gap-3">
            <ShieldCheck className="size-6 text-emerald-500" />
            <h3 className="text-xl font-black">Security</h3>
          </div>
          <div className="space-y-4">
            <SettingRow icon={KeyRound} label="Session token" value="Stored as career_token in localStorage" />
            <SettingRow icon={UserRound} label="User profile" value="Stored as career_user in localStorage" />
            <SettingRow icon={Globe} label="API endpoint" value={API_BASE_URL} />
          </div>
          <button onClick={logout} className="btn-secondary mt-6 w-full border-rose-200 text-rose-700 hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950">
            Sign out of this device
          </button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="glass-card">
            <Bell className="mb-4 size-7 text-primary-500" />
            <h3 className="text-xl font-black">Notifications</h3>
            <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">Toast notifications appear after login, analysis, saves, and errors. They auto-dismiss after a few seconds.</p>
          </div>
          <div className="glass-card">
            <CreditCard className="mb-4 size-7 text-emerald-500" />
            <h3 className="text-xl font-black">Billing</h3>
            <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">This frontend is ready for subscription pages and can connect to any billing provider through API routes.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function themeButtonClass(active: boolean): string {
  return [
    'flex flex-col gap-3 rounded-3xl border p-5 text-left transition',
    active
      ? 'border-primary-500 bg-primary-50 shadow-glow dark:border-primary-400 dark:bg-primary-950'
      : 'border-slate-200 bg-slate-50 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-950 dark:hover:bg-slate-900',
  ].join(' ');
}

function SettingRow({ icon: Icon, label, value }: { icon: ElementType; label: string; value: string }) {
  return (
    <div className="flex items-start gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
      <Icon className="mt-0.5 size-5 shrink-0 text-primary-500" />
      <div>
        <p className="font-black">{label}</p>
        <p className="mt-1 break-all text-sm font-semibold text-slate-500 dark:text-slate-400">{value}</p>
      </div>
    </div>
  );
}
