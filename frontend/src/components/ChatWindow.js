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
 */
const ChatWindow = ({ messages, isLoading, onFeedback }) => {
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
        />
      ))}
      {/* Show typing indicator only when loading and the last message was from the user */}
      {isLoading && messages[messages.length-1]?.sender === 'user' && (
         <div className="flex justify-start">
            <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-md p-4 max-w-2xl">
                <div className="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
         </div>
      )}
      {/* Empty div to act as a reference for scrolling to the bottom */}
      <div ref={messagesEndRef} />
    </main>
  );
};

export default ChatWindow;