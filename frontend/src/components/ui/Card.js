import React from 'react';

const Card = ({ className = '', children, ...props }) => {
  const classes = [
    'bg-white dark:bg-[#2f2f2f] border border-gray-200 dark:border-neutral-700 rounded-2xl shadow-sm',
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
