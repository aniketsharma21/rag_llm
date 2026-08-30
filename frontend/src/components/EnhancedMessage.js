import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDownIcon, DocumentTextIcon, ClipboardIcon, CheckIcon } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';

const EnhancedMessage = ({ message, onRegenerate }) => {
  const isUser = message.sender === 'user';
  const isAI = message.sender === 'ai' || message.sender === 'bot';
  const isSystem = message.sender === 'system';
  const [showSources, setShowSources] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyAnswer = async () => {
    try {
      await navigator.clipboard.writeText(message.text || '');
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch (error) {
      console.error('Failed to copy answer', error);
    }
  };

  const previewSource = (source) => {
    const previewUrl = source.preview_url || source.previewUrl;
    if (previewUrl) {
      window.open(previewUrl, '_blank', 'noopener,noreferrer');
    }
  };

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="max-w-xl rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-center text-xs text-gray-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-gray-300">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
      {/* Message Content */}
      <div className={`${isUser ? 'max-w-[80%] text-right' : 'w-full text-left'}`}>
        <div className="flex flex-col gap-2">
          {isAI && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">RAG Assistant</span>
              <div className="flex items-center gap-3">
                {onRegenerate && <button type="button" onClick={onRegenerate} className="text-xs text-gray-500 hover:text-emerald-600">Regenerate</button>}
                <button type="button" onClick={copyAnswer} className="flex items-center gap-1 text-xs text-gray-500 hover:text-emerald-600" aria-label="Copy answer">
                  {copied ? <CheckIcon className="h-4 w-4" /> : <ClipboardIcon className="h-4 w-4" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>
          )}
          
          <div className={`
            text-left
            ${isUser 
              ? 'inline-block rounded-3xl bg-[#f4f4f4] dark:bg-[#2f2f2f] px-5 py-3 text-gray-900 dark:text-gray-100' 
              : 'w-full text-gray-900 dark:text-gray-100'
            }
          `}>
            {isUser ? (
              <p className="text-base leading-relaxed">{message.text}</p>
            ) : (
              <div className="prose prose-zinc dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-950 prose-pre:border prose-pre:border-gray-800">
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
              className="flex items-center gap-2 text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
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
                        onClick={() => previewSource(source)}
                        className={`bg-gray-50 dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-xl p-3 hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors ${source.preview_url || source.previewUrl ? 'cursor-pointer group/source' : ''}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-1.5 bg-white dark:bg-neutral-700 rounded text-gray-500 dark:text-gray-400 group-hover/source:text-emerald-600 dark:group-hover/source:text-emerald-400 transition-colors">
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
        <div className={`mt-2 text-xs text-gray-300 dark:text-neutral-600 flex items-center gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          {message.confidence_score && (
            <>
              <span>&bull;</span>
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
