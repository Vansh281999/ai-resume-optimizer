import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Eye, EyeOff, Gauge, Mail, ShieldCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    const emailVal = email.trim();
    const passVal = password;
    if (!emailVal || !passVal) {
      setError('Email and password are required.');
      return;
    }
    try {
      await login(emailVal, passVal, rememberMe);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
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
              <p className="text-sm font-black uppercase tracking-[0.25em] text-primary-600">Welcome back</p>
              <h1 className="mt-4 text-4xl font-black tracking-tight">Sign in to your workspace</h1>
              <p className="mt-4 leading-7 text-slate-600 dark:text-slate-400">Continue optimizing resumes, matching jobs, and preparing for interviews.</p>
            </div>

            <form onSubmit={handleSubmit} className="glass-card space-y-5">
              {error && (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
                  {error}
                </div>
              )}
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
                    autoComplete="current-password"
                    placeholder="Enter your password"
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
              <div className="flex items-center">
                <input
                  id="remember"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="size-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                />
                <label htmlFor="remember" className="ml-2 text-sm text-slate-600 dark:text-slate-400">Remember me on this device</label>
              </div>
              <button className="btn-primary w-full" type="submit" disabled={isLoading}>
                {isLoading ? 'Signing in...' : 'Sign in'}
                {!isLoading && <ArrowRight className="size-4" />}
              </button>
            </form>

            <p className="text-center text-sm text-slate-600 dark:text-slate-400">
              New here?{' '}
              <Link to="/signup" className="font-black text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300">Create an account</Link>
            </p>
          </div>
        </div>

        <div className="relative hidden overflow-hidden bg-slate-950 lg:flex">
          <div className="absolute -right-24 -top-24 size-96 rounded-full bg-primary-600/30 blur-3xl"></div>
          <div className="absolute -bottom-24 left-12 size-96 rounded-full bg-emerald-500/20 blur-3xl"></div>
          <div className="relative z-10 m-auto max-w-lg p-10">
            <div className="mb-8 flex size-14 items-center justify-center rounded-3xl bg-primary-500 text-white shadow-glow">
              <Gauge className="size-7" />
            </div>
            <h2 className="text-4xl font-black tracking-tight text-white">Make every application stronger.</h2>
            <p className="mt-6 text-lg leading-8 text-slate-300">Login to access ATS scoring, job matching, interview prep, career roadmaps, and analytics in one dashboard.</p>
            <div className="mt-10 grid gap-4">
              {[
                ['Secure token storage', 'Your session token is stored securely.'],
                ['Personalized insights', 'Use your resume and target roles to generate relevant feedback.'],
                ['Fast workflow', 'Move from resume review to interview practice in minutes.'],
              ].map(([title, description]) => (
                <div key={title} className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur">
                  <div className="mb-3 flex items-center gap-2 text-emerald-300">
                    <ShieldCheck className="size-5" />
                    <span className="font-black">{title}</span>
                  </div>
                  <p className="leading-7 text-slate-300">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}