import React, { useState } from 'react';
import { Box, Button, List, ListItem, ListItemText, Typography, Divider, TextField } from '@mui/material';

function Sidebar({ conversations, onNewConversation, onSelectConversation }) {
  const [search, setSearch] = useState('');
  const filtered = conversations.filter(conv =>
    conv.title.toLowerCase().includes(search.toLowerCase())
  );
  return (
    <Box
      sx={{
        width: 260,
        flexShrink: 0,
        bgcolor: 'background.paper',
        borderRight: '1px solid',
        borderColor: 'divider',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box sx={{ p: 2 }}>
        <Button variant="outlined" fullWidth onClick={onNewConversation}>
          + New Chat
        </Button>
      </Box>
      <Box sx={{ px: 2, pb: 1 }}>
        <TextField
          size="small"
          fullWidth
          placeholder="Search chats..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          variant="outlined"
        />
      </Box>
      <Divider />
      <List sx={{ flexGrow: 1, overflowY: 'auto' }}>
        {filtered.length === 0 && <ListItem><ListItemText primary="No chats found." /></ListItem>}
        {filtered.map((conv) => (
          <ListItem component="button" key={conv.id} onClick={() => onSelectConversation(conv.id)}>
            <ListItemText primary={conv.title} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

export default Sidebar;