import React, { useEffect, useRef } from 'react';

import EnhancedMessage from './EnhancedMessage';
import { useConversationStore } from '../context/ConversationStoreContext';
import { useWebSocket } from '../context/WebSocketContext';
import Card, { CardContent } from './ui/Card';
import Button from './ui/Button';

/**
 * Displays the list of messages in the main chat area.
 * It maps over the messages array and renders a message component for each entry
 * while showing a streaming indicator based on the WebSocket state.
 */
const TypingIndicator = ({ onStop }) => (
  <div className="flex items-center space-x-3">
    <Card className="max-w-2xl bg-surface-light dark:bg-surface-dark">
      <CardContent className="flex items-center space-x-3">
        <div className="typing-indicator">
          <span />
          <span />
          <span />
        </div>
        <span className="text-sm text-gray-600 dark:text-gray-300">AI is responding...</span>
      </CardContent>
    </Card>
    <Button
      variant="ghost"
      size="sm"
      className="text-red-600 border border-red-200 dark:border-red-500/40 hover:bg-red-50 dark:hover:bg-red-500/10"
      onClick={onStop}
    >
      Stop
    </Button>
  </div>
);

const ChatWindow = () => {
  const { messages } = useConversationStore();
  const { isLoading, handleFeedback, stopGeneration } = useWebSocket();
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
      {messages.map((msg) => (
        <EnhancedMessage
          key={msg.id || msg.timestamp}
          id={msg.id}
          sender={msg.sender}
          text={msg.text}
          sources={msg.sources}
          onFeedback={handleFeedback}
          timestamp={msg.timestamp || new Date().toISOString()}
          jobStatus={msg.jobStatus}
          isProcessing={msg.isProcessing}
          details={msg.details}
        />
      ))}
      {/* Show typing indicator only when loading and the last message was from the user */}
      {isLoading && messages[messages.length - 1]?.sender === 'user' && (
        <TypingIndicator onStop={stopGeneration} />
      )}
      {/* Empty div to act as a reference for scrolling to the bottom */}
      <div ref={messagesEndRef} />
    </main>
  );
};

export default ChatWindow;