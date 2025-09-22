import React from 'react';
import { Box, Button, List, ListItem, ListItemText, Typography, Divider } from '@mui/material';

function Sidebar({ conversations, onNewConversation, onSelectConversation }) {
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
      <Divider />
      <List sx={{ flexGrow: 1, overflowY: 'auto' }}>
        {conversations.map((conv) => (
          <ListItem button key={conv.id} onClick={() => onSelectConversation(conv.id)}>
            <ListItemText primary={conv.title} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

export default Sidebar;