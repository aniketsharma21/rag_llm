import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import SettingsPanel from './components/SettingsPanel';

const AppContent = () => {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [settings, setSettings] = useState(() => {
    const savedSettings = localStorage.getItem('settings');
    const defaults = { model: 'all-MiniLM-L6-v2', numDocs: 3 };
    return savedSettings ? { ...defaults, ...JSON.parse(savedSettings) } : defaults;
  });
  const ws = useRef(null);
  const navigate = useNavigate();

  // WebSocket connection logic
  useEffect(() => {
    const ws_url = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/chat';
    ws.current = new WebSocket(ws_url);
    ws.current.onopen = () => console.log('WebSocket connected');
    ws.current.onclose = () => console.log('WebSocket disconnected');

    ws.current.onmessage = (event) => {
      const receivedMessage = JSON.parse(event.data);
      if (receivedMessage.type === 'chunk') {
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.sender === 'bot') {
            return [...prev.slice(0, -1), { ...lastMsg, text: lastMsg.text + receivedMessage.content }];
          }
          return [...prev, { text: receivedMessage.content, sender: 'bot', sources: [] }];
        });
      } else if (receivedMessage.type === 'complete') {
        if (receivedMessage.message) {
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.sender === 'bot') {
              return [...prev.slice(0, -1), { ...lastMsg, ...receivedMessage.message }];
            }
            // Handle non-streamed case where 'complete' is the first and only message
            return [...prev, receivedMessage.message];
          });
        }
        setIsLoading(false);
      } else if (receivedMessage.type === 'error') {
        setMessages(prev => [...prev, { text: `Error: ${receivedMessage.message}`, sender: 'bot' }]);
        setIsLoading(false);
      }
    };
    return () => ws.current.close();
  }, []);

  // Theme & Settings management logic
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('settings', JSON.stringify(settings));
  }, [settings]);

  const handleThemeToggle = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  const handleSettingsSave = (newSettings) => {
    setSettings(newSettings);
  };

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

  const handleFeedback = (messageId, feedback) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'feedback', message_id: messageId, feedback }));
    }
  };

  const saveCurrentConversation = () => {
    // Only save if there are messages and it's not an already saved conversation
    if (messages.length > 0 && currentConversationId === null) {
      const newConversation = { id: Date.now(), title: messages[0].text.substring(0, 30), messages: [...messages] };
      setConversations(prev => [newConversation, ...prev]);
      // We don't set currentConversationId here, so the user can continue the chat and save it as another new one if they wish.
    }
  };

  const handleNewConversation = () => {
    saveCurrentConversation();
    setMessages([]);
    setCurrentConversationId(null);
    navigate('/');
  };

  const handleSelectConversation = (id) => {
    if (id === currentConversationId) return;
    saveCurrentConversation();
    const conversation = conversations.find(c => c.id === id);
    if (conversation) {
      setCurrentConversationId(id);
      setMessages(conversation.messages);
      navigate('/');
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

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

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;