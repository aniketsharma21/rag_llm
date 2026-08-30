import React from 'react';
import { useLocation } from 'react-router-dom';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { useWebSocket } from '../context/WebSocketContext';

const EnhancedHeader = () => {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const { connectionStatus } = useWebSocket();

  const getPageTitle = () => {
    if (location.pathname.startsWith('/upload')) return 'Knowledge Base';
    return 'RAG Assistant';
  };

  return (
    <header className="sticky top-0 z-30 bg-white/95 dark:bg-[#212121]/95">
      <div className="px-5 py-3 flex items-center justify-between">
        <motion.div 
          key={location.pathname}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col"
        >
          <h1 className="text-lg font-display font-semibold text-gray-800 dark:text-gray-100">
            {getPageTitle()}
          </h1>
        </motion.div>
        
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 dark:border-neutral-700 dark:text-gray-300">
            <span
              className={`h-2 w-2 rounded-full ${
                connectionStatus === 'connected'
                  ? 'bg-emerald-500'
                  : connectionStatus === 'connecting'
                    ? 'bg-amber-500'
                    : 'bg-red-500'
              }`}
            />
            <span className="capitalize">{connectionStatus}</span>
          </div>
          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleTheme}
            className="p-2 rounded-full text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <SunIcon className="w-5 h-5 text-amber-500" />
            ) : (
              <MoonIcon className="w-5 h-5" />
            )}
          </motion.button>
        </div>
      </div>
    </header>
  );
};

export default EnhancedHeader;
