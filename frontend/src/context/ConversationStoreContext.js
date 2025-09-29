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

const ConversationStoreContext = createContext(null);

const THEME_KEY = 'theme';
const SETTINGS_KEY = 'settings';
const DEFAULT_SETTINGS = { model: 'llama-3.1-70b-versatile', numDocs: 5 };

const readJsonValue = (key, fallback) => {
  if (typeof window === 'undefined') {
    return fallback;
  }

  try {
    const stored = window.localStorage.getItem(key);
    if (!stored) {
      return fallback;
    }
    return JSON.parse(stored);
  } catch (error) {
    console.warn(`Failed to parse ${key} from localStorage`, error);
    return fallback;
  }
};

const readTheme = () => {
  if (typeof window === 'undefined') {
    return 'light';
  }
  return window.localStorage.getItem(THEME_KEY) || 'light';
};

export const ConversationStoreProvider = ({ children }) => {
  const { apiBaseUrl, jobStatusPollInterval } = useConfig();

  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [theme, setTheme] = useState(readTheme);
  const [settings, setSettings] = useState(() => readJsonValue(SETTINGS_KEY, DEFAULT_SETTINGS));
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeJobs, setActiveJobs] = useState({});
  const [connectionNotice, setConnectionNotice] = useState(null);

  const jobPollersRef = useRef({});
  const isUnmountedRef = useRef(false);

  const addMessage = useCallback((message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const updateMessageById = useCallback((id, updater) => {
    setMessages((prev) => prev.map((msg) => (msg.id === id ? updater(msg) : msg)));
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const appendSystemMessage = useCallback(
    (text) => {
      addMessage({
        id: `system-${Date.now()}`,
        sender: 'system',
        text,
        timestamp: new Date().toISOString(),
      });
    },
    [addMessage],
  );

  const addUserMessage = useCallback(
    (text) => {
      const id = `user-${Date.now()}`;
      addMessage({
        id,
        sender: 'user',
        text,
        timestamp: new Date().toISOString(),
      });
      return id;
    },
    [addMessage],
  );

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', theme === 'dark');
    }
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(THEME_KEY, theme);
    }
  }, [theme]);

  const openSettings = useCallback(() => setIsSettingsOpen(true), []);
  const closeSettings = useCallback(() => setIsSettingsOpen(false), []);

  const saveSettings = useCallback((nextSettings) => {
    setSettings(nextSettings);
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    }
  }, [settings]);

  const saveCurrentConversation = useCallback(() => {
    if (messages.length === 0 || currentConversationId !== null) {
      return;
    }

    const title = messages[0]?.text?.slice(0, 30) || 'Conversation';
    const newConversation = {
      id: Date.now(),
      title,
      messages: [...messages],
    };
    setConversations((prev) => [newConversation, ...prev]);
  }, [messages, currentConversationId]);

  const startNewConversation = useCallback(() => {
    saveCurrentConversation();
    setMessages([]);
    setCurrentConversationId(null);
  }, [saveCurrentConversation]);

  const selectConversation = useCallback(
    (id) => {
      if (id === currentConversationId) {
        return;
      }

      saveCurrentConversation();
      const conversation = conversations.find((item) => item.id === id);
      if (conversation) {
        setCurrentConversationId(id);
        setMessages(conversation.messages);
      }
    },
    [conversations, currentConversationId, saveCurrentConversation],
  );

  const filteredConversations = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return conversations;
    }
    return conversations.filter((item) => item.title.toLowerCase().includes(query));
  }, [conversations, searchQuery]);

  const getMessageById = useCallback(
    (id) => messages.find((message) => message.id === id),
    [messages],
  );

  const stopAllJobPollers = useCallback(() => {
    Object.values(jobPollersRef.current).forEach((timeoutId) => {
      clearTimeout(timeoutId);
    });
    jobPollersRef.current = {};
    setActiveJobs({});
  }, []);

  useEffect(() => {
    isUnmountedRef.current = false;

    return () => {
      isUnmountedRef.current = true;
      stopAllJobPollers();
      setConnectionNotice(null);
    };
  }, [stopAllJobPollers, setConnectionNotice]);

  const cleanupJobPoller = useCallback((jobId) => {
    const timeoutId = jobPollersRef.current[jobId];
    if (timeoutId) {
      clearTimeout(timeoutId);
      delete jobPollersRef.current[jobId];
    }
  }, []);

  const updateJobMessage = useCallback(
    (jobId, updates) => {
      const messageId = `job-${jobId}`;
      updateMessageById(messageId, (msg) => ({ ...msg, ...updates }));
    },
    [updateMessageById],
  );

  const pollJobStatus = useCallback(
    (jobId, fileName) => {
      const poll = async () => {
        if (isUnmountedRef.current) {
          return;
        }

        try {
          const response = await fetch(`${apiBaseUrl}/status/${jobId}`);
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

          setActiveJobs((prev) => {
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
              const { [jobId]: _ignored, ...rest } = next;
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
            jobPollersRef.current[jobId] = window.setTimeout(poll, jobStatusPollInterval);
          }
        } catch (error) {
          cleanupJobPoller(jobId);
          updateJobMessage(jobId, {
            text: `Failed to retrieve status for ${fileName}: ${error.message}`,
            jobStatus: 'error',
            isProcessing: false,
          });
          appendSystemMessage(`Failed to retrieve status for ${fileName}. Please try again later.`);
          setActiveJobs((prev) => {
            const { [jobId]: _removed, ...rest } = prev;
            return rest;
          });
        }
      };

      poll();
    },
    [apiBaseUrl, appendSystemMessage, cleanupJobPoller, jobStatusPollInterval, updateJobMessage],
  );

  const handleJobSubmission = useCallback(
    (jobId, fileName, initialMessage, initialStatus) => {
      addMessage({
        id: `job-${jobId}`,
        sender: 'system',
        text: initialMessage || `Processing ${fileName}...`,
        jobId,
        fileName,
        jobStatus: initialStatus || 'queued',
        isProcessing: true,
        timestamp: new Date().toISOString(),
      });

      pollJobStatus(jobId, fileName);

      setActiveJobs((prev) => ({
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
    },
    [addMessage, pollJobStatus],
  );

  const handleFileUpload = useCallback(
    async (files) => {
      if (!files || files.length === 0) {
        return;
      }

      const successes = [];
      const failures = [];

      // eslint-disable-next-line no-restricted-syntax
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        try {
          const response = await fetch(`${apiBaseUrl}/ingest`, {
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
            .map(({ file, message }) => `${file.name} (${message})`)
            .join('; ')}`,
        );
      }
    },
    [apiBaseUrl, appendSystemMessage, handleJobSubmission],
  );

  const value = useMemo(
    () => ({
      // Conversations and messages
      messages,
      addMessage,
      updateMessageById,
      clearMessages,
      appendSystemMessage,
      addUserMessage,
      conversations,
      filteredConversations,
      getMessageById,
      currentConversationId,
      setCurrentConversationId,
      startNewConversation,
      selectConversation,
      searchQuery,
      setSearchQuery,

      // Theme & settings
      theme,
      toggleTheme,
      settings,
      saveSettings,
      isSettingsOpen,
      openSettings,
      closeSettings,

      // Jobs & uploads
      activeJobs,
      handleJobSubmission,
      handleFileUpload,
      stopAllJobPollers,

      // Connection status
      connectionNotice,
      setConnectionNotice,
    }),
    [
      messages,
      addMessage,
      updateMessageById,
      clearMessages,
      appendSystemMessage,
      addUserMessage,
      conversations,
      filteredConversations,
      currentConversationId,
      startNewConversation,
      selectConversation,
      searchQuery,
      theme,
      toggleTheme,
      settings,
      saveSettings,
      isSettingsOpen,
      openSettings,
      closeSettings,
      activeJobs,
      handleJobSubmission,
      handleFileUpload,
      stopAllJobPollers,
      getMessageById,
      connectionNotice,
      setConnectionNotice,
    ],
  );

  return (
    <ConversationStoreContext.Provider value={value}>
      {children}
    </ConversationStoreContext.Provider>
  );
};

export const useConversationStore = () => {
  const context = useContext(ConversationStoreContext);
  if (!context) {
    throw new Error('useConversationStore must be used within a ConversationStoreProvider');
  }
  return context;
};
