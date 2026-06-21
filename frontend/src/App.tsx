import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import type { ReactNode } from 'react';
import { Layout } from './components/layout/Layout';
import { useAuth } from './contexts/AuthContext';
import { Analytics } from './pages/Analytics';
import { Dashboard } from './pages/Dashboard';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Settings } from './pages/Settings';
import { Signup } from './pages/Signup';
import Onboarding from './pages/Onboarding';
import ProfileSettings from './pages/ProfileSettings';

const Analyzer = lazy(() => import('./pages/Analyzer').then(m => ({ default: m.Analyzer })));
const Career = lazy(() => import('./pages/Career').then(m => ({ default: m.Career })));
const InterviewPrep = lazy(() => import('./pages/InterviewPrep').then(m => ({ default: m.InterviewPrep })));
const JobMatch = lazy(() => import('./pages/JobMatch').then(m => ({ default: m.JobMatch })));
const AiSettings = lazy(() => import('./pages/AiSettings').then(m => ({ default: m.AiSettings })));
const HealthDashboard = lazy(() => import('./pages/HealthDashboard').then(m => ({ default: m.HealthDashboard })));
const MarketIntelligence = lazy(() => import('./pages/MarketIntelligence').then(m => ({ default: m.MarketIntelligence })));

function ProtectedRoute({ children, requireOnboarding = true }: { children: ReactNode; requireOnboarding?: boolean }) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-50">
        <p className="text-sm font-semibold">Loading workspace...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireOnboarding && !user?.onboarded) {
    return <Navigate to="/onboarding" replace />;
  }

  if (!requireOnboarding && user?.onboarded) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Layout><Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p className="text-sm font-semibold">Loading...</p></div>}>{children}</Suspense></Layout>;
}

export default function App() {
  console.log('[PROD-DIAG] App rendered');
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/onboarding" element={<ProtectedRoute requireOnboarding={false}><Onboarding /></ProtectedRoute>} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/analyzer" element={<ProtectedRoute><Analyzer /></ProtectedRoute>} />
      <Route path="/job-match" element={<ProtectedRoute><JobMatch /></ProtectedRoute>} />
      <Route path="/interview" element={<ProtectedRoute><InterviewPrep /></ProtectedRoute>} />
      <Route path="/career" element={<ProtectedRoute><Career /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><ProfileSettings /></ProtectedRoute>} />
      <Route path="/ai-settings" element={<ProtectedRoute><AiSettings /></ProtectedRoute>} />
      <Route path="/health" element={<ProtectedRoute><HealthDashboard /></ProtectedRoute>} />
      <Route path="/market" element={<ProtectedRoute><MarketIntelligence /></ProtectedRoute>} />
    </Routes>
  );
}
