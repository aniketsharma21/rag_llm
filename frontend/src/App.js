import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
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
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light'); // UI theme: 'light' or 'dark'
  const [isSettingsOpen, setIsSettingsOpen] = useState(false); // Controls the visibility of the settings modal
  const [searchQuery, setSearchQuery] = useState(''); // Input for searching conversation history
  const [settings, setSettings] = useState(() => { // User-configurable settings
    const savedSettings = localStorage.getItem('settings');
    const defaults = { model: 'all-MiniLM-L6-v2', numDocs: 3 };
    return savedSettings ? { ...defaults, ...JSON.parse(savedSettings) } : defaults;
  });
  const ws = useRef(null); // Ref to hold the WebSocket instance
  const navigate = useNavigate(); // Hook for programmatic navigation

  /**
   * Initializes and manages the WebSocket connection to the backend.
   * Handles incoming messages for streaming responses, completion, and errors.
   */
  useEffect(() => {
    const ws_url = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/chat';
    ws.current = new WebSocket(ws_url);
    ws.current.onopen = () => console.log('WebSocket connected');
    ws.current.onclose = () => console.log('WebSocket disconnected');

    ws.current.onmessage = (event) => {
      const receivedMessage = JSON.parse(event.data);
      if (receivedMessage.type === 'chunk') {
        // Append content to the last bot message for a streaming effect
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.sender === 'bot') {
            return [...prev.slice(0, -1), { ...lastMsg, text: lastMsg.text + receivedMessage.content }];
          }
          return [...prev, { text: receivedMessage.content, sender: 'bot', sources: [] }];
        });
      } else if (receivedMessage.type === 'complete') {
        // Finalize the bot's message with ID and sources
        if (receivedMessage.message) {
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.sender === 'bot') {
              return [...prev.slice(0, -1), { ...lastMsg, ...receivedMessage.message }];
            }
            return [...prev, receivedMessage.message]; // Handle non-streamed responses
          });
        }
        setIsLoading(false);
      } else if (receivedMessage.type === 'error') {
        setMessages(prev => [...prev, { text: `Error: ${receivedMessage.message}`, sender: 'bot' }]);
        setIsLoading(false);
      }
    };
    // Cleanup WebSocket connection on component unmount
    return () => ws.current.close();
  }, []);

  /**
   * Manages the application's theme by toggling the 'dark' class on the root element
   * and persisting the theme choice in local storage.
   */
  useEffect(() => {
    const root = window.document.documentElement;
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
      <Sidebar
        theme={theme}
        onThemeToggle={handleThemeToggle}
        conversations={filteredConversations}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        currentConversationId={currentConversationId}
        onSettingsClick={() => setIsSettingsOpen(true)}
      />
      <div className="flex-1 flex flex-col max-w-full overflow-hidden">
        <Header onClearChat={handleClearChat} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <Routes>
          <Route path="/" element={
            <div className="flex-1 flex flex-col overflow-y-hidden">
              <ChatWindow messages={messages} isLoading={isLoading} onFeedback={handleFeedback} />
              <ChatInput onSendMessage={handleSendMessage} />
            </div>
          }/>
          <Route path="/upload" element={<FileUpload />} />
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
 * The root App component wraps the main application content in a Router
 * to enable client-side navigation.
 */
function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;