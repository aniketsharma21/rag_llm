import React from 'react';

import { useConversationStore } from '../context/ConversationStoreContext';
import { useWebSocket } from '../context/WebSocketContext';
import Button from './ui/Button';

/**
 * Enhanced Header component with simplified design
 * - Shows real-time connection status from WebSocket context
 * - Clear chat action sourced from the conversation store
 */
const STATUS_CONFIG = {
  connected: {
    label: 'Connected',
    dot: 'bg-green-500',
  },
  connecting: {
    label: 'Connecting…',
    dot: 'bg-yellow-400',
  },
  disconnected: {
    label: 'Disconnected',
    dot: 'bg-red-500',
  },
};

const EnhancedHeader = () => {
  const { clearMessages } = useConversationStore();
  const { connectionStatus = 'connected' } = useWebSocket();
  const statusConfig = STATUS_CONFIG[connectionStatus] || {
    label: 'Unknown',
    dot: 'bg-gray-400',
  };

  return (
    <header className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="flex items-center space-x-3">
        <div className="flex items-center text-xs font-medium text-gray-600 dark:text-gray-300">
          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${statusConfig.dot}`} aria-hidden="true" />
          <span>{statusConfig.label}</span>
        </div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">AI Assistant</h1>
      </div>
      
      <Button variant="secondary" size="sm" onClick={clearMessages} className="gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        <span>Clear Chat</span>
      </Button>
    </header>
  );
};

export default EnhancedHeader;
