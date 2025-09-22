import React, { useState } from 'react';
import { Box, TextField, IconButton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

function ChatInput({ onSendMessage }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSendMessage(input);
    setInput('');
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        p: 2,
        display: 'flex',
        alignItems: 'center',
        borderTop: '1px solid',
        borderColor: 'divider',
      }}
    >
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Type a message..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        multiline
        maxRows={4}
      />
      <IconButton type="submit" color="primary" sx={{ ml: 1 }}>
        <SendIcon />
      </IconButton>
    </Box>
  );
}

export default ChatInput;