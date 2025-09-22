import React, { useState, useEffect, useRef } from 'react';
import { Box, CssBaseline, IconButton, Snackbar, Alert, CircularProgress, Tooltip } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import SettingsIcon from '@mui/icons-material/Settings';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import FileUpload from './components/FileUpload';
import SettingsPanel from './components/SettingsPanel';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState(() => {
    const darkMode = localStorage.getItem('darkMode');
    return { model: 'all-MiniLM-L6-v2', numDocs: 3, darkMode: darkMode ? JSON.parse(darkMode) : false };
  });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const ws = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const ws_url = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/chat';
    ws.current = new WebSocket(ws_url);

    ws.current.onopen = () => console.log('WebSocket connected');
    ws.current.onclose = () => console.log('WebSocket disconnected');

    ws.current.onmessage = (event) => {
      let receivedMessage;
      try {
        receivedMessage = JSON.parse(event.data);
      } catch (error) {
        setSnackbar({ open: true, message: 'Received malformed data from server.', severity: 'error' });
        setMessages(prevMessages => [
          ...prevMessages,
          { text: 'Error: Received malformed data from server.', sender: 'bot' }
        ]);
        setIsLoading(false);
        return;
      }

      if (receivedMessage.type === 'chunk') {
        setMessages(prevMessages => {
          const lastMessage = prevMessages[prevMessages.length - 1];
          if (lastMessage && lastMessage.sender === 'bot') {
            // Append to the last bot message if it's a streaming chunk
            return [
              ...prevMessages.slice(0, -1),
              { ...lastMessage, text: lastMessage.text + receivedMessage.content }
            ];
          } else {
            // Add a new bot message
            return [
              ...prevMessages,
              { text: receivedMessage.content, sender: 'bot' }
            ];
          }
        });
      } else if (receivedMessage.type === 'complete') {
        setIsLoading(false);
        setSnackbar({ open: true, message: 'Response complete.', severity: 'success' });
      } else if (receivedMessage.type === 'error') {
        setMessages(prevMessages => [...prevMessages, { text: `Error: ${receivedMessage.message}`, sender: 'bot' }]);
        setIsLoading(false);
        setSnackbar({ open: true, message: receivedMessage.message, severity: 'error' });
      }
    };

    return () => {
      ws.current.close();
    };
  }, []);

  const handleSendMessage = (message) => {
    if (message.trim()) {
      const userMessage = { text: message, sender: 'user' };
      setMessages(prevMessages => [...prevMessages, userMessage]);
      setIsLoading(true);

      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        // Send message in the format expected by the backend
        ws.current.send(JSON.stringify({ type: 'query', question: message }));
      } else {
        setSnackbar({ open: true, message: 'Could not connect to the server.', severity: 'error' });
        setMessages(prevMessages => [...prevMessages, { text: 'Error: Could not connect to the server.', sender: 'bot' }]);
        setIsLoading(false);
      }
    }
  };

  const handleNewConversation = () => {
    if (messages.length > 0) {
      const newConversation = {
        id: Date.now(),
        title: messages[0].text.substring(0, 30),
        messages: [...messages]
      };
      setConversations(prev => [newConversation, ...prev]);
    }
    setMessages([]);
    setCurrentConversationId(null);
  };

  const handleSelectConversation = (id) => {
    const conversation = conversations.find(c => c.id === id);
    if (conversation) {
      setCurrentConversationId(id);
      setMessages(conversation.messages);
    }
  };

  const theme = createTheme({
    palette: {
      mode: settings.darkMode ? 'dark' : 'light',
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh' }}>
        <Sidebar
          conversations={conversations}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
        />
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', p: 1 }}>
            <Tooltip title="Settings">
              <IconButton aria-label="Settings" onClick={() => navigate('/settings')}>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>
          <Routes>
            <Route path="/" element={
              <>
                <FileUpload />
                <Box sx={{ flex: 1, position: 'relative' }}>
                  <ChatWindow messages={messages} isLoading={isLoading} />
                  {isLoading && (
                    <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 10 }}>
                      <CircularProgress />
                    </Box>
                  )}
                </Box>
                <ChatInput onSendMessage={handleSendMessage} />
              </>
            } />
            <Route path="/settings" element={
              <SettingsPanel
                open={true}
                onClose={() => navigate(-1)}
                settings={settings}
                onChange={setSettings}
              />
            } />
            <Route path="/upload" element={<FileUpload />} />
          </Routes>
          <Snackbar
            open={snackbar.open}
            autoHideDuration={4000}
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
          >
            <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} sx={{ width: '100%' }}>
              {snackbar.message}
            </Alert>
          </Snackbar>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
