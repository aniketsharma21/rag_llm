import React from 'react';

const baseStyles = 'p-1.5 rounded-full transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2';

const variants = {
  subtle: 'bg-gray-100 hover:bg-gray-200 text-gray-600 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300 focus-visible:ring-gray-400',
  inverse: 'bg-white/20 hover:bg-white/30 text-white focus-visible:ring-white/60',
  ghost: 'bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 focus-visible:ring-gray-400',
};

const IconButton = ({
  children,
  className,
  variant = 'subtle',
  tooltip,
  ...props
}) => {
  const classes = [baseStyles, variants[variant], className].filter(Boolean).join(' ');

  return (
    <button type="button" className={classes} title={tooltip} {...props}>
      {children}
    </button>
  );
};

export default IconButton;
