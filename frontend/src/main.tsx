import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import './index.css';

console.log('main loaded');

class GlobalErrorBoundary extends React.Component<{ children: React.ReactNode }, { error: Error | null }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React crash:', error, errorInfo);
    const root = document.getElementById('root');
    if (root) {
      root.innerHTML = `<div style="padding: 20px; font-family: monospace; color: red;"><h2>Runtime Error</h2><pre>${error.message}</pre><pre>${error.stack}</pre></div>`;
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 20, fontFamily: 'monospace', color: 'red' }}>
          <h2>Runtime Error</h2>
          <pre>{this.state.error.message}</pre>
          <pre>{this.state.error.stack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

console.log('creating root');

try {
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    throw new Error('Root element not found');
  }
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <GlobalErrorBoundary>
        <HashRouter basename="/ai-resume-optimizer">
          <ThemeProvider>
            <ToastProvider>
              <AuthProvider>
                <App />
              </AuthProvider>
            </ToastProvider>
          </ThemeProvider>
        </HashRouter>
      </GlobalErrorBoundary>
    </React.StrictMode>,
  );
} catch (e) {
  console.error('Failed to mount React:', e);
  const root = document.getElementById('root');
  if (root) {
    root.innerHTML = `<div style="padding: 20px; font-family: monospace; color: red;"><h2>Mount Error</h2><pre>${(e as Error)?.message || String(e)}</pre><pre>${(e as Error)?.stack || ''}</pre></div>`;
  }
}