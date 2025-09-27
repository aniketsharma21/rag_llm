import React from 'react';

/**
 * Enhanced Header component with simplified design
 * - Removed search functionality (now in sidebar)
 * - Clean, minimal header with just title and clear chat button
 * - Better responsive design
 */
const EnhancedHeader = ({ onClearChat }) => {
  return (
    <header className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="flex items-center">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">AI Assistant</h1>
      </div>
      
      <div className="flex items-center">
        {/* Clear Chat Button */}
        <button
          onClick={onClearChat}
          className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear Chat
        </button>
      </div>
    </header>
  );
};

export default EnhancedHeader;
