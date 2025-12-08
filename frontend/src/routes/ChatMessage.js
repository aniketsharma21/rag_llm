import React from 'react';
import { motion } from 'framer-motion';
import { UserIcon, CpuChipIcon } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';
import SourceCard from './SourceCard';

const ChatMessage = ({ message }) => {
  const isUser = message.sender === 'user';
  const isAI = message.sender === 'ai';

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`
        flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
        ${isUser
          ? 'bg-primary-600 text-white'
          : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
        }
      `}>
        {isUser ? (
          <UserIcon className="w-4 h-4" />
        ) : (
          <CpuChipIcon className="w-4 h-4" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-3xl ${isUser ? 'text-right' : ''}`}>
        <div className={`
          inline-block px-4 py-3 rounded-2xl shadow-sm
          ${isUser
            ? 'bg-primary-600 text-white'
            : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
          }
        `}>
          {isUser ? (
            <p className="text-sm leading-relaxed">{message.text}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{message.text}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {isAI && message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-3 space-y-2"
          >
            <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
              Sources:
            </p>
            <div className="grid gap-2">
              {message.sources.map((source, index) => (
                <SourceCard key={index} source={source} />
              ))}
            </div>
          </motion.div>
        )}

        {/* Metadata */}
        <div className="mt-2 text-xs text-gray-400 dark:text-gray-500">
          {new Date(message.timestamp).toLocaleTimeString()}
          {message.confidence_score && (
            <span className="ml-2">
              Confidence: {Math.round(message.confidence_score * 100)}%
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
