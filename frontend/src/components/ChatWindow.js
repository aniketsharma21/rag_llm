import React from 'react';
import { Box } from '@mui/material';
import Message from './Message';

function ChatWindow({ messages, isLoading }) {
  return (
    <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 3 }}>
      {messages.map((msg, index) => (
        <Message key={index} text={msg.text} sender={msg.sender} />
      ))}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </Box>
      )}
    </Box>
  );
}

export default ChatWindow;