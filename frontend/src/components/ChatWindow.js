import React, { useEffect, useRef } from 'react';
import EnhancedMessage from './EnhancedMessage';

/**
 * Displays the list of messages in the main chat area.
 * It maps over the messages array and renders a `Message` component for each one.
 * It also includes a "typing" indicator when the bot is generating a response.
 *
 * @param {object} props - The component props.
 * @param {Array<object>} props.messages - The array of message objects to display.
 * @param {boolean} props.isLoading - Flag indicating if the bot is typing.
 * @param {function} props.onFeedback - Callback function to handle user feedback on messages.
 * @param {function} props.onStop - Callback to request stopping the current generation.
 */
const ChatWindow = ({ messages, isLoading, onFeedback, onStop }) => {
  const messagesEndRef = useRef(null);

  /**
   * Automatically scrolls the chat window to the bottom
   * whenever a new message is added.
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 relative" id="chat-window">
      {messages.map((msg, index) => (
        <EnhancedMessage
          key={index}
          id={msg.id}
          sender={msg.sender}
          text={msg.text}
          sources={msg.sources}
          onFeedback={onFeedback}
          timestamp={msg.timestamp || new Date().toISOString()}
          jobStatus={msg.jobStatus}
          isProcessing={msg.isProcessing}
          details={msg.details}
        />
      ))}
      {/* Show typing indicator only when loading and the last message was from the user */}
      {isLoading && messages[messages.length-1]?.sender === 'user' && (
        <div className="flex items-center space-x-3">
          <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-md p-4 max-w-2xl flex items-center space-x-3">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
            <span className="text-sm text-gray-600 dark:text-gray-300">AI is responding...</span>
          </div>
          {typeof onStop === 'function' && (
            <button
              type="button"
              onClick={onStop}
              className="px-4 py-2 text-sm font-medium text-red-600 border border-red-200 dark:border-red-500/40 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
            >
              Stop
            </button>
          )}
        </div>
      )}
      {/* Empty div to act as a reference for scrolling to the bottom */}
      <div ref={messagesEndRef} />
    </main>
  );
};

export default ChatWindow;