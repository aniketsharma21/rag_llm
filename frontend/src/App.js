import React, { useState, useEffect, useRef } from 'react';
import { Box, CssBaseline } from '@mui/material';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import FileUpload from './components/FileUpload';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    const ws_url = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/chat';
    ws.current = new WebSocket(ws_url);

    ws.current.onopen = () => console.log('WebSocket connected');
    ws.current.onclose = () => console.log('WebSocket disconnected');

    ws.current.onmessage = (event) => {
      const receivedMessage = JSON.parse(event.data);

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
      } else if (receivedMessage.type === 'error') {
        setMessages(prevMessages => [...prevMessages, { text: `Error: ${receivedMessage.message}`, sender: 'bot' }]);
        setIsLoading(false);
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
        console.error('WebSocket is not connected.');
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

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <CssBaseline />
      <Sidebar 
        conversations={conversations}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
      />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <FileUpload />
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSendMessage={handleSendMessage} />
      </Box>
    </Box>
  );
}

export default App;
