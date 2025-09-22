import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import ReactMarkdown from 'react-markdown';

function Message({ text, sender }) {
  const isUser = sender === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 2,
          bgcolor: isUser ? 'primary.main' : 'background.paper',
          color: isUser ? 'primary.contrastText' : 'text.primary',
          maxWidth: '80%',
          borderRadius: isUser ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
        }}
      >
        <Typography component="div">
          <ReactMarkdown>{text}</ReactMarkdown>
        </Typography>
      </Paper>
    </Box>
  );
}

export default Message;