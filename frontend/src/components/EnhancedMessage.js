import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserIcon, CpuChipIcon, ChevronDownIcon, DocumentTextIcon } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';

const EnhancedMessage = ({ message }) => {
  const isUser = message.sender === 'user';
  const isAI = message.sender === 'ai';
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={`flex gap-6 ${isUser ? 'flex-row-reverse' : ''} group`}>
      {/* Avatar */}
      <div className={`
        flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center shadow-sm
        ${isUser 
          ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white' 
          : 'bg-white dark:bg-gray-800 text-primary-600 dark:text-primary-400 border border-gray-200 dark:border-gray-700'
        }
      `}>
        {isUser ? (
          <UserIcon className="w-5 h-5" />
        ) : (
          <CpuChipIcon className="w-5 h-5" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-3xl ${isUser ? 'text-right' : ''}`}>
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-gray-400 dark:text-gray-500 px-1">
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          
          <div className={`
            inline-block px-6 py-4 rounded-2xl shadow-sm text-left
            ${isUser 
              ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white rounded-tr-sm' 
              : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-tl-sm'
            }
          `}>
            {isUser ? (
              <p className="text-base leading-relaxed">{message.text}</p>
            ) : (
              <div className="prose prose-zinc dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-800">
                <ReactMarkdown>{message.text}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>

        {/* Sources */}
        {isAI && message.sources && message.sources.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
            >
              <ChevronDownIcon className={`w-3 h-3 transition-transform ${showSources ? 'rotate-180' : ''}`} />
              {message.sources.length} Sources Referenced
            </button>

            <AnimatePresence>
              {showSources && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="grid gap-2 mt-2">
                    {message.sources.map((source, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-primary-300 dark:hover:border-primary-700 transition-colors cursor-pointer group/source"
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-1.5 bg-gray-100 dark:bg-gray-700 rounded-md text-gray-500 dark:text-gray-400 group-hover/source:text-primary-600 dark:group-hover/source:text-primary-400 transition-colors">
                            <DocumentTextIcon className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="font-medium text-sm text-gray-900 dark:text-gray-100 mb-0.5">
                              {source.filename}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">
                              {source.content}
                            </div>
                            {source.page_number && (
                              <div className="text-[10px] font-medium text-gray-400 mt-1.5 uppercase tracking-wide">
                                Page {source.page_number}
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Metadata */}
        <div className={`mt-2 text-xs text-gray-300 dark:text-gray-600 flex items-center gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          {message.confidence_score && (
            <>
              <span>•</span>
              <span className={message.confidence_score > 0.8 ? 'text-green-500' : 'text-amber-500'}>
                {Math.round(message.confidence_score * 100)}% Confidence
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedMessage;