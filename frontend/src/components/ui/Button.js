import React from 'react';

const baseClasses = 'inline-flex items-center justify-center font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 rounded-lg';

const variants = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500',
  secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 focus-visible:ring-gray-400',
  subtle: 'bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-200 dark:hover:bg-blue-800/60 focus-visible:ring-blue-400',
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
