import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import { login, signup, type AuthResponse, type User } from '../lib/api';
import { useToast } from './ToastContext';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  rememberMe: boolean;
  login: (email: string, password: string, remember?: boolean) => Promise<AuthResponse>;
  signup: (name: string, email: string, password: string, remember?: boolean) => Promise<AuthResponse>;
  logout: () => void;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredAuth(): { user: User | null; token: string | null; rememberMe: boolean } {
  const storedUser = localStorage.getItem('career_user');
  const storedToken = localStorage.getItem('career_token');
  const storedRemember = localStorage.getItem('career_remember');
  const rememberMe = storedRemember === 'true';
  
  let user: User | null = null;
  if (storedUser) {
    try {
      user = JSON.parse(storedUser) as User;
    } catch {
      localStorage.removeItem('career_user');
    }
  }
  
  return { user, token: storedToken, rememberMe };
}

function storeAuth(token: string, user: User, remember: boolean) {
  if (remember) {
    localStorage.setItem('career_token', token);
    localStorage.setItem('career_user', JSON.stringify(user));
    localStorage.setItem('career_remember', 'true');
  } else {
    sessionStorage.setItem('career_token', token);
    sessionStorage.setItem('career_user', JSON.stringify(user));
    localStorage.setItem('career_remember', 'false');
  }
}

function clearAuth() {
  localStorage.removeItem('career_token');
  localStorage.removeItem('career_user');
  localStorage.removeItem('career_remember');
  sessionStorage.removeItem('career_token');
  sessionStorage.removeItem('career_user');
}

export function AuthProvider({ children }: { children: ReactNode }) {
  console.log('[PROD-DIAG] AuthProvider rendered');
  const [token, setToken] = useState<string | null>(() => {
    const stored = readStoredAuth();
    if (stored.rememberMe) {
      try {
        return localStorage.getItem('career_token');
      } catch {
        return null;
      }
    }
    try {
      return sessionStorage.getItem('career_token');
    } catch {
      return null;
    }
  });
  const [user, setUser] = useState<User | null>(() => readStoredAuth().user);
  const [rememberMe, setRememberMe] = useState<boolean>(() => readStoredAuth().rememberMe);
  const [isLoading, setIsLoading] = useState(false);
  const { addToast } = useToast();

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'career_token' || e.key === 'career_user') {
        if (e.newValue === null) {
          setToken(null);
          setUser(null);
        }
      }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!rememberMe && token) {
        clearAuth();
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [rememberMe, token]);

  const value = useMemo<AuthContextValue>(() => {
    const persistAuth = (response: AuthResponse, remember: boolean) => {
      setToken(response.access_token);
      setUser(response.user);
      setRememberMe(remember);
      storeAuth(response.access_token, response.user, remember);
    };

    return {
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      rememberMe,
      login: async (email, password, remember = false) => {
        setIsLoading(true);
        try {
          const response = await login(email, password);
          persistAuth(response, remember);
          addToast('Welcome back.', 'success');
          return response;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Login failed.';
          addToast(message, 'error');
          throw error;
        } finally {
          setIsLoading(false);
        }
      },
      signup: async (name, email, password, remember = false) => {
        setIsLoading(true);
        try {
          const response = await signup(name, email, password);
          persistAuth(response, remember);
          addToast('Account created successfully.', 'success');
          return response;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Signup failed.';
          addToast(message, 'error');
          throw error;
        } finally {
          setIsLoading(false);
        }
      },
      logout: useCallback(() => {
        setToken(null);
        setUser(null);
        setRememberMe(false);
        clearAuth();
        addToast('You have been signed out.', 'info');
        window.location.href = '/login';
      }, [addToast]),
      setUser,
    };
  }, [addToast, isLoading, token, user, rememberMe]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}