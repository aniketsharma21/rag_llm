import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { PaperAirplaneIcon, StopIcon, SparklesIcon } from '@heroicons/react/24/solid';

const EnhancedChatInput = ({ onSendMessage, isLoading, onStop }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;
    
    onSendMessage(message.trim());
    setMessage('');
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleStop = () => {
    if (onStop) onStop();
  };

  return (
    <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
      <motion.div 
        animate={{
          boxShadow: isFocused ? '0 0 20px rgba(99, 102, 241, 0.15)' : '0 0 0 rgba(0,0,0,0)',
          scale: isFocused ? 1.005 : 1
        }}
        className={`
          relative rounded-2xl transition-all duration-200
          bg-white dark:bg-gray-800 
          border ${isFocused ? 'border-primary-500' : 'border-gray-200 dark:border-gray-700'}
        `}
      >
        <div className="flex items-end p-2">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Ask me anything about your documents..."
            rows={1}
            className="flex-1 max-h-32 min-h-[56px] py-4 px-4 bg-transparent border-none focus:ring-0 resize-none text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
            disabled={isLoading}
          />
          
          <div className="flex items-center gap-2 pb-2 pr-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type={isLoading ? "button" : "submit"}
              onClick={isLoading ? handleStop : undefined}
              disabled={!isLoading && !message.trim()}
              className={`
                p-3 rounded-xl transition-all duration-200 flex items-center justify-center
                ${isLoading 
                  ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/30' 
                  : message.trim() 
                    ? 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg shadow-primary-500/30' 
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                }
              `}
            >
              {isLoading ? (
                <StopIcon className="w-5 h-5" />
              ) : (
                <PaperAirplaneIcon className="w-5 h-5" />
              )}
            </motion.button>
          </div>
        </div>
      </motion.div>
      
      <div className="flex justify-between items-center mt-3 px-2">
        <div className="flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
          <SparklesIcon className="w-3 h-3" />
          <span>AI-powered search</span>
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500">
          Press <kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 font-sans">Enter</kbd> to send
        </p>
      </div>
    </form>
  );
};

export default EnhancedChatInput;