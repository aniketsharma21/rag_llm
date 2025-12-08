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
  const { isLoading, sendMessage, stopGeneration } = useWebSocket();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (message) => {
    await sendMessage(message);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
            {messages.map((message, index) => (
              <motion.div
                key={message.id || index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <EnhancedMessage message={message} />
              </motion.div>
            ))}
            
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <TypingIndicator onStop={stopGeneration} />
              </motion.div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-4 py-4">
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