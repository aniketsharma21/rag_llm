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
  reconnecting: {
    label: 'Reconnecting…',
    dot: 'bg-amber-500 animate-pulse',
  },
  disconnected: {
    label: 'Disconnected',
    dot: 'bg-red-500',
  },
};

const EnhancedHeader = () => {
  const {
    clearMessages,
    connectionNotice,
    refreshConversations,
    isConversationsLoading,
  } = useConversationStore();
  const { connectionStatus = 'connected' } = useWebSocket();
  const statusConfig = STATUS_CONFIG[connectionStatus] || {
    label: 'Unknown',
    dot: 'bg-gray-400',
  };

  return (
    <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-3 gap-2 sm:gap-0">
        <div className="flex items-center text-xs font-medium text-gray-600 dark:text-gray-300">
          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${statusConfig.dot}`} aria-hidden="true" />
          <span>{statusConfig.label}</span>
          </div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">AI Assistant</h1>
        {connectionNotice && (
          <span className="inline-flex items-center rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-900 dark:text-amber-100 px-3 py-1 text-xs font-medium shadow-sm">
            {connectionNotice}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 self-start md:self-auto">
        <Button
          variant="ghost"
          size="sm"
          onClick={refreshConversations}
          disabled={isConversationsLoading}
          className="gap-2"
        >
          <svg
            className={`w-4 h-4 ${isConversationsLoading ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v6h6M20 20v-6h-6M5.754 18.246A8 8 0 1118.246 5.754"
            />
          </svg>
          <span>{isConversationsLoading ? 'Refreshing…' : 'Refresh'}</span>
        </Button>

        <Button variant="secondary" size="sm" onClick={clearMessages} className="gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span>Clear Chat</span>
        </Button>
      </div>
    </header>
  );
};

export default EnhancedHeader;
