import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { PaperAirplaneIcon, StopIcon } from '@heroicons/react/24/solid';

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
    <form onSubmit={handleSubmit} className="relative">
      <motion.div 
        animate={{
          boxShadow: isFocused ? '0 8px 30px rgba(0, 0, 0, 0.12)' : '0 8px 22px rgba(0, 0, 0, 0.08)'
        }}
        className={`
          relative rounded-3xl transition-all duration-150
          bg-white dark:bg-[#2f2f2f] 
          border ${isFocused ? 'border-gray-400 dark:border-neutral-500' : 'border-gray-200 dark:border-neutral-700'}
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
            placeholder="Message RAG Assistant"
            rows={1}
            className="flex-1 max-h-32 min-h-[48px] py-3 px-4 bg-transparent border-none focus:ring-0 resize-none text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
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
                p-2.5 rounded-full transition-colors duration-150 flex items-center justify-center
                ${isLoading 
                  ? 'bg-gray-900 hover:bg-gray-700 dark:bg-white dark:text-gray-900 text-white' 
                  : message.trim() 
                    ? 'bg-gray-900 hover:bg-gray-700 dark:bg-white dark:text-gray-900 text-white' 
                    : 'bg-gray-100 dark:bg-neutral-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
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
      
      <div className="mt-2 px-2 text-center">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Responses can make mistakes. Check important answers against the cited documents.
        </p>
      </div>
    </form>
  );
};

export default EnhancedChatInput;
