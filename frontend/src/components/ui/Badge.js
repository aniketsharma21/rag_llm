import React from 'react';

const baseClasses = 'inline-flex items-center px-2 py-1 text-xs font-medium rounded-full';

const variants = {
  neutral: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200',
  blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-200',
  green: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200',
  purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-200',
};

const Badge = ({ children, variant = 'neutral', className = '', ...props }) => {
  const classes = [baseClasses, variants[variant], className].filter(Boolean).join(' ');
  return (
    <span className={classes} {...props}>
      {children}
    </span>
  );
};

export default Badge;
