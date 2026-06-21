import { createContext, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  toasts: ToastMessage[];
  addToast: (message: string, type?: ToastType) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  console.log('[PROD-DIAG] ToastProvider rendered');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = (id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  };

  const addToast = (message: string, type: ToastType = 'info') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setToasts((current) => [...current, { id, message, type }]);
    window.setTimeout(() => removeToast(id), 4500);
  };

  const value = useMemo<ToastContextValue>(() => ({ toasts, addToast, removeToast }), [toasts]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-50 flex w-[calc(100%-2rem)] max-w-md flex-col gap-3">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={[
              'flex items-start gap-3 rounded-2xl border p-4 shadow-glow backdrop-blur',
              toast.type === 'success'
                ? 'border-emerald-200 bg-emerald-50 text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-50'
                : '',
              toast.type === 'error'
                ? 'border-rose-200 bg-rose-50 text-rose-950 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-50'
                : '',
              toast.type === 'info'
                ? 'border-primary-200 bg-white text-slate-950 dark:border-primary-900 dark:bg-slate-950 dark:text-slate-50'
                : '',
            ].join(' ')}
          >
            <p className="flex-1 text-sm font-medium leading-6">{toast.message}</p>
            <button
              aria-label="Dismiss notification"
              className="rounded-full p-1 text-current/70 transition hover:bg-current/10 hover:text-current"
              onClick={() => removeToast(toast.id)}
            >
              <X className="size-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used inside ToastProvider');
  }
  return context;
}
