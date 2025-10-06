import React, { useState, useMemo } from 'react';
import ThumbUpAltOutlinedIcon from '@mui/icons-material/ThumbUpAltOutlined';
import ThumbDownAltOutlinedIcon from '@mui/icons-material/ThumbDownAltOutlined';
import ReactMarkdown from 'react-markdown';
import { useConfig } from '../context/ConfigContext';
import IconButton from './ui/IconButton';
import Tooltip from './ui/Tooltip';
import Modal from './ui/Modal';
import Button from './ui/Button';
import SourceList from './messages/SourceList';

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
  const { apiBaseUrl } = useConfig();

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
          <SourceList
            sources={safeSources.map((source, index) => ({
              key: `${source.id || index}-${source.display_name || source.name || index}`,
              citation: source.citation || `${index + 1}`,
              displayName: source.display_name || source.name || `Document ${index + 1}`,
              pageLabel: source.page_label || (source.page_number ? `Page ${source.page_number}` : null),
              sourceDisplayPath: source.source_display_path,
              snippet: source.snippet || source.content,
              relevance: typeof source.relevance_score === 'number' ? source.relevance_score : null,
              confidence: typeof source.confidence === 'number' ? source.confidence : null,
              previewUrl: resolvePreviewUrl(source),
              externalUrl: resolveExternalUrl(source),
              rawSource: source,
            }))}
            expandedCards={expandedCards}
            onToggle={(index) => toggleCard(index)}
            onPreview={(source) => handleOpenPreview(source.rawSource)}
          />
        )}

        <div>

          {/* Action buttons overlay */}
          <div className={`
            absolute top-2 ${isUser ? 'left-2' : 'right-2'} 
            flex items-center space-x-1 
            transition-opacity duration-200
            ${showActions ? 'opacity-100' : 'opacity-0 md:opacity-0'}
          `}>
            <Tooltip content={copySuccess ? 'Copied!' : 'Copy message'}>
              <IconButton
                onClick={handleCopy}
                variant={isUser ? 'inverse' : 'subtle'}
                className="hover:scale-110"
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
              </IconButton>
            </Tooltip>

            <Tooltip content="Share message">
              <IconButton
                onClick={handleShare}
                variant={isUser ? 'inverse' : 'subtle'}
                className="hover:scale-110"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                </svg>
              </IconButton>
            </Tooltip>
          </div>
        </div>

        {/* Mobile action buttons - always visible on mobile */}
        <div className="flex md:hidden items-center mt-2 space-x-2">
          <Button
            onClick={handleCopy}
            variant="secondary"
            size="sm"
            className="flex items-center space-x-1"
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
          </Button>

          <Button
            onClick={handleShare}
            variant="secondary"
            size="sm"
            className="flex items-center space-x-1"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
            </svg>
            <span>Share</span>
          </Button>
        </div>

        {/* Enhanced feedback buttons for bot messages */}
        {!isUser && onFeedback && id && (
          <div className="flex items-center mt-2 space-x-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">Was this helpful?</span>
            <Button
              variant={feedbackGiven === 'helpful' ? 'subtle' : 'ghost'}
              size="sm"
              className="flex items-center space-x-1 text-xs"
              onClick={() => handleFeedbackClick('helpful')}
              disabled={!!feedbackGiven}
              aria-label="Helpful"
            >
              <ThumbUpAltOutlinedIcon fontSize="inherit" sx={{ width: '1rem', height: '1rem' }} />
              <span>Yes</span>
            </Button>
            <Button
              variant={feedbackGiven === 'not_helpful' ? 'subtle' : 'ghost'}
              size="sm"
              className="flex items-center space-x-1 text-xs"
              onClick={() => handleFeedbackClick('not_helpful')}
              disabled={!!feedbackGiven}
              aria-label="Not Helpful"
            >
              <ThumbDownAltOutlinedIcon fontSize="inherit" sx={{ width: '1rem', height: '1rem' }} />
              <span>No</span>
            </Button>
          </div>
        )}
      </div>
    </div>

  <Modal
    isOpen={!!activePreview}
    title={activePreview?.title}
    subtitle={activePreview?.pageLabel}
    onClose={handleClosePreview}
  >
    {activePreview && (
      <iframe
        src={activePreview.url}
        title={activePreview.title}
        className="w-full h-full border-0"
      />
    )}
  </Modal>
  </>
  );
};

export default EnhancedMessage;
