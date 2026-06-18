import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { login, signup, type AuthResponse, type User } from '../lib/api';
import { useToast } from './ToastContext';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<AuthResponse>;
  signup: (name: string, email: string, password: string) => Promise<AuthResponse>;
  logout: () => void;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredUser(): User | null {
  const storedUser = localStorage.getItem('career_user');
  if (!storedUser) {
    return null;
  }
  try {
    return JSON.parse(storedUser) as User;
  } catch {
    localStorage.removeItem('career_user');
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  console.log('AuthProvider mounted');
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('career_token'));
  const [user, setUser] = useState<User | null>(readStoredUser);
  const [isLoading, setIsLoading] = useState(false);
  const { addToast } = useToast();

  useEffect(() => {
    if (token) {
      localStorage.setItem('career_token', token);
    } else {
      localStorage.removeItem('career_token');
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('career_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('career_user');
    }
  }, [user]);

  const value = useMemo<AuthContextValue>(() => {
    const persistAuth = (response: AuthResponse) => {
      setToken(response.access_token);
      setUser(response.user);
      localStorage.setItem('career_token', response.access_token);
      localStorage.setItem('career_user', JSON.stringify(response.user));
    };

    return {
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      login: async (email, password) => {
        setIsLoading(true);
        try {
          const response = await login(email, password);
          persistAuth(response);
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
      signup: async (name, email, password) => {
        setIsLoading(true);
        try {
          const response = await signup(name, email, password);
          persistAuth(response);
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
      logout: () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('career_token');
        localStorage.removeItem('career_user');
        addToast('You have been signed out.', 'info');
      },
      setUser,
    };
  }, [addToast, isLoading, token, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
