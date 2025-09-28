import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import { useConfig } from './ConfigContext';
import { useConversationStore } from './ConversationStoreContext';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children }) => {
  const { websocketUrl, maxReconnectDelay } = useConfig();
  const {
    appendSystemMessage,
    addMessage,
    updateMessageById,
    addUserMessage,
    settings,
    stopAllJobPollers,
  } = useConversationStore();

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const pendingMessagesRef = useRef([]);
  const currentResponseIdRef = useRef(null);
  const lastCompletionRef = useRef({ content: '', timestamp: 0 });
  const isUnmountedRef = useRef(false);

  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [isLoading, setIsLoading] = useState(false);

  const flushPendingMessages = useCallback(() => {
    const socket = wsRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }

    let flushed = 0;
    while (pendingMessagesRef.current.length > 0) {
      const payload = pendingMessagesRef.current.shift();
      try {
        socket.send(JSON.stringify(payload));
        flushed += 1;
      } catch (error) {
        pendingMessagesRef.current.unshift(payload);
        console.error('Failed to flush pending message:', error);
        break;
      }
    }

    if (flushed > 0) {
      setIsLoading(true);
    }
  }, []);

  const handleChunkMessage = useCallback(
    (message) => {
      const content = message.content || '';
      if (!content) {
        return;
      }

      const isSummary = message.role === 'summary';

      if (isSummary || !currentResponseIdRef.current) {
        const responseId = `bot-${Date.now()}`;
        currentResponseIdRef.current = responseId;
        addMessage({
          id: responseId,
          sender: 'bot',
          text: content,
          sources: [],
          timestamp: new Date().toISOString(),
        });
        return;
      }

      const responseId = currentResponseIdRef.current;
      let found = false;
      updateMessageById(responseId, (existing) => {
        if (!existing) {
          return existing;
        }
        found = true;
        const separator = existing.text ? '\n\n' : '';
        return {
          ...existing,
          text: `${existing.text || ''}${separator}${content}`,
        };
      });

      if (!found) {
        addMessage({
          id: responseId,
          sender: 'bot',
          text: content,
          sources: [],
          timestamp: new Date().toISOString(),
        });
      }
    },
    [addMessage, updateMessageById],
  );

  const handleCompleteMessage = useCallback(
    (message) => {
      const finalContent = message.content || '';
      const sources = message.sources || [];
      const responseId = currentResponseIdRef.current;
      const now = Date.now();

      if (
        finalContent &&
        lastCompletionRef.current.content === finalContent &&
        now - lastCompletionRef.current.timestamp < 1000
      ) {
        setIsLoading(false);
        currentResponseIdRef.current = null;
        return;
      }

      if (responseId) {
        let updated = false;
        updateMessageById(responseId, (existing) => {
          if (!existing) {
            return existing;
          }
          updated = true;
          return {
            ...existing,
            text: finalContent || existing.text || '',
            sources: sources.length ? sources : existing.sources || [],
          };
        });

        if (!updated) {
          addMessage({
            id: `bot-${Date.now()}`,
            sender: 'bot',
            text: finalContent,
            sources,
            timestamp: new Date().toISOString(),
          });
        }
      } else {
        addMessage({
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: finalContent,
          sources,
          timestamp: new Date().toISOString(),
        });
      }

      setIsLoading(false);
      currentResponseIdRef.current = null;
      lastCompletionRef.current = { content: finalContent, timestamp: now };
    },
    [addMessage, updateMessageById],
  );

  const connectWebSocket = useCallback(() => {
    if (isUnmountedRef.current) {
      return;
    }

    const existing = wsRef.current;
    if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setConnectionStatus('connecting');

    const socket = new WebSocket(websocketUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      if (isUnmountedRef.current) {
        return;
      }
      setConnectionStatus('connected');
      setIsLoading(false);
      reconnectAttemptsRef.current = 0;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      flushPendingMessages();
    };

    socket.onmessage = (event) => {
      if (isUnmountedRef.current) {
        return;
      }

      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        return;
      }

      if (payload.type === 'status') {
        if (payload.status === 'processing') {
          setIsLoading(true);
        } else if (payload.status === 'stopped') {
          setIsLoading(false);
          currentResponseIdRef.current = null;
          appendSystemMessage('Generation stopped.');
        } else if (payload.status === 'connected') {
          setConnectionStatus('connected');
        } else if (payload.status === 'idle' || payload.status === 'completed') {
          setIsLoading(false);
        }
        return;
      }

      if (payload.type === 'chunk') {
        handleChunkMessage(payload);
        return;
      }

      if (payload.type === 'complete') {
        handleCompleteMessage(payload);
        return;
      }

      if (payload.type === 'error') {
        appendSystemMessage(`An error occurred: ${payload.message}`);
        setIsLoading(false);
        currentResponseIdRef.current = null;
        return;
      }

      if (payload.type === 'pong') {
        return;
      }
    };

    socket.onerror = (event) => {
      console.error('WebSocket error:', event);
      try {
        socket.close();
      } catch (error) {
        console.error('Error closing socket after error:', error);
      }
    };

    socket.onclose = () => {
      if (isUnmountedRef.current) {
        return;
      }

      wsRef.current = null;
      setConnectionStatus('disconnected');
      stopAllJobPollers();
      currentResponseIdRef.current = null;

      reconnectAttemptsRef.current += 1;
      const delay = Math.min(
        1000 * 2 ** Math.max(reconnectAttemptsRef.current - 1, 0),
        maxReconnectDelay,
      );

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectTimeoutRef.current = null;
        connectWebSocket();
      }, delay);
    };
  }, [
    appendSystemMessage,
    flushPendingMessages,
    handleChunkMessage,
    handleCompleteMessage,
    maxReconnectDelay,
    stopAllJobPollers,
    websocketUrl,
  ]);

  useEffect(() => {
    isUnmountedRef.current = false;
    connectWebSocket();

    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      const socket = wsRef.current;
      if (socket && socket.readyState === WebSocket.OPEN) {
        try {
          socket.close();
        } catch (error) {
          console.error('Error closing WebSocket on unmount:', error);
        }
      }
    };
  }, [connectWebSocket]);

  const sendPayload = useCallback((payload) => {
    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
      return true;
    }

    pendingMessagesRef.current.push(payload);
    connectWebSocket();
    return false;
  }, [connectWebSocket]);

  const sendMessage = useCallback((text) => {
    const trimmed = text.trim();
    if (!trimmed) {
      return;
    }

    addUserMessage(trimmed);
    currentResponseIdRef.current = null;

    const payload = {
      type: 'query',
      question: trimmed,
      settings: {
        model: settings.model,
        num_docs: settings.numDocs,
      },
    };

    lastCompletionRef.current = { content: '', timestamp: 0 };
    const wasSent = sendPayload(payload);
    if (wasSent) {
      setIsLoading(true);
    } else {
      setConnectionStatus('connecting');
      appendSystemMessage('Waiting for server connection. Your request will be sent once connected.');
    }
  }, [addUserMessage, appendSystemMessage, sendPayload, settings.model, settings.numDocs]);

  const stopGeneration = useCallback(() => {
    const payload = { type: 'stop_generation' };
    sendPayload(payload);
    setIsLoading(false);
    currentResponseIdRef.current = null;
  }, [sendPayload]);

  const handleFeedback = useCallback((messageId, feedback) => {
    const payload = { type: 'feedback', message_id: messageId, feedback };
    sendPayload(payload);
  }, [sendPayload]);

  const value = useMemo(() => ({
    connectionStatus,
    isLoading,
    sendMessage,
    stopGeneration,
    handleFeedback,
  }), [connectionStatus, handleFeedback, isLoading, sendMessage, stopGeneration]);

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
