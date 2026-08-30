import React from 'react';
import { motion } from 'framer-motion';
import { ArrowUpRightIcon } from '@heroicons/react/24/outline';
import { useWebSocket } from '../context/WebSocketContext';

const WelcomeScreen = () => {
  const { sendMessage } = useWebSocket();

  const suggestions = [
    "Summarize the latest uploaded document",
    "Find the main risks and cite the source",
    "Explain this document like I am new to the topic",
    "Compare the financial results with the previous quarter"
  ];

  return (
    <div className="flex flex-col items-center justify-start h-full max-w-3xl mx-auto px-4 pb-20 pt-[14vh]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-6 text-center"
      >
        <h1 className="text-3xl font-display font-semibold text-gray-900 dark:text-gray-100 mb-3 tracking-tight">
          How can I help with your documents?
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-lg mx-auto leading-relaxed">
          Ask a question, request a summary, or use the knowledge base to ground responses in your uploaded files.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full"
      >
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => sendMessage(suggestion)}
            className="group min-h-[86px] rounded-2xl border border-gray-300 bg-gray-50 px-4 py-3 text-left hover:bg-gray-100 dark:border-neutral-700 dark:bg-[#2f2f2f] dark:hover:bg-neutral-800 transition-colors"
          >
            <div className="flex h-full items-start justify-between gap-3">
              <span className="text-sm leading-5 text-gray-700 dark:text-gray-200">
                {suggestion}
              </span>
              <ArrowUpRightIcon className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-300 transition-colors group-hover:text-gray-500 dark:text-neutral-600 dark:group-hover:text-gray-300" />
            </div>
          </button>
        ))}
      </motion.div>
    </div>
  );
};

export default WelcomeScreen;
