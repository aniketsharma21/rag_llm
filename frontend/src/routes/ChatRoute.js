import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useConversationStore } from '../context/ConversationStoreContext';
import { useWebSocket } from '../context/WebSocketContext';
import EnhancedMessage from '../components/EnhancedMessage';
import EnhancedChatInput from '../components/EnhancedChatInput';
import WelcomeScreen from '../components/WelcomeScreen';
import TypingIndicator from '../components/TypingIndicator';

const ChatRoute = () => {
  const messagesEndRef = useRef(null);
  const { messages } = useConversationStore();
  const { isLoading, generationStatus, sendMessage, stopGeneration } = useWebSocket();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (message) => {
    await sendMessage(message);
  };

  const regenerateLastAnswer = async () => {
    const lastUserMessage = [...messages].reverse().find((message) => message.sender === 'user');
    if (lastUserMessage && !isLoading) {
      await sendMessage(lastUserMessage.text);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#212121]">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
            {messages.map((message, index) => (
              <motion.div
                key={message.id || index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.18, delay: Math.min(index * 0.015, 0.12) }}
              >
                <EnhancedMessage
                  message={message}
                  onRegenerate={message.sender === 'bot' || message.sender === 'ai' ? regenerateLastAnswer : undefined}
                />
              </motion.div>
            ))}
            
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <TypingIndicator status={generationStatus} onStop={stopGeneration} />
              </motion.div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-[#212121]">
        <div className="max-w-3xl mx-auto px-4 pb-5 pt-3">
          <EnhancedChatInput 
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            onStop={stopGeneration}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatRoute;
