import React from 'react';
import { Box, Paper, Typography, IconButton, Tooltip, Link } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import ThumbUpAltOutlinedIcon from '@mui/icons-material/ThumbUpAltOutlined';
import ThumbDownAltOutlinedIcon from '@mui/icons-material/ThumbDownAltOutlined';

function Message({ text, sender, sources = [], onFeedback }) {
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
        {/* Source citations */}
        {sources.length > 0 && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Sources:
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 16 }}>
              {sources.map((src, idx) => (
                <li key={idx}>
                  <Link href={src.url || '#'} target="_blank" rel="noopener noreferrer">
                    {src.title || src.name || 'Source'}
                  </Link>
                  {src.section && ` (Section: ${src.section})`}
                </li>
              ))}
            </ul>
          </Box>
        )}
        {/* Feedback buttons for bot messages */}
        {!isUser && (
          <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
            <Tooltip title="Helpful">
              <IconButton size="small" onClick={() => onFeedback && onFeedback('up')}
                aria-label="Mark as helpful">
                <ThumbUpAltOutlinedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Not helpful">
              <IconButton size="small" onClick={() => onFeedback && onFeedback('down')}
                aria-label="Mark as not helpful">
                <ThumbDownAltOutlinedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Paper>
    </Box>
  );
}

export default Message;