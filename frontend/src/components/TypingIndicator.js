// Create frontend/src/components/TypingIndicator.js
import React from 'react';
import { motion } from 'framer-motion';
import { CpuChipIcon, StopIcon } from '@heroicons/react/24/solid';

const TypingIndicator = ({ onStop }) => {
  return (
    <div className="flex gap-4">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
        <CpuChipIcon className="w-4 h-4" />
      </div>

      {/* Typing Content */}
      <div className="flex-1 max-w-3xl">
        <div className="inline-block px-4 py-3 rounded-2xl shadow-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-1">
            <span className="text-gray-600 dark:text-gray-300 text-sm mr-2">AI is thinking</span>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        {onStop && (
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            onClick={onStop}
            className="mt-2 flex items-center space-x-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <StopIcon className="w-3 h-3" />
            <span>Stop generating</span>
          </motion.button>
        )}
      </div>
    </div>
  );
};

export default TypingIndicator;
