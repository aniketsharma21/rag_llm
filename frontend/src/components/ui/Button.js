import React from 'react';

const baseClasses = 'inline-flex items-center justify-center font-medium transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 rounded-md';

const variants = {
  primary: 'bg-gray-900 text-white hover:bg-gray-700 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200 focus-visible:ring-gray-500 shadow-sm',
  secondary: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 dark:bg-[#2f2f2f] dark:border-neutral-700 dark:text-gray-200 dark:hover:bg-neutral-800 focus-visible:ring-gray-400',
  subtle: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/30 dark:text-emerald-200 dark:hover:bg-emerald-900/40 focus-visible:ring-emerald-400',
  ghost: 'bg-transparent text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 focus-visible:ring-gray-400',
};

const sizes = {
  sm: 'px-3 py-2 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-3 text-base',
};

const isNativeButton = (component) => {
  if (typeof component === 'string') {
    return component.toLowerCase() === 'button';
  }
  return component === 'button';
};

const Button = ({
  children,
  className = '',
  variant = 'primary',
  size = 'md',
  as: Component = 'button',
  type = 'button',
  ...props
}) => {
  const classes = [baseClasses, variants[variant], sizes[size], className]
    .filter(Boolean)
    .join(' ');

  const componentProps = {
    className: classes,
    ...props,
  };

  if (isNativeButton(Component)) {
    componentProps.type = type;
  }

  const RenderComponent = Component;

  return <RenderComponent {...componentProps}>{children}</RenderComponent>;
};

export default Button;
