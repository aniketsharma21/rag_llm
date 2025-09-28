import React, { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * Enhanced Message component with copy, share, timestamps, and mobile responsiveness
 */
const EnhancedMessage = ({ id, sender, text, sources, onFeedback, timestamp }) => {
  const isUser = sender === 'user';
  const [feedbackGiven, setFeedbackGiven] = useState(null);
  const [showActions, setShowActions] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [expandedCards, setExpandedCards] = useState([]);
  const [activePreview, setActivePreview] = useState(null);

  const safeSources = useMemo(() => sources || [], [sources]);
  const apiBaseUrl = useMemo(() => {
    const envUrl = process.env.REACT_APP_API_URL;
    if (envUrl && envUrl.trim()) {
      return envUrl.replace(/\/$/, '');
    }
    return 'http://localhost:8000';
  }, []);

  const buildAbsoluteUrl = (path) => {
    if (!path || typeof path !== 'string') {
      return null;
    }
    if (/^https?:\/\//i.test(path)) {
      return path;
    }
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${apiBaseUrl}${normalizedPath}`;
  };

  const extractFilename = (rawPath) => {
    if (!rawPath || typeof rawPath !== 'string') {
      return null;
    }
    const parts = rawPath.split(/[/\\]/);
    return parts[parts.length - 1] || null;
  };

  const resolvePreviewUrl = (source) => {
    if (!source) {
      return null;
    }
    const previewPath = source.preview_url || source.metadata?.preview_url;
    if (previewPath) {
      return buildAbsoluteUrl(previewPath);
    }

    const rawPath = source.raw_file_path || source.source_file || source.metadata?.raw_file_path;
    const filename = extractFilename(rawPath);
    if (filename) {
      return buildAbsoluteUrl(`/files/preview/${filename}`);
    }

    return null;
  };

  const resolveExternalUrl = (source) => {
    if (!source) {
      return null;
    }

    const directUrl = source.url;
    if (directUrl && /^https?:\/\//i.test(directUrl)) {
      return directUrl;
    }

    const previewUrl = resolvePreviewUrl(source);
    if (previewUrl) {
      return previewUrl;
    }

    const rawPath = source.raw_file_path || source.source_file || source.metadata?.raw_file_path;
    if (rawPath && !/^file:/.test(rawPath)) {
      const filename = extractFilename(rawPath);
      if (filename) {
        return buildAbsoluteUrl(`/files/preview/${filename}`);
      }
    }

    return null;
  };

  /**
   * Handle feedback submission
   */
  const handleFeedbackClick = (feedback) => {
    if (!feedbackGiven && onFeedback) {
      onFeedback(id, feedback);
      setFeedbackGiven(feedback);
    }
  };

  /**
   * Copy message text to clipboard
   */
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  /**
   * Share message via Web Share API or fallback to copy
   */
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'RAG LLM Chat Message',
          text: text,
        });
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Error sharing:', err);
          handleCopy(); // Fallback to copy
        }
      }
    } else {
      handleCopy(); // Fallback for browsers without Web Share API
    }
  };

  const toggleCard = (index) => {
    setExpandedCards((prev) =>
      prev.includes(index)
        ? prev.filter((i) => i !== index)
        : [...prev, index]
    );
  };

  const handleOpenPreview = (source) => {
    const previewUrl = resolvePreviewUrl(source);
    if (!previewUrl) {
      return;
    }
    setActivePreview({
      url: previewUrl,
      title: source.display_name || source.name || `Document ${source.id || ''}`,
      pageLabel: source.page_label || (source.page_number ? `Page ${source.page_number}` : null),
    });
  };

  const handleClosePreview = () => setActivePreview(null);

  /**
   * Format timestamp for display
   */
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      const diffInMinutes = Math.floor((now - date) / (1000 * 60));
      return diffInMinutes < 1 ? 'Just now' : `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <>
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-slide-in-up`}>
      <div className="flex flex-col max-w-[85%] md:max-w-2xl" style={{ alignItems: isUser ? 'flex-end' : 'flex-start' }}>
        {/* Timestamp */}
        {timestamp && (
          <div className={`text-xs text-gray-500 dark:text-gray-400 mb-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {formatTimestamp(timestamp)}
          </div>
        )}

        {/* Main message bubble */}
        <div 
          className={`
            relative group
            ${isUser 
              ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' 
              : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
            } 
            rounded-2xl shadow-md hover:shadow-lg transition-all duration-200 p-4
            ${isUser ? 'rounded-br-md' : 'rounded-bl-md'}
          `}
          onMouseEnter={() => setShowActions(true)}
          onMouseLeave={() => setShowActions(false)}
        >
          {/* Message text with Markdown rendering */}
          <div className={`prose prose-sm max-w-none ${isUser ? 'prose-invert' : 'dark:prose-invert'}`}>
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>

        </div>

        {/* Enhanced Sources section - displayed separately below the message */}
        {!isUser && safeSources.length > 0 && (
          <div className="mt-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center mb-3">
              <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="font-medium text-sm text-gray-700 dark:text-gray-300">
                Sources ({safeSources.length})
              </span>
            </div>
            <div className="space-y-3">
              {safeSources.map((source, index) => {
                const isExpanded = expandedCards.includes(index);
                const displayName = source.display_name || source.name || `Document ${index + 1}`;
                const pageLabel = source.page_label || (source.page_number ? `Page ${source.page_number}` : null);
                const relevance = typeof source.relevance_score === 'number' ? source.relevance_score : null;
                const snippet = source.snippet || source.content;
                const previewUrl = resolvePreviewUrl(source);
                const externalUrl = resolveExternalUrl(source);
                return (
                  <div
                    key={`${source.id || index}-${displayName}`}
                    className="bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm"
                  >
                    <button
                      type="button"
                      onClick={() => toggleCard(index)}
                      className="w-full flex items-start justify-between px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800/70 rounded-t-xl"
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center text-xs font-semibold text-blue-600 dark:text-blue-300">
                          {source.citation || `${index + 1}`}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                            {displayName}
                          </p>
                          {pageLabel && (
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {pageLabel}
                            </p>
                          )}
                          {source.source_display_path && (
                            <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                              {source.source_display_path}
                            </p>
                          )}
                          {!isExpanded && snippet && (
                            <p className="mt-1 text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
                              {snippet}
                            </p>
                          )}
                        </div>
                      </div>
                      <svg
                        className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {isExpanded && (
                      <div className="px-4 pb-4 pt-1 border-t border-gray-200 dark:border-gray-700 rounded-b-xl">
                        {snippet && (
                          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                            {snippet}
                          </p>
                        )}
                        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                          {pageLabel && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-200">
                              {pageLabel}
                            </span>
                          )}
                          {relevance !== null && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-200">
                              Relevance: {(relevance * 100).toFixed(0)}%
                            </span>
                          )}
                          {source.confidence && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-200">
                              Confidence: {(source.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {previewUrl && (
                            <button
                              type="button"
                              onClick={() => handleOpenPreview(source)}
                              className="inline-flex items-center px-3 py-2 text-xs font-medium text-blue-600 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/30 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-800/60 transition-colors"
                            >
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618V19a2 2 0 01-2 2H7a2 2 0 01-2-2V5a2 2 0 012-2h6" />
                              </svg>
                              Quick preview
                            </button>
                          )}
                          {externalUrl && (
                            <a
                              href={externalUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                            >
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4m-2-8l5 5m0 0l-5 5m5-5H9" />
                              </svg>
                              Open source
                            </a>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div>

          {/* Action buttons overlay */}
          <div className={`
            absolute top-2 ${isUser ? 'left-2' : 'right-2'} 
            flex items-center space-x-1 
            transition-opacity duration-200
            ${showActions ? 'opacity-100' : 'opacity-0 md:opacity-0'}
          `}>
            {/* Copy button */}
            <button
              onClick={handleCopy}
              className={`
                p-1.5 rounded-full transition-all duration-200 hover:scale-110
                ${isUser 
                  ? 'bg-white/20 hover:bg-white/30 text-white' 
                  : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300'
                }
              `}
              title={copySuccess ? 'Copied!' : 'Copy message'}
            >
              {copySuccess ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              )}
            </button>

            {/* Share button */}
            <button
              onClick={handleShare}
              className={`
                p-1.5 rounded-full transition-all duration-200 hover:scale-110
                ${isUser 
                  ? 'bg-white/20 hover:bg-white/30 text-white' 
                  : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300'
                }
              `}
              title="Share message"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile action buttons - always visible on mobile */}
        <div className="flex md:hidden items-center mt-2 space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            {copySuccess ? (
              <>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Copy</span>
              </>
            )}
          </button>

          <button
            onClick={handleShare}
            className="flex items-center space-x-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
            </svg>
            <span>Share</span>
          </button>
        </div>

        {/* Enhanced feedback buttons for bot messages */}
        {!isUser && onFeedback && id && (
          <div className="flex items-center mt-2 space-x-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">Was this helpful?</span>
            <button
              onClick={() => handleFeedbackClick('helpful')}
              disabled={!!feedbackGiven}
              className={`
                flex items-center space-x-1 px-2 py-1 text-xs rounded-full transition-all duration-200
                ${feedbackGiven === 'helpful' 
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' 
                  : 'bg-gray-100 hover:bg-green-50 dark:bg-gray-700 dark:hover:bg-green-900/20 text-gray-600 dark:text-gray-300'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              aria-label="Helpful"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
              <span>Yes</span>
            </button>
            <button
              onClick={() => handleFeedbackClick('not_helpful')}
              disabled={!!feedbackGiven}
              className={`
                flex items-center space-x-1 px-2 py-1 text-xs rounded-full transition-all duration-200
                ${feedbackGiven === 'not_helpful' 
                  ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' 
                  : 'bg-gray-100 hover:bg-red-50 dark:bg-gray-700 dark:hover:bg-red-900/20 text-gray-600 dark:text-gray-300'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              aria-label="Not Helpful"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
              </svg>
              <span>No</span>
            </button>
          </div>
        )}
      </div>
    </div>

    {activePreview && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
        <div className="relative w-full max-w-4xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {activePreview.title}
              </h3>
              {activePreview.pageLabel && (
                <p className="text-xs text-gray-500 dark:text-gray-400">{activePreview.pageLabel}</p>
              )}
            </div>
            <button
              type="button"
              onClick={handleClosePreview}
              className="p-2 rounded-full text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Close preview"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="h-[60vh] bg-gray-100 dark:bg-gray-800">
            <iframe
              src={activePreview.url}
              title={activePreview.title}
              className="w-full h-full border-0"
            />
          </div>
        </div>
      </div>
    )}
    </>
  );
};

export default EnhancedMessage;
