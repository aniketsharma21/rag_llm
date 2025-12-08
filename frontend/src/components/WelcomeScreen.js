import React from 'react';
import { motion } from 'framer-motion';
import { 
  SparklesIcon, 
  DocumentTextIcon, 
  ChatBubbleBottomCenterTextIcon,
  LightBulbIcon 
} from '@heroicons/react/24/outline';
import { useWebSocket } from '../context/WebSocketContext';

const WelcomeScreen = () => {
  const { sendMessage } = useWebSocket();

  const features = [
    {
      icon: DocumentTextIcon,
      title: 'Analyze Documents',
      description: 'Upload PDFs, DOCX, or TXT files and get instant insights.'
    },
    {
      icon: ChatBubbleBottomCenterTextIcon,
      title: 'Contextual Chat',
      description: 'Ask questions and get answers based on your specific data.'
    },
    {
      icon: SparklesIcon,
      title: 'AI Powered',
      description: 'Leveraging advanced LLMs for accurate and helpful responses.'
    }
  ];

  const suggestions = [
    "Summarize the key points of the last uploaded document",
    "What are the main risks identified in the contract?",
    "Explain the technical architecture described",
    "Compare the financial results with the previous quarter"
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-4xl mx-auto px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-12"
      >
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 mb-6 shadow-glow-sm">
          <SparklesIcon className="w-8 h-8" />
        </div>
        <h1 className="text-4xl font-display font-bold text-gray-900 dark:text-white mb-4 tracking-tight">
          Welcome to RAG Assistant
        </h1>
        <p className="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
          Your personal AI research assistant. Upload documents and start a conversation to unlock insights instantly.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="grid md:grid-cols-3 gap-6 w-full mb-12"
      >
        {features.map((feature, index) => (
          <div 
            key={index}
            className="p-6 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
          >
            <feature.icon className="w-8 h-8 text-primary-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {feature.title}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              {feature.description}
            </p>
          </div>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="w-full max-w-2xl"
      >
        <p className="text-sm font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-4 text-center">
          Try asking
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => sendMessage(suggestion)}
              className="flex items-center gap-3 p-3 text-left bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-primary-400 dark:hover:border-primary-500 hover:shadow-sm transition-all group"
            >
              <LightBulbIcon className="w-5 h-5 text-gray-400 group-hover:text-primary-500 transition-colors" />
              <span className="text-sm text-gray-600 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
                {suggestion}
              </span>
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default WelcomeScreen;
