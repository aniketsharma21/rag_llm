import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';
import EnhancedSidebar from './components/EnhancedSidebar';
import ChatWindow from './components/ChatWindow';
import EnhancedChatInput from './components/EnhancedChatInput';
import EnhancedHeader from './components/EnhancedHeader';
import EnhancedFileUpload from './components/EnhancedFileUpload';
import SettingsPanel from './components/SettingsPanel';

const WEBSOCKET_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/chat';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const JOB_STATUS_POLL_INTERVAL = 2000;
const MAX_RECONNECT_DELAY = 30000;

/**
 * AppContent is the main component that holds the application's state and logic.
 * It's wrapped in a Router in the App component to provide routing context.
 */
const AppContent = () => {
  // State Management
  const [conversations, setConversations] = useState([]); // Stores all past conversations
  const [currentConversationId, setCurrentConversationId] = useState(null); // ID of the conversation currently being viewed
  const [messages, setMessages] = useState([]); // Messages for the currently active chat
  const [isLoading, setIsLoading] = useState(false); // Tracks if the bot is currently generating a response
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light'); // Theme state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false); // Controls the settings panel visibility
  const [searchQuery, setSearchQuery] = useState(''); // Search query for filtering conversations
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('settings');
    return saved ? JSON.parse(saved) : { model: 'llama-3.1-70b-versatile', numDocs: 5 };
  });
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [activeJobs, setActiveJobs] = useState({});

  const ws = useRef(null); // WebSocket connection reference
  const navigate = useNavigate(); // Navigation hook for routing
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const jobPollersRef = useRef({});
  const pendingMessagesRef = useRef([]);
  const isUnmountedRef = useRef(false);

  const appendSystemMessage = useCallback((text) => {
    setMessages(prev => [
      ...prev,
      {
        id: `system-${Date.now()}`,
        sender: 'system',
        text,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const cleanupJobPoller = useCallback((jobId) => {
    const timeoutId = jobPollersRef.current[jobId];
    if (timeoutId) {
      clearTimeout(timeoutId);
      delete jobPollersRef.current[jobId];
    }
  }, []);

  const stopAllJobPollers = useCallback(() => {
    Object.values(jobPollersRef.current).forEach((timeoutId) => clearTimeout(timeoutId));
    jobPollersRef.current = {};
    setActiveJobs({});
  }, []);

  const updateJobMessage = useCallback((jobId, updates) => {
    setMessages(prev => prev.map(msg => (msg.jobId === jobId ? { ...msg, ...updates } : msg)));
  }, []);

  const pollJobStatus = useCallback((jobId, fileName) => {
    const poll = async () => {
      if (isUnmountedRef.current) {
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
        if (!response.ok) {
          throw new Error(`(${response.status}) ${response.statusText}`);
        }

        const statusData = await response.json();
        const status = statusData.status || 'queued';
        const messageText = statusData.message || `Processing ${fileName}...`;
        const isTerminal = ['completed', 'failed', 'skipped'].includes(status);

        updateJobMessage(jobId, {
          text: messageText,
          jobStatus: status,
          isProcessing: !isTerminal,
          details: statusData.details,
        });

        setActiveJobs(prev => {
          const next = {
            ...prev,
            [jobId]: {
              jobId,
              fileName,
              status,
              message: messageText,
              details: statusData.details,
              isProcessing: !isTerminal,
            },
          };
          if (isTerminal) {
            const { [jobId]: _, ...rest } = next;
            return rest;
          }
          return next;
        });

        if (isTerminal) {
          cleanupJobPoller(jobId);
          if (status === 'failed') {
            appendSystemMessage(`Processing failed for ${fileName}: ${statusData.error || 'Unknown error'}`);
          } else if (status === 'completed') {
            appendSystemMessage(`Document processed: ${fileName}`);
          } else if (status === 'skipped') {
            appendSystemMessage(`Document unchanged: ${fileName}`);
          }
        } else {
          cleanupJobPoller(jobId);
          jobPollersRef.current[jobId] = window.setTimeout(poll, JOB_STATUS_POLL_INTERVAL);
        }
      } catch (error) {
        cleanupJobPoller(jobId);
        updateJobMessage(jobId, {
          text: `Failed to retrieve status for ${fileName}: ${error.message}`,
          jobStatus: 'error',
          isProcessing: false,
        });
        appendSystemMessage(`Failed to retrieve status for ${fileName}. Please try again later.`);
        setActiveJobs(prev => {
          const { [jobId]: _, ...rest } = prev;
          return rest;
        });
      }
    };

    poll();
  }, [appendSystemMessage, cleanupJobPoller, updateJobMessage, setActiveJobs]);

  const handleJobSubmission = useCallback((jobId, fileName, initialMessage, initialStatus) => {
    setMessages(prev => [
      ...prev,
      {
        id: `job-${jobId}`,
        sender: 'system',
        text: initialMessage || `Processing ${fileName}...`,
        jobId,
        fileName,
        jobStatus: initialStatus || 'queued',
        isProcessing: true,
        timestamp: new Date().toISOString(),
      },
    ]);

    pollJobStatus(jobId, fileName);

    setActiveJobs(prev => ({
      ...prev,
      [jobId]: {
        jobId,
        fileName,
        status: initialStatus || 'queued',
        message: initialMessage || `Processing ${fileName}...`,
        details: {},
        isProcessing: true,
      },
    }));
  }, [pollJobStatus, setActiveJobs]);

  const connectWebSocket = useCallback(() => {
    if (isUnmountedRef.current) {
      return;
    }

    setConnectionStatus('connecting');

    if (ws.current) {
      const state = ws.current.readyState;
      if (state === WebSocket.OPEN || state === WebSocket.CLOSING) {
        try {
          ws.current.close();
        } catch (error) {
          console.error('Error closing existing WebSocket:', error);
        }
      }
    }

    const socket = new WebSocket(WEBSOCKET_URL);
    ws.current = socket;

    socket.onopen = () => {
      setConnectionStatus('connected');
      if (reconnectAttemptsRef.current > 0) {
        appendSystemMessage('Reconnected to the server.');
      }
      reconnectAttemptsRef.current = 0;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      let flushedCount = 0;
      while (pendingMessagesRef.current.length > 0 && socket.readyState === WebSocket.OPEN) {
        const payload = pendingMessagesRef.current.shift();
        try {
          socket.send(JSON.stringify(payload));
          flushedCount += 1;
        } catch (error) {
          console.error('Failed to flush pending message:', error);
          pendingMessagesRef.current.unshift(payload);
          break;
        }
      }

      if (flushedCount > 0) {
        setIsLoading(true);
      }
    };

    socket.onmessage = (event) => {
      let receivedMessage;
      try {
        receivedMessage = JSON.parse(event.data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        return;
      }

      if (receivedMessage.type === 'status') {
        if (receivedMessage.status === 'processing') {
          setIsLoading(true);
        } else if (receivedMessage.status === 'stopped') {
          setIsLoading(false);
          appendSystemMessage('Generation stopped.');
        } else if (receivedMessage.status === 'connected') {
          setConnectionStatus('connected');
        } else if (receivedMessage.status === 'idle' || receivedMessage.status === 'completed') {
          setIsLoading(false);
        }
        return;
      }

      if (receivedMessage.type === 'chunk') {
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.sender === 'bot') {
            updated[updated.length - 1] = {
              ...lastMsg,
              text: (lastMsg.text || '') + (receivedMessage.content || ''),
              timestamp: lastMsg.timestamp || new Date().toISOString(),
            };
            return updated;
          }
          return [
            ...updated,
            {
              text: receivedMessage.content || '',
              sender: 'bot',
              sources: [],
              id: Date.now(),
              timestamp: new Date().toISOString(),
            },
          ];
        });
        return;
      }

      if (receivedMessage.type === 'complete') {
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          const finalContent = receivedMessage.content || lastMsg?.text || '';
          if (lastMsg && lastMsg.sender === 'bot') {
            updated[updated.length - 1] = {
              ...lastMsg,
              text: finalContent,
              sources: receivedMessage.sources || [],
              id: Date.now(),
            };
            return updated;
          }
          return [
            ...updated,
            {
              text: finalContent,
              sender: 'bot',
              sources: receivedMessage.sources || [],
              id: Date.now(),
              timestamp: new Date().toISOString(),
            },
          ];
        });
        setIsLoading(false);
        return;
      }

      if (receivedMessage.type === 'error') {
        appendSystemMessage(`An error occurred: ${receivedMessage.message}`);
        setIsLoading(false);
        return;
      }

      if (receivedMessage.type === 'pong') {
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

      ws.current = null;
      setConnectionStatus('disconnected');
      stopAllJobPollers();

      reconnectAttemptsRef.current += 1;
      const delay = Math.min(1000 * 2 ** Math.max(reconnectAttemptsRef.current - 1, 0), MAX_RECONNECT_DELAY);

      if (reconnectAttemptsRef.current === 1) {
        appendSystemMessage('Connection lost. Attempting to reconnect...');
      } else {
        appendSystemMessage(`Reconnecting in ${Math.round(delay / 1000)}s...`);
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      reconnectTimeoutRef.current = window.setTimeout(() => {
        reconnectTimeoutRef.current = null;
        connectWebSocket();
      }, delay);
    };
  }, [appendSystemMessage, stopAllJobPollers]);

  useEffect(() => {
    isUnmountedRef.current = false;
    connectWebSocket();

    return () => {
      isUnmountedRef.current = true;
      if (ws.current) {
        try {
          ws.current.close();
        } catch (error) {
          console.error('Error closing WebSocket on unmount:', error);
        }
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      stopAllJobPollers();
    };
  }, [connectWebSocket, stopAllJobPollers]);

  // --- Theme and Settings Management ---

  /**
   * Applies the theme to the document root and persists it to local storage.
   */
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  /**
   * Persists user settings to local storage whenever they change.
   */
  useEffect(() => {
    localStorage.setItem('settings', JSON.stringify(settings));
  }, [settings]);

  // --- Event Handlers ---

  const handleThemeToggle = () => setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  const handleSettingsSave = (newSettings) => setSettings(newSettings);

  /**
   * Sends a user's message to the backend via WebSocket.
   * @param {string} message - The text of the message to send.
   */
  const handleSendMessage = useCallback((message) => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) {
      return;
    }

    setMessages(prev => [
      ...prev,
      { text: trimmedMessage, sender: 'user', timestamp: new Date().toISOString() },
    ]);

    const payload = {
      type: 'query',
      question: trimmedMessage,
      settings: { model: settings.model, num_docs: settings.numDocs },
    };

    if (ws.current?.readyState === WebSocket.OPEN) {
      setIsLoading(true);
      ws.current.send(JSON.stringify(payload));
      return;
    }

    pendingMessagesRef.current.push(payload);

    if (connectionStatus === 'connected') {
      setConnectionStatus('connecting');
    }

    if (!ws.current || ws.current.readyState === WebSocket.CLOSED) {
      connectWebSocket();
    }

    appendSystemMessage('Waiting for server connection. Your request will be sent once connected.');
  }, [connectionStatus, connectWebSocket, settings.model, settings.numDocs, appendSystemMessage]);

  /**
   * Sends user feedback for a specific message to the backend.
   * @param {string} messageId - The ID of the message being rated.
   * @param {string} feedback - The feedback value ('helpful' or 'not_helpful').
   */
  const handleFeedback = (messageId, feedback) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'feedback', message_id: messageId, feedback }));
    }
  };

  /**
   * Handles file upload from chat input - ADDED MISSING FUNCTION
   * @param {Array} files - Array of files to upload
   */
  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) {
      return;
    }

    const successes = [];
    const failures = [];

    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch(`${API_BASE_URL}/ingest`, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok && data.job_id) {
          successes.push({ file, data });
        } else {
          const message = data?.message || data?.detail || 'Upload failed';
          failures.push({ file, message });
        }
      } catch (error) {
        failures.push({ file, message: error.message });
      }
    }

    if (successes.length > 0) {
      successes.forEach(({ file, data }) => {
        handleJobSubmission(
          data.job_id,
          file.name,
          data.message || `Processing ${file.name}...`,
          data.status,
        );
      });
    }

    if (failures.length > 0) {
      appendSystemMessage(
        `Failed to upload ${failures.length} file(s): ${failures
          .map(({ file, message: msg }) => `${file.name} (${msg})`)
          .join('; ')}`,
      );
    }
  };

  const handleStopGeneration = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'stop_generation' }));
    }
    setIsLoading(false);
  }, []);

  /**
   * Saves the current chat session to the conversation history if it's new.
   */
  const saveCurrentConversation = () => {
    if (messages.length > 0 && currentConversationId === null) {
      const newConversation = { id: Date.now(), title: messages[0].text.substring(0, 30), messages: [...messages] };
      setConversations(prev => [newConversation, ...prev]);
    }
  };

  /**
   * Saves the current chat (if new) and starts a fresh chat session.
   */
  const handleNewConversation = () => {
    saveCurrentConversation();
    setMessages([]);
    setCurrentConversationId(null);
    navigate('/');
  };

  /**
   * Loads a selected conversation from the history into the main chat window.
   * @param {string} id - The ID of the conversation to load.
   */
  const handleSelectConversation = (id) => {
    if (id === currentConversationId) return;
    saveCurrentConversation(); // Save the current work before switching
    const conversation = conversations.find(c => c.id === id);
    if (conversation) {
      setCurrentConversationId(id);
      setMessages(conversation.messages);
      navigate('/');
    }
  };

  /**
   * Clears the messages from the current chat window without saving it to history.
   */
  const handleClearChat = () => {
    setMessages([]);
  };

  // Filters conversation history based on the search query
  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark font-display flex h-screen">
      <EnhancedSidebar
        theme={theme}
        onThemeToggle={handleThemeToggle}
        conversations={filteredConversations}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        currentConversationId={currentConversationId}
        onSettingsClick={() => setIsSettingsOpen(true)}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />
      <div className="flex-1 flex flex-col max-w-full overflow-hidden">
        <EnhancedHeader onClearChat={handleClearChat} connectionStatus={connectionStatus} />
        <Routes>
          <Route path="/" element={
            <div className="flex-1 flex flex-col overflow-y-hidden">
              <ChatWindow messages={messages} isLoading={isLoading} onFeedback={handleFeedback} onStop={handleStopGeneration} />
              <EnhancedChatInput onSendMessage={handleSendMessage} onFileUpload={handleFileUpload} activeJobs={activeJobs} />
            </div>
          }/>
          <Route path="/upload" element={<EnhancedFileUpload />} />
        </Routes>
      </div>
      <SettingsPanel
        open={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        onSave={handleSettingsSave}
      />
    </div>
  );
};

/**
 * Main App component that wraps AppContent with Router for routing context.
 */
const App = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;
