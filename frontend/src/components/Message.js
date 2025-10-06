import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * Renders a single chat message bubble.
 * It distinguishes between user and bot messages, displays message text with Markdown,
 * shows sources for bot messages, and provides feedback buttons.
 *
 * @param {object} props - The component props.
 * @param {string} props.id - The unique ID of the message, used for feedback.
 * @param {string} props.sender - The sender of the message ('user' or 'bot').
 * @param {string} props.text - The text content of the message.
 * @param {Array<object>} [props.sources] - An optional array of source objects for bot messages.
 * @param {function} [props.onFeedback] - Optional callback function to handle feedback submission.
 */
const Message = ({ id, sender, text, sources, onFeedback }) => {
  const isUser = sender === 'user';
  // Local state to track if feedback has been submitted for this message, to disable buttons.
  const [feedbackGiven, setFeedbackGiven] = useState(null);

  /**
   * Handles the click event for the feedback buttons.
   * It calls the onFeedback prop and updates the local state to prevent multiple submissions.
   * @param {string} feedback - The feedback value ('helpful' or 'not_helpful').
   */
  const handleFeedbackClick = (feedback) => {
    if (!feedbackGiven && onFeedback) {
      onFeedback(id, feedback);
      setFeedbackGiven(feedback);
    }
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className="flex flex-col" style={{ alignItems: isUser ? 'flex-end' : 'flex-start' }}>
        {/* Main message bubble */}
        <div className={`max-w-2xl ${isUser ? 'bg-bubble-user-light dark:bg-bubble-user-dark' : 'bg-surface-light dark:bg-surface-dark'} rounded-xl shadow-md p-4`}>
          {/* Message text with Markdown rendering */}
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
          {/* Sources section for bot messages */}
          {!isUser && sources && sources.length > 0 && (
            <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
              <p className="font-medium">Sources:</p>
              <ul className="list-disc list-inside">
                {sources.map((source, index) => (
                  <li key={index}>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                      {source.name || `Source ${index + 1}`}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        {/* Feedback buttons for bot messages */}
        {!isUser && onFeedback && id && (
          <div className="flex items-center mt-1">
            <button
              onClick={() => handleFeedbackClick('helpful')}
              disabled={!!feedbackGiven}
              className={`p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 ${feedbackGiven === 'helpful' ? 'text-primary' : 'text-text-secondary-light dark:text-text-secondary-dark'}`}
              aria-label="Helpful"
            >
              <span className="material-icons text-base">thumb_up</span>
            </button>
            <button
              onClick={() => handleFeedbackClick('not_helpful')}
              disabled={!!feedbackGiven}
              className={`p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 ${feedbackGiven === 'not_helpful' ? 'text-red-500' : 'text-text-secondary-light dark:text-text-secondary-dark'}`}
              aria-label="Not Helpful"
            >
              <span className="material-icons text-base">thumb_down</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;