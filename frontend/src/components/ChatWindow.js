import React, { useState } from 'react';
import { Box, Button, Typography, Divider, Tooltip } from '@mui/material';
import Message from './Message';
import DownloadIcon from '@mui/icons-material/Download';

function exportChat(messages, format = 'csv') {
  if (format === 'csv') {
    const csv = messages.map(m => `"${m.sender}","${m.text.replace(/"/g, '""')}"`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chat_history.csv';
    a.click();
    URL.revokeObjectURL(url);
  } else if (format === 'txt') {
    const txt = messages.map(m => `${m.sender}: ${m.text}`).join('\n');
    const blob = new Blob([txt], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chat_history.txt';
    a.click();
    URL.revokeObjectURL(url);
  }
}

function ChatWindow({ messages, isLoading, sessions = [], currentSessionId, onFeedback }) {
  const [visibleCount, setVisibleCount] = useState(20);
  const handleLoadMore = () => setVisibleCount((c) => c + 20);

  // Group messages by session if sessions provided, else show all
  const grouped = sessions.length > 0
    ? sessions.map(session => ({
        ...session,
        messages: messages.filter(m => m.sessionId === session.id)
      }))
    : [{ id: 'default', title: 'Current Chat', messages }];

  return (
    <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 3 }} role="log" aria-label="Chat messages">
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Tooltip title="Export chat as CSV">
          <span>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => exportChat(messages, 'csv')}
              size="small"
              aria-label="Export chat"
            >
              Export Chat
            </Button>
          </span>
        </Tooltip>
      </Box>
      {grouped.map((group, idx) => (
        <Box key={group.id} sx={{ mb: 4 }}>
          {sessions.length > 0 && (
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              {group.title || `Session ${idx + 1}`}
            </Typography>
          )}
          {/* Pagination: show only the last visibleCount messages */}
          {group.messages.length > visibleCount && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <Button onClick={handleLoadMore} size="small" variant="text" aria-label="Load more messages">
                Load More
              </Button>
            </Box>
          )}
          {group.messages.slice(-visibleCount).map((msg, i) => (
            <Message key={i} {...msg} />
          ))}
          {idx < grouped.length - 1 && <Divider sx={{ my: 2 }} />}
        </Box>
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