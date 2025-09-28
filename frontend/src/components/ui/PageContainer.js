import React from 'react';

const PageContainer = ({ className = '', children }) => {
  const classes = [
    'flex-1 overflow-y-auto bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes}>
      <div className="w-full h-full mx-auto max-w-5xl p-4 md:p-6">{children}</div>
    </div>
  );
};

export default PageContainer;
