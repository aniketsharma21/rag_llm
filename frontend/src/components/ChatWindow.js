import React, { useEffect, useRef } from 'react';
import Message from './Message';

const ChatWindow = ({ messages, isLoading, onFeedback }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 relative" id="chat-window">
      {messages.map((msg, index) => (
        <Message
          key={index}
          id={msg.id}
          sender={msg.sender}
          text={msg.text}
          sources={msg.sources}
          onFeedback={onFeedback}
        />
      ))}
      {isLoading && messages[messages.length-1]?.sender === 'user' && (
         <div className="flex justify-start">
            <div className="bg-surface-light dark:bg-surface-dark rounded-xl shadow-md p-4 max-w-2xl">
                <div className="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
         </div>
      )}
      <div ref={messagesEndRef} />
    </main>
  );
};

export default ChatWindow;