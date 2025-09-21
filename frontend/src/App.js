import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  IconButton,
  CircularProgress,
  TextField,
  Snackbar,
  Alert,
  Button,
  Tooltip,
  Paper,
  styled,
  alpha,
  keyframes,
  CssBaseline,
  AppBar,
  Toolbar,
  Avatar,
  Divider,
  Container,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  InputAdornment,
  useTheme,
  useMediaQuery,
  Drawer,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fade,
  Slide,
  Zoom
} from '@mui/material';
import {
  Send as SendIcon,
  Upload as UploadIcon,
  Stop as StopIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  AttachFile as AttachFileIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
  ErrorOutline as ErrorOutlineIcon
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import MenuIcon from '@mui/icons-material/Menu';
import SettingsIcon from '@mui/icons-material/Settings';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

// Custom styled components
const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const pulse = keyframes`
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
`;

const typingDots = keyframes`
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
`;

const slideInRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

const slideInLeft = keyframes`
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;
const MainContainer = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  backgroundColor: (props) => props.theme.palette.background.default,
});

const ChatContainer = styled(Box)({
  flex: 1,
  overflowY: 'auto',
  padding: '1rem',
  paddingBottom: '120px',
  '&::-webkit-scrollbar': {
    width: '6px',
  },
  '&::-webkit-scrollbar-track': {
    background: (props) => props.theme.palette.mode === 'dark' ? '#2d2d2d' : '#f1f1f1',
  },
  '&::-webkit-scrollbar-thumb': {
    background: (props) => props.theme.palette.mode === 'dark' ? '#555' : '#aaa',
    borderRadius: '10px',
  },
  '&::-webkit-scrollbar-thumb:hover': {
    background: (props) => props.theme.palette.mode === 'dark' ? '#777' : '#888',
  },
});

const WelcomeScreen = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '60vh',
  textAlign: 'center',
  padding: '2rem',
  animation: `${fadeInUp} 0.6s ease-out`,
});

const WelcomeCard = styled(Paper)({
  padding: '3rem',
  borderRadius: '24px',
  background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)',
  border: '1px solid rgba(37, 99, 235, 0.2)',
  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
  maxWidth: '600px',
  width: '100%',
  animation: `${fadeInUp} 0.8s ease-out 0.2s both`,
});

const AnimatedMessageItem = styled(ListItem)(({ sender }) => ({
  animation: sender === 'user' ? `${slideInRight} 0.3s ease-out` : `${slideInLeft} 0.3s ease-out`,
  '& .MuiListItemText-root': {
    animation: `${fadeInUp} 0.4s ease-out 0.1s both`,
  },
  '& .message-bubble': {
    animation: `${fadeInUp} 0.4s ease-out 0.2s both`,
  },
}));

const MessageBubble = styled(Paper)(({ theme, sender }) => ({
  maxWidth: '80%',
  padding: '16px 20px',
  borderRadius: sender === 'user' ? '20px 20px 6px 20px' : '20px 20px 20px 6px',
  marginBottom: '16px',
  wordBreak: 'break-word',
  position: 'relative',
  backgroundColor: sender === 'user'
    ? theme.palette.primary.main
    : theme.palette.mode === 'dark'
      ? theme.palette.grey[800]
      : '#ffffff',
  color: sender === 'user'
    ? '#ffffff'
    : theme.palette.text.primary,
  alignSelf: sender === 'user' ? 'flex-end' : 'flex-start',
  boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
  border: sender === 'bot' ? `1px solid ${theme.palette.mode === 'dark' ? theme.palette.grey[700] : theme.palette.grey[200]}` : 'none',
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12)',
    transform: 'translateY(-1px)',
  },
  '& pre': {
    backgroundColor: sender === 'user'
      ? 'rgba(255, 255, 255, 0.1)'
      : theme.palette.mode === 'dark'
        ? theme.palette.grey[900]
        : theme.palette.grey[100],
    borderRadius: '8px',
    padding: '12px',
    margin: '8px 0',
    overflow: 'auto',
    fontSize: '0.875rem',
    border: `1px solid ${theme.palette.mode === 'dark' ? theme.palette.grey[700] : theme.palette.grey[300]}`,
  },
  '& code': {
    backgroundColor: sender === 'user'
      ? 'rgba(255, 255, 255, 0.15)'
      : theme.palette.mode === 'dark'
        ? theme.palette.grey[700]
        : theme.palette.grey[200],
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '0.85em',
    fontFamily: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  },
  '& p': {
    margin: '8px 0',
    lineHeight: 1.6,
  },
  '& ul, & ol': {
    margin: '8px 0',
    paddingLeft: '20px',
  },
  '& li': {
    margin: '4px 0',
  },
  '& blockquote': {
    borderLeft: `4px solid ${theme.palette.primary.main}`,
    paddingLeft: '16px',
    margin: '16px 0',
    color: theme.palette.text.secondary,
    fontStyle: 'italic',
  },
}));

const InputContainer = styled('form')(({ theme }) => ({
  position: 'fixed',
  bottom: 0,
  left: 0,
  right: 0,
  padding: '16px',
  backgroundColor: theme.palette.background.paper,
  borderTop: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  gap: '12px',
  alignItems: 'center',
  zIndex: 10,
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  flex: 1,
  '& .MuiOutlinedInput-root': {
    borderRadius: '24px',
    backgroundColor: theme.palette.mode === 'dark' ? alpha(theme.palette.grey[800], 0.5) : alpha(theme.palette.grey[100], 0.8),
    '&:hover .MuiOutlineInput-notchedOutline': {
      borderColor: theme.palette.primary.main,
    },
    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
      borderColor: theme.palette.primary.main,
      borderWidth: '1px',
    },
  },
  '& .MuiOutlinedInput-input': {
    padding: '12px 20px',
  },
}));

const SendButton = styled(IconButton)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
  '&:disabled': {
    backgroundColor: theme.palette.action.disabled,
  },
}));

const TypingIndicator = styled('div')({
  display: 'flex',
  gap: '4px',
  padding: '8px 0',
  '& > div': {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: 'currentColor',
    animation: `${pulse} 1.5s infinite`,
    '&:nth-of-type(2)': {
      animationDelay: '0.2s',
    },
    '&:nth-of-type(3)': {
      animationDelay: '0.4s',
    },
  },
});

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
});

// Create a WebSocket connection
const createWebSocket = (url, onOpen, onMessage, onError, onClose) => {
  const ws = new WebSocket(url);

  ws.onopen = () => {
    console.log('WebSocket connected');
    if (onOpen) onOpen();
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    if (onClose) onClose();
  };

  return ws;
};

const drawerWidth = 280;

const themeColors = {
  light: {
    primary: '#2563eb',
    secondary: '#7c3aed',
    background: '#ffffff',
    chatBg: '#f8fafc',
    sidebarBg: '#1f2937',
    sidebarText: '#ffffff',
    border: '#e5e7eb',
    userBubble: '#2563eb',
    botBubble: '#ffffff',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    surface: '#f1f5f9',
    text: '#1e293b',
    textSecondary: '#64748b'
  },
  dark: {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    background: '#0f172a',
    chatBg: '#1e293b',
    sidebarBg: '#1e293b',
    sidebarText: '#f1f5f9',
    border: '#334155',
    userBubble: '#3b82f6',
    botBubble: '#1e293b',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    surface: '#1e293b',
    text: '#f1f5f9',
    textSecondary: '#94a3b8'
  }
};

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: 'Hello! Upload a document and ask me questions about it.',
      sender: 'bot',
      type: 'text'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [file, setFile] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [websocket, setWebsocket] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const messagesEndRef = useRef(null);
  const chatHistoryRef = useRef([]);

  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const colors = isDark ? themeColors.dark : themeColors.light;

  // Initialize WebSocket connection
  useEffect(() => {
    const wsUrl = process.env.REACT_APP_WS_URL || `ws://${window.location.hostname}:8000/ws/chat`;
    const ws = createWebSocket(
      wsUrl,
      () => {
        setIsConnected(true);
        setSnackbar(prev => prev.open && prev.severity === 'error' ? { ...prev, open: false } : prev);
      }, // onOpen
      handleWebSocketMessage,     // onMessage
      handleWebSocketError,       // onError
      () => {
        setIsConnected(false);
        setSnackbar({
          open: true,
          message: 'Connection lost. Please refresh the page.',
          severity: 'error'
        });
      } // onClose
    );
    setWebsocket(ws);

    // Clean up WebSocket on component unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Update chat history ref when messages change
  useEffect(() => {
    chatHistoryRef.current = messages
      .filter(msg => msg.type === 'text')
      .map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text
      }));
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'status':
        // Handle status updates (e.g., processing)
        console.log('Status:', data.status);
        break;

      case 'chunk':
        // Stream response chunks
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];

          if (lastMessage.sender === 'bot' && lastMessage.isStreaming) {
            // Update the last message with new chunk
            return [
              ...prev.slice(0, -1),
              {
                ...lastMessage,
                text: lastMessage.text + data.content,
                isStreaming: true
              }
            ];
          } else {
            // Create a new message for the first chunk
            return [
              ...prev,
              {
                id: Date.now(),
                text: data.content,
                sender: 'bot',
                isStreaming: true,
                type: 'text'
              }
            ];
          }
        });
        break;

      case 'complete':
        // Mark the streaming as complete
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage.sender === 'bot' && lastMessage.isStreaming) {
            return [
              ...prev.slice(0, -1),
              {
                ...lastMessage,
                isStreaming: false,
                sources: data.sources || []
              }
            ];
          }
          return prev;
        });
        setIsLoading(false);
        break;

      case 'error':
        // Handle errors
        setSnackbar({
          open: true,
          message: data.message || 'An error occurred',
          severity: 'error'
        });
        setIsLoading(false);
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }, []);

  const handleWebSocketError = useCallback((error) => {
    console.warn('WebSocket warning:', error);
    setSnackbar({
      open: true,
      message: 'WebSocket warning: Some features may be temporarily unavailable.',
      severity: 'warning'
    });
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || !websocket || isLoading) return;

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      text: input,
      sender: 'user',
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Send message via WebSocket
      websocket.send(JSON.stringify({
        type: 'query',
        question: input,
        chat_history: chatHistoryRef.current
      }));

    } catch (error) {
      console.error('Error sending message:', error);
      setSnackbar({
        open: true,
        message: 'Error sending message. Please try again.',
        severity: 'error'
      });
      setIsLoading(false);
    }
  };

  const handleStopGeneration = () => {
    if (websocket) {
      websocket.send(JSON.stringify({ type: 'stop_generation' }));
      setIsLoading(false);

      // Mark the last message as not streaming
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage.isStreaming) {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              isStreaming: false,
              text: lastMessage.text + '\n\n*Generation stopped by user*'
            }
          ];
        }
        return prev;
      });
    }
    // Mark the last message as not streaming
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1];
      if (lastMessage.isStreaming) {
        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            isStreaming: false
          }
        ];
      }
      return prev;
    });
  };

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    setFile(selectedFile);
    setIsLoading(true);

    try {
      await api.post('/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSnackbar({
        open: true,
        message: `Document "${selectedFile.name}" uploaded and processed successfully!`,
        severity: 'success'
      });
    } catch (error) {
      console.error('Error uploading file:', error);
      setSnackbar({
        open: true,
        message: 'Error uploading document. Please try again.',
        severity: 'error'
      });
    } finally {
      setFile(null);
      setIsLoading(false);
      // Reset file input
      e.target.value = null;
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Render message content with markdown support
  const renderMessageContent = (message) => {
    if (message.type === 'text') {
      return (
        <ReactMarkdown>
          {message.text}
        </ReactMarkdown>
      );
    }
    return null;
  };

  const renderSources = (sources) => {
    if (!sources || sources.length === 0) return null;
    // Deduplicate by source name (after stripping temp_)
    const uniqueSources = Array.from(
      new Set(
        sources.map(source => {
          let name = source?.source || source?.file_name || source?.filename || 'unknown';
          if (name.startsWith('temp_')) name = name.replace(/^temp_/, '');
          return name;
        })
      )
    );
    return (
      <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700, mb: 0.5 }}>
          Sources:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {uniqueSources.map((name, idx) => (
            <Paper
              key={idx}
              elevation={0}
              sx={{
                px: 1.5,
                py: 0.5,
                borderRadius: 2,
                bgcolor: 'grey.100',
                color: 'text.secondary',
                fontSize: 13,
                border: '1px solid',
                borderColor: 'grey.300',
                mr: 1,
                mb: 0.5,
                display: 'inline-block',
                maxWidth: 220,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {name}
            </Paper>
          ))}
        </Box>
      </Box>
    );
  };

  // Sidebar content
  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: colors.sidebarBg, color: colors.sidebarText }}>
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ bgcolor: 'secondary.main', width: 48, height: 48 }}>R</Avatar>
        <Box>
          <Typography variant="h6" fontWeight={700}>RAG LLM</Typography>
          <Typography variant="body2" color="rgba(255,255,255,0.7)">Enterprise Chat</Typography>
        </Box>
      </Box>
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.12)' }} />
      <Box sx={{ flex: 1, p: 2 }}>
        <Button startIcon={<AccountCircleIcon />} fullWidth sx={{ color: colors.sidebarText, justifyContent: 'flex-start', mb: 1 }}>
          User Profile
        </Button>
        <Button startIcon={<SettingsIcon />} fullWidth sx={{ color: colors.sidebarText, justifyContent: 'flex-start', mb: 1 }} onClick={() => setShowSettings(true)}>
          Settings
        </Button>
        <Button startIcon={<HelpOutlineIcon />} fullWidth sx={{ color: colors.sidebarText, justifyContent: 'flex-start' }} onClick={() => setShowHelp(true)}>
          Help
        </Button>
      </Box>
      <Box sx={{ p: 2, textAlign: 'center', fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>
        &copy; {new Date().getFullYear()} RAG LLM
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: colors.background }}>
      {/* Sidebar */}
      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, bgcolor: colors.sidebarBg, color: colors.sidebarText },
          }}
          open
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, bgcolor: colors.sidebarBg, color: colors.sidebarText },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      {/* Main content */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: colors.background }}>
        {/* Header */}
        <AppBar position="static" elevation={0} sx={{
          bgcolor: colors.chatBg,
          color: 'text.primary',
          borderBottom: `1px solid ${colors.border}`,
          backdropFilter: 'blur(10px)',
          backgroundColor: theme.palette.mode === 'dark'
            ? 'rgba(30, 41, 59, 0.8)'
            : 'rgba(255, 255, 255, 0.8)',
          boxShadow: '0 2px 20px rgba(0, 0, 0, 0.08)',
        }}>
          <Toolbar sx={{ minHeight: 64 }}>
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setMobileOpen(true)}
              sx={{
                mr: 2,
                display: { sm: 'none' },
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                }
              }}
            >
              <MenuIcon />
            </IconButton>

            {/* Logo Section */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mr: 3 }}>
              <Avatar sx={{
                width: 40,
                height: 40,
                bgcolor: 'primary.main',
                background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                fontSize: '1.2rem',
                fontWeight: 'bold',
                boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)',
              }}>
                R
              </Avatar>
              <Box sx={{ display: { xs: 'none', md: 'block' } }}>
                <Typography variant="h6" sx={{
                  fontWeight: 700,
                  fontSize: '1.25rem',
                  background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  lineHeight: 1.2
                }}>
                  RAG LLM
                </Typography>
                <Typography variant="caption" sx={{
                  color: 'text.secondary',
                  fontSize: '0.75rem',
                  lineHeight: 1,
                  opacity: 0.8
                }}>
                  Enterprise AI Assistant
                </Typography>
              </Box>
            </Box>

            {/* Status Indicator */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 'auto' }}>
              <Box sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: isConnected ? 'success.main' : 'error.main',
                boxShadow: `0 0 8px ${isConnected ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)'}`,
                animation: isConnected ? `${pulse} 2s infinite` : 'none',
              }} />
              <Typography variant="body2" sx={{
                color: 'text.secondary',
                fontSize: '0.875rem',
                display: { xs: 'none', sm: 'block' }
              }}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </Typography>
            </Box>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip title="Settings">
                <IconButton
                  color="inherit"
                  onClick={() => setShowSettings(true)}
                  sx={{
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                      transform: 'scale(1.05)',
                    },
                    transition: 'all 0.2s ease-in-out',
                  }}
                >
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Help">
                <IconButton
                  color="inherit"
                  onClick={() => setShowHelp(true)}
                  sx={{
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                      transform: 'scale(1.05)',
                    },
                    transition: 'all 0.2s ease-in-out',
                  }}
                >
                  <HelpOutlineIcon />
                </IconButton>
              </Tooltip>
              <Avatar sx={{
                ml: 1,
                bgcolor: 'primary.main',
                background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                width: 36,
                height: 36,
                fontSize: '0.9rem',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(37, 99, 235, 0.3)',
                '&:hover': {
                  transform: 'scale(1.05)',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.4)',
                },
                transition: 'all 0.2s ease-in-out',
              }}>
                U
              </Avatar>
            </Box>
          </Toolbar>
        </AppBar>
        {/* Chat area */}
        <ChatContainer sx={{ flex: 1, minHeight: 0, maxHeight: '100%', p: { xs: 1, sm: 3 }, bgcolor: colors.background, display: 'flex', flexDirection: 'column', justifyContent: messages.length <= 1 ? 'center' : 'flex-end' }}>
          <Container maxWidth="md" sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: messages.length <= 1 ? 'center' : 'flex-end', minHeight: 0, p: 0 }}>
            {messages.length <= 1 ? (
              <WelcomeScreen>
                <WelcomeCard elevation={0}>
                  <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main', mb: 3, mx: 'auto' }}>
                    <Typography variant="h2" sx={{ color: 'white', fontWeight: 'bold' }}>R</Typography>
                  </Avatar>
                  <Typography variant="h3" sx={{ mb: 2, fontWeight: 700, background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    Welcome to RAG LLM Chat
                  </Typography>
                  <Typography variant="h6" sx={{ mb: 3, color: 'text.secondary', fontWeight: 400 }}>
                    Your intelligent document assistant powered by advanced AI
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: 'rgba(37, 99, 235, 0.05)', borderRadius: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}>📄</Avatar>
                      <Box sx={{ textAlign: 'left' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Upload Documents</Typography>
                        <Typography variant="body2" sx={{ color: 'text.secondary' }}>Upload PDFs, DOCX, or TXT files to get started</Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: 'rgba(124, 58, 237, 0.05)', borderRadius: 2 }}>
                      <Avatar sx={{ bgcolor: 'secondary.main', width: 40, height: 40 }}>💬</Avatar>
                      <Box sx={{ textAlign: 'left' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Ask Questions</Typography>
                        <Typography variant="body2" sx={{ color: 'text.secondary' }}>Get instant answers about your documents</Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: 'rgba(34, 197, 94, 0.05)', borderRadius: 2 }}>
                      <Avatar sx={{ bgcolor: 'success.main', width: 40, height: 40 }}>🚀</Avatar>
                      <Box sx={{ textAlign: 'left' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Powered by AI</Typography>
                        <Typography variant="body2" sx={{ color: 'text.secondary' }}>Advanced RAG technology for accurate responses</Typography>
                      </Box>
                    </Box>
                  </Box>
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<AttachFileIcon />}
                    onClick={() => document.getElementById('upload-document')?.click()}
                    sx={{
                      py: 1.5,
                      px: 4,
                      borderRadius: '12px',
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                      boxShadow: '0 4px 16px rgba(37, 99, 235, 0.3)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #1d4ed8 0%, #6d28d9 100%)',
                        boxShadow: '0 6px 24px rgba(37, 99, 235, 0.4)',
                        transform: 'translateY(-2px)',
                      },
                      transition: 'all 0.2s ease-in-out',
                    }}
                  >
                    Upload Your First Document
                  </Button>
                  <input
                    accept=".pdf,.docx,.txt"
                    style={{ display: 'none' }}
                    id="welcome-upload"
                    type="file"
                    onChange={handleFileUpload}
                  />
                </WelcomeCard>
              </WelcomeScreen>
            ) : (
              <List sx={{ width: '100%', bgcolor: 'transparent', flex: 1, minHeight: 0, overflow: 'visible' }}>
                {messages.map((message, index) => (
                  <AnimatedMessageItem key={message.id} sender={message.sender} alignItems="flex-start" sx={{
                    flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                    textAlign: message.sender === 'user' ? 'right' : 'left',
                    border: 'none',
                    background: 'none',
                    mb: 1,
                    animationDelay: `${index * 0.1}s`
                  }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: message.sender === 'user' ? 'primary.main' : 'secondary.main', width: 40, height: 40 }}>
                        {message.sender === 'user' ? 'U' : 'A'}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <MessageBubble
                          className="message-bubble"
                          sender={message.sender}
                          elevation={0}
                          sx={{
                            p: 2,
                            borderRadius: message.sender === 'user' ? '20px 20px 6px 20px' : '20px 20px 20px 6px',
                            backgroundColor: message.sender === 'user'
                              ? theme.palette.primary.main
                              : theme.palette.mode === 'dark'
                                ? theme.palette.grey[800]
                                : '#ffffff',
                            color: message.sender === 'user' ? '#ffffff' : theme.palette.text.primary,
                            boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
                            border: message.sender === 'bot' ? `1px solid ${theme.palette.mode === 'dark' ? theme.palette.grey[700] : theme.palette.grey[200]}` : 'none',
                            fontSize: '1rem',
                            position: 'relative',
                            minWidth: 80,
                            maxWidth: { xs: '90vw', sm: '70%' },
                            wordBreak: 'break-word',
                            mb: 0.5,
                            transition: 'all 0.2s ease-in-out',
                            '&:hover': {
                              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12)',
                              transform: 'translateY(-1px)',
                            },
                          }}
                        >
                          {renderMessageContent(message)}
                          {message.isStreaming && (
                            <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1, mt: 1 }}>
                              <Box sx={{
                                display: 'flex',
                                gap: 0.5,
                                '& > div': {
                                  width: 4,
                                  height: 4,
                                  borderRadius: '50%',
                                  backgroundColor: 'text.secondary',
                                  animation: `${typingDots} 1.4s infinite ease-in-out`,
                                },
                                '& > div:nth-of-type(1)': { animationDelay: '-0.32s' },
                                '& > div:nth-of-type(2)': { animationDelay: '-0.16s' },
                              }}>
                                <div></div>
                                <div></div>
                                <div></div>
                              </Box>
                            </Box>
                          )}
                          {message.sender === 'bot' && message.sources && message.sources.length > 0 && renderSources(message.sources)}
                        </MessageBubble>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', animation: `${fadeInUp} 0.3s ease-out 0.3s both` }}>
                          {new Date(message.id).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </Typography>
                      }
                    />
                  </AnimatedMessageItem>
                ))}
                <div ref={messagesEndRef} />
              </List>
            )}
          </Container>
        </ChatContainer>
        {/* Input bar */}
        <Box component="form" onSubmit={handleSendMessage} sx={{
          p: { xs: 2, sm: 3 },
          bgcolor: colors.chatBg,
          borderTop: `1px solid ${colors.border}`,
          display: 'flex',
          alignItems: 'flex-end',
          position: 'sticky',
          bottom: 0,
          zIndex: 10,
          backdropFilter: 'blur(10px)',
          backgroundColor: theme.palette.mode === 'dark'
            ? 'rgba(30, 41, 59, 0.9)'
            : 'rgba(255, 255, 255, 0.9)',
        }}>
          <Container maxWidth="md" sx={{ display: 'flex', alignItems: 'flex-end', gap: 2, p: 0 }}>
            {/* File Upload Button */}
            <Tooltip title="Upload document">
              <IconButton
                component="label"
                disabled={isLoading || !isConnected}
                sx={{
                  minWidth: 48,
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  bgcolor: 'rgba(0, 0, 0, 0.04)',
                  color: 'text.secondary',
                  '&:hover': {
                    bgcolor: 'rgba(0, 0, 0, 0.08)',
                    transform: 'scale(1.05)',
                  },
                  '&:disabled': {
                    opacity: 0.5,
                  },
                  transition: 'all 0.2s ease-in-out',
                  flexShrink: 0,
                }}
              >
                <AttachFileIcon />
                <input
                  accept=".pdf,.docx,.txt"
                  style={{ display: 'none' }}
                  id="upload-document"
                  type="file"
                  onChange={handleFileUpload}
                  disabled={isLoading || !isConnected}
                />
              </IconButton>
            </Tooltip>

            {/* Text Input */}
            <TextField
              fullWidth
              variant="outlined"
              placeholder={
                !isConnected
                  ? "Connecting to server..."
                  : isLoading
                    ? "AI is thinking..."
                    : "Ask me anything about your documents..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading || !isConnected}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
              multiline
              maxRows={5}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '24px',
                  backgroundColor: theme.palette.mode === 'dark'
                    ? 'rgba(51, 65, 85, 0.5)'
                    : 'rgba(241, 245, 249, 0.8)',
                  border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(148, 163, 184, 0.2)' : 'rgba(0, 0, 0, 0.08)'}`,
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    backgroundColor: theme.palette.mode === 'dark'
                      ? 'rgba(51, 65, 85, 0.7)'
                      : 'rgba(241, 245, 249, 0.9)',
                    borderColor: theme.palette.primary.main,
                  },
                  '&.Mui-focused': {
                    backgroundColor: theme.palette.mode === 'dark'
                      ? 'rgba(51, 65, 85, 0.8)'
                      : 'rgba(255, 255, 255, 0.95)',
                    borderColor: theme.palette.primary.main,
                    boxShadow: `0 0 0 3px ${theme.palette.primary.main}25`,
                  },
                  '& .MuiOutlinedInput-input': {
                    padding: '16px 20px',
                    fontSize: '1rem',
                    lineHeight: 1.5,
                    '&::placeholder': {
                      color: 'text.secondary',
                      opacity: 0.7,
                    },
                  },
                  '& .MuiOutlinedInput-notchedOutline': {
                    border: 'none',
                  },
                },
              }}
              InputProps={{
                endAdornment: input.trim() && !isLoading ? (
                  <InputAdornment position="end">
                    <Tooltip title="Send message (Enter)">
                      <IconButton
                        type="submit"
                        disabled={!input.trim() || isLoading || !isConnected}
                        sx={{
                          bgcolor: 'primary.main',
                          color: 'white',
                          width: 36,
                          height: 36,
                          '&:hover': {
                            bgcolor: 'primary.dark',
                            transform: 'scale(1.1)',
                          },
                          '&:disabled': {
                            bgcolor: 'action.disabledBackground',
                            color: 'action.disabled',
                          },
                          transition: 'all 0.2s ease-in-out',
                        }}
                      >
                        <SendIcon sx={{ fontSize: 18 }} />
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                ) : null,
              }}
            />

            {/* Send Button (when no text) */}
            {!input.trim() && (
              <Tooltip title={isLoading ? "Stop generation" : "Send message"}>
                <span>
                  <IconButton
                    type="submit"
                    disabled={!input.trim() && !isLoading || !isConnected}
                    sx={{
                      minWidth: 48,
                      width: 48,
                      height: 48,
                      borderRadius: '12px',
                      bgcolor: isLoading ? 'error.main' : 'primary.main',
                      color: 'white',
                      '&:hover': {
                        bgcolor: isLoading ? 'error.dark' : 'primary.dark',
                        transform: 'scale(1.05)',
                      },
                      '&:disabled': {
                        bgcolor: 'action.disabledBackground',
                        color: 'action.disabled',
                      },
                      transition: 'all 0.2s ease-in-out',
                      flexShrink: 0,
                    }}
                  >
                    {isLoading ? <StopIcon /> : <SendIcon />}
                  </IconButton>
                </span>
              </Tooltip>
            )}
          </Container>
        </Box>
        {/* Settings Modal */}
        <Dialog open={showSettings} onClose={() => setShowSettings(false)}>
          <DialogTitle>Settings</DialogTitle>
          <DialogContent>
            <Typography variant="body2">Settings panel coming soon.</Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowSettings(false)}>Close</Button>
          </DialogActions>
        </Dialog>
        {/* Help Modal */}
        <Dialog open={showHelp} onClose={() => setShowHelp(false)}>
          <DialogTitle>Help</DialogTitle>
          <DialogContent>
            <Typography variant="body2">This is an enterprise RAG LLM chat. Upload a document and ask questions about its content. For more help, contact your admin.</Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowHelp(false)}>Close</Button>
          </DialogActions>
        </Dialog>
        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Box>
  );
}

export default App;

