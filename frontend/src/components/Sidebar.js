import React, { useState } from 'react';
import { Box, Button, List, ListItem, ListItemText, Typography, Divider, TextField, ListItemIcon } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import ChatIcon from '@mui/icons-material/Chat';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SettingsIcon from '@mui/icons-material/Settings';

function Sidebar({ conversations, onNewConversation, onSelectConversation }) {
  const [search, setSearch] = useState('');
  const location = useLocation();
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
      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Button variant="outlined" fullWidth onClick={onNewConversation}>
          + New Chat
        </Button>
        <Button
          component={Link}
          to="/"
          startIcon={<ChatIcon />}
          color={location.pathname === '/' ? 'primary' : 'inherit'}
          variant={location.pathname === '/' ? 'contained' : 'text'}
        >
          Chat
        </Button>
        <Button
          component={Link}
          to="/upload"
          startIcon={<CloudUploadIcon />}
          color={location.pathname === '/upload' ? 'primary' : 'inherit'}
          variant={location.pathname === '/upload' ? 'contained' : 'text'}
        >
          Upload
        </Button>
        <Button
          component={Link}
          to="/settings"
          startIcon={<SettingsIcon />}
          color={location.pathname === '/settings' ? 'primary' : 'inherit'}
          variant={location.pathname === '/settings' ? 'contained' : 'text'}
        >
          Settings
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