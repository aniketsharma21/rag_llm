import React, { useState, useRef, useEffect } from 'react';

/**
 * Enhanced ChatInput component with upload button, clean design, and improved UX
 * - Upload button near message input
 * - Clean send button (icon only, no color overlay)
 * - Removed black container overlay while typing
 * - Better responsive design
 */
const EnhancedChatInput = ({ onSendMessage, onFileUpload, activeJobs = {} }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  /**
   * Auto-resize textarea based on content
   */
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`; // Max height of 120px
    }
  }, [input]);

  /**
   * Handle sending message
   */
  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /**
   * Handle file upload - open file dialog directly
   */
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  /**
   * Handle file selection
   */
  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0 && onFileUpload) {
      onFileUpload(files);
    }
    // Reset file input
    e.target.value = '';
  };

  return (
    <footer className="p-4 md:p-6 bg-background-light dark:bg-background-dark border-t border-gray-200 dark:border-gray-700">
      <div className="max-w-4xl mx-auto">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          className="hidden"
        />
        
        <div className="flex items-end bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-all duration-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
          
          {/* Upload button */}
          <button
            onClick={handleUploadClick}
            className="flex-shrink-0 p-3 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors duration-200 rounded-l-2xl hover:bg-gray-50 dark:hover:bg-gray-700"
            title="Upload files"
            aria-label="Upload files"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>
          
          {/* Message input - no black container overlay */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              className="w-full bg-transparent border-none focus:ring-0 focus:outline-none resize-none text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 p-3 leading-6"
              placeholder="Type your message..."
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          
          {/* Send button - clean icon only, no color overlay */}
          <button
            onClick={handleSend}
            className="flex-shrink-0 p-3 text-gray-400 hover:text-blue-600 dark:text-gray-500 dark:hover:text-blue-400 transition-colors duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:text-gray-400 dark:disabled:hover:text-gray-500 rounded-r-2xl hover:bg-gray-50 dark:hover:bg-gray-700"
            disabled={!input.trim()}
            title="Send message"
            aria-label="Send message"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        
        <div className="mt-3 space-y-2">
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>

          {Object.keys(activeJobs).length > 0 && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-3">
              <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 mb-2">
                Processing uploads…
              </p>
              <ul className="space-y-2">
                {Object.values(activeJobs).map(job => (
                  <li key={job.jobId} className="flex items-start justify-between text-xs text-blue-800 dark:text-blue-200">
                    <div className="mr-3 min-w-0">
                      <p className="font-medium truncate">{job.fileName}</p>
                      <p className="text-blue-600/80 dark:text-blue-300/80 truncate">
                        {job.message || 'Processing…'}
                      </p>
                    </div>
                    <span className="uppercase tracking-wide text-[10px] font-semibold bg-blue-100 dark:bg-blue-800/60 text-blue-700 dark:text-blue-200 px-2 py-1 rounded-full">
                      {job.status?.replace('_', ' ') || 'running'}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </footer>
  );
};

export default EnhancedChatInput;
