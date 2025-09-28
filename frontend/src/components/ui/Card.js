import React from 'react';

const Card = ({ className = '', children, ...props }) => {
  const classes = [
    'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export const CardHeader = ({ className = '', children, ...props }) => {
  const classes = ['px-4 py-3 border-b border-gray-200 dark:border-gray-700', className]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export const CardContent = ({ className = '', children, ...props }) => {
  const classes = ['px-4 py-3', className].filter(Boolean).join(' ');
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export default Card;
