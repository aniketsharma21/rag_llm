import React, { useEffect } from 'react';

const typeStyles = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100',
  error: 'border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-100',
  info: 'border-gray-200 bg-white text-gray-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-gray-100',
  warning: 'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100',
};

const Toast = ({ message, type = 'info', onClose, duration = 5000 }) => {
  useEffect(() => {
    if (!message) return undefined;
    const timer = setTimeout(() => {
      onClose?.();
    }, duration);
    return () => clearTimeout(timer);
  }, [message, duration, onClose]);

  if (!message) return null;

  return (
    <div className={`fixed top-4 right-4 z-50 max-w-sm rounded-xl border px-4 py-3 text-sm shadow-xl ${typeStyles[type] || typeStyles.info}`}>
      <div className="flex items-center justify-between gap-4">
        <span>{message}</span>
        <button
          type="button"
          onClick={onClose}
          className="text-lg leading-none opacity-70 hover:opacity-100"
          aria-label="Dismiss notification"
        >
          &times;
        </button>
      </div>
    </div>
  );
};

export default Toast;
