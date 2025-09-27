import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';
import EnhancedSidebar from './components/EnhancedSidebar';
import ChatWindow from './components/ChatWindow';
import EnhancedChatInput from './components/EnhancedChatInput';
import EnhancedHeader from './components/EnhancedHeader';
import EnhancedFileUpload from './components/EnhancedFileUpload';
import SettingsPanel from './components/SettingsPanel';

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

  const ws = useRef(null); // WebSocket connection reference
  const navigate = useNavigate(); // Navigation hook for routing

  // --- WebSocket Connection ---

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws/chat');
    ws.current.onopen = () => console.log('WebSocket connected');
    ws.current.onclose = () => console.log('WebSocket disconnected');

    ws.current.onmessage = (event) => {
      const receivedMessage = JSON.parse(event.data);
      if (receivedMessage.type === 'chunk') {
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.sender === 'bot') {
            return [...prev.slice(0, -1), { 
              ...lastMsg, 
              text: (lastMsg.text || '') + (receivedMessage.content || '')
            }];
          }
          return [...prev, { 
            text: receivedMessage.content || '', 
            sender: 'bot', 
            sources: [],
            id: Date.now() 
          }];
        });
      } else if (receivedMessage.type === 'complete') {
        // Finalize the bot's message with sources - FIXED SOURCES HANDLING
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.sender === 'bot') {
            return [...prev.slice(0, -1), { 
              ...lastMsg, 
              sources: receivedMessage.sources || [],
              id: Date.now()
            }];
          }
          return [...prev, {
            text: receivedMessage.content || '',
            sender: 'bot',
            sources: receivedMessage.sources || [],
            id: Date.now()
          }];
        });
        setIsLoading(false);
      } else if (receivedMessage.type === 'error') {
        setMessages(prev => [...prev, { text: `An error occurred: ${receivedMessage.message}`, sender: 'bot' }]);
        setIsLoading(false);
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

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
  const handleSendMessage = (message) => {
    if (message.trim()) {
      setIsLoading(true);
      setMessages(prev => [...prev, { text: message, sender: 'user' }]);
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: 'query', question: message, settings: { model: settings.model, num_docs: settings.numDocs } }));
      } else {
        setMessages(prev => [...prev, { text: 'Error: Could not connect to the server.', sender: 'bot' }]);
        setIsLoading(false);
      }
    }
  };

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
        const response = await fetch('http://localhost:8000/ingest', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
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
      setMessages(prev => [...prev, {
        text: `Uploaded ${successes.length} file(s): ${successes.map(({ file }) => file.name).join(', ')}`,
        sender: 'system'
      }]);
    }

    if (failures.length > 0) {
      setMessages(prev => [...prev, {
        text: `Failed to upload ${failures.length} file(s): ${failures.map(({ file, message }) => `${file.name} (${message})`).join('; ')}`,
        sender: 'system'
      }]);
    }
  };

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
        <EnhancedHeader onClearChat={handleClearChat} />
        <Routes>
          <Route path="/" element={
            <div className="flex-1 flex flex-col overflow-y-hidden">
              <ChatWindow messages={messages} isLoading={isLoading} onFeedback={handleFeedback} />
              <EnhancedChatInput onSendMessage={handleSendMessage} onFileUpload={handleFileUpload} />
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
