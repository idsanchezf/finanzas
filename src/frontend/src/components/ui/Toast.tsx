'use client';

import {
  useState,
  useCallback,
  useEffect,
  createContext,
  useContext,
} from 'react';
import type { ReactNode } from 'react';

// ---------- Types ----------

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (type: ToastType, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

// ---------- Context ----------

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return ctx;
}

// ---------- Provider ----------

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastType, message: string, duration = 5000) => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { id, type, message, duration }]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
}

// ---------- Container ----------

function ToastContainer() {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      aria-live="polite"
      aria-label="Notificaciones"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={removeToast} />
      ))}
    </div>
  );
}

// ---------- Item ----------

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: Toast;
  onDismiss: (id: string) => void;
}) {
  const [exiting, setExiting] = useState(false);

  const handleDismiss = () => {
    setExiting(true);
    setTimeout(() => onDismiss(toast.id), 300);
  };

  useEffect(() => {
    if (toast.duration && toast.duration > 0) {
      const exitTimer = setTimeout(() => {
        setExiting(true);
        setTimeout(() => onDismiss(toast.id), 300);
      }, toast.duration);
      return () => clearTimeout(exitTimer);
    }
  }, [toast.duration, toast.id, onDismiss]);

  const config = TOAST_CONFIG[toast.type];

  return (
    <div
      className={`pointer-events-auto flex items-center gap-3 rounded-lg border p-4 shadow-lg transition-all duration-300 ${
        exiting
          ? 'opacity-0 translate-x-4 scale-95'
          : 'opacity-100 translate-x-0 scale-100 animate-slide-up'
      } ${config.bg} ${config.border}`}
      role="alert"
    >
      <span className="text-lg flex-shrink-0">{config.icon}</span>
      <p className={`flex-1 text-sm font-medium ${config.text}`}>
        {toast.message}
      </p>
      <button
        onClick={handleDismiss}
        className={`flex-shrink-0 rounded-full p-1 transition-colors ${config.closeHover}`}
        aria-label="Cerrar notificacion"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}

const TOAST_CONFIG: Record<
  ToastType,
  { icon: string; bg: string; border: string; text: string; closeHover: string }
> = {
  success: {
    icon: '✅',
    bg: 'bg-success-50',
    border: 'border-success-200',
    text: 'text-success-800',
    closeHover: 'hover:bg-success-100 text-success-500',
  },
  error: {
    icon: '❌',
    bg: 'bg-danger-50',
    border: 'border-danger-200',
    text: 'text-danger-800',
    closeHover: 'hover:bg-danger-100 text-danger-500',
  },
  info: {
    icon: 'ℹ️',
    bg: 'bg-primary-50',
    border: 'border-primary-200',
    text: 'text-primary-800',
    closeHover: 'hover:bg-primary-100 text-primary-500',
  },
  warning: {
    icon: '⚠️',
    bg: 'bg-warning-50',
    border: 'border-warning-200',
    text: 'text-warning-800',
    closeHover: 'hover:bg-warning-100 text-warning-500',
  },
};
