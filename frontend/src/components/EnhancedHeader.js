import React from 'react';
import { useLocation } from 'react-router-dom';
import { SunIcon, MoonIcon, BellIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';

const EnhancedHeader = () => {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  const getPageTitle = () => {
    if (location.pathname.startsWith('/upload')) return 'Knowledge Base';
    if (location.pathname.startsWith('/chat')) return 'Chat';
    return 'Dashboard';
  };

  return (
    <header className="sticky top-0 z-30 px-8 py-5">
      <div className="glass-panel rounded-2xl px-6 py-4 flex items-center justify-between">
        <motion.div 
          key={location.pathname}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col"
        >
          <h1 className="text-xl font-display font-semibold text-gray-900 dark:text-white">
            {getPageTitle()}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Manage your AI interactions
          </p>
        </motion.div>
        
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2.5 rounded-xl text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <BellIcon className="w-5 h-5" />
          </motion.button>

          <div className="h-6 w-px bg-gray-200 dark:bg-gray-700 mx-1" />

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleTheme}
            className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors shadow-sm"
          >
            {theme === 'dark' ? (
              <SunIcon className="w-5 h-5 text-amber-500" />
            ) : (
              <MoonIcon className="w-5 h-5 text-primary-600" />
            )}
          </motion.button>
        </div>
      </div>
    </header>
  );
};

export default EnhancedHeader;