import React, { useState } from 'react';
import { Box, TextField, IconButton, Tooltip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

function ChatInput({ onSendMessage }) {
  const [input, setInput] = useState('');
  const [error, setError] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) {
      setError(true);
      return;
    }
    onSendMessage(input);
    setInput('');
    setError(false);
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
        onChange={(e) => {
          setInput(e.target.value);
          if (error && e.target.value.trim()) setError(false);
        }}
        multiline
        maxRows={4}
        error={error}
        helperText={error ? 'Message cannot be empty.' : ''}
        inputProps={{ 'aria-label': 'Type a message' }}
      />
      <Tooltip title="Send message">
        <span>
          <IconButton type="submit" color="primary" sx={{ ml: 1 }} disabled={!input.trim()}>
            <SendIcon />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
}

export default ChatInput;