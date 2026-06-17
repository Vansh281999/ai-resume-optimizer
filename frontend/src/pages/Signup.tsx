import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Check, Eye, EyeOff, Gauge, Mail, Sparkles, UserRound } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export function Signup() {
  const navigate = useNavigate();
  const { signup, isLoading } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    const nameVal = name.trim();
    const emailVal = email.trim();
    const passVal = password;
    if (!nameVal || !emailVal || !passVal) {
      setError('All fields are required.');
      return;
    }
    try {
      await signup(nameVal, emailVal, passVal);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
      <div className="grid min-h-screen lg:grid-cols-2">
        <div className="flex items-center justify-center p-8">
          <div className="w-full max-w-md space-y-8">
            <div>
              <Link to="/" className="mb-8 inline-flex items-center gap-2 font-black">
                <Gauge className="size-6 text-primary-600" />
                AI Career Platform
              </Link>
              <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600">Create account</p>
              <h1 className="mt-4 text-4xl font-black tracking-tight">Start optimizing your career path</h1>
              <p className="mt-4 leading-7 text-slate-600 dark:text-slate-400">Join the platform that turns applications into measurable progress.</p>
            </div>

            <form onSubmit={handleSubmit} className="glass-card space-y-5">
              {error && (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
                  {error}
                </div>
              )}
              <div>
                <label className="field-label" htmlFor="name">Full name</label>
                <div className="relative">
                  <UserRound className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
                  <input
                    id="name"
                    className="field-input pl-12"
                    type="text"
                    value={name}
                    autoComplete="name"
                    placeholder="Alex Morgan"
                    onChange={(event) => setName(event.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="field-label" htmlFor="email">Email address</label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
                  <input
                    id="email"
                    className="field-input pl-12"
                    type="email"
                    value={email}
                    autoComplete="email"
                    placeholder="you@example.com"
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="field-label" htmlFor="password">Password</label>
                <div className="relative">
                  <input
                    id="password"
                    className="field-input pr-12"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    autoComplete="new-password"
                    placeholder="Create a strong password"
                    onChange={(event) => setPassword(event.target.value)}
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                  </button>
                </div>
              </div>
              <button className="btn-primary w-full" type="submit" disabled={isLoading}>
                {isLoading ? 'Creating account...' : 'Create account'}
                {!isLoading && <ArrowRight className="size-4" />}
              </button>
            </form>

            <p className="text-center text-sm text-slate-600 dark:text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="font-black text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300">Sign in</Link>
            </p>
          </div>
        </div>

        <div className="relative hidden overflow-hidden bg-slate-950 lg:flex">
          <div className="absolute -right-20 top-16 size-96 rounded-full bg-primary-600/30 blur-3xl"></div>
          <div className="absolute bottom-16 left-10 size-96 rounded-full bg-emerald-500/20 blur-3xl"></div>
          <div className="relative z-10 m-auto max-w-lg p-10">
            <div className="mb-8 flex size-14 items-center justify-center rounded-3xl bg-primary-500 text-white shadow-glow">
              <Sparkles className="size-7" />
            </div>
            <h2 className="text-4xl font-black tracking-tight text-white">Your AI career workspace is ready.</h2>
            <p className="mt-6 text-lg leading-8 text-slate-300">Create an account to save your profile, run ATS reviews, compare job descriptions, and build targeted career roadmaps.</p>
            <div className="mt-10 space-y-4">
              {['Resume scoring and upload review', 'Job description matching', 'Interview question generation', 'Career roadmap and analytics'].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 font-semibold text-slate-200">
                  <Check className="size-5 shrink-0 text-emerald-400" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
