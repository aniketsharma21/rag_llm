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
  DialogActions
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

const MessageBubble = styled(Paper)(({ theme, sender }) => ({
  maxWidth: '80%',
  padding: '12px 16px',
  borderRadius: '18px',
  marginBottom: '12px',
  wordBreak: 'break-word',
  position: 'relative',
  backgroundColor: sender === 'user' 
    ? theme.palette.mode === 'dark' 
      ? theme.palette.primary.dark 
      : theme.palette.primary.light
    : theme.palette.mode === 'dark'
      ? alpha(theme.palette.grey[800], 0.8)
      : alpha(theme.palette.grey[100], 0.8),
  color: sender === 'user' 
    ? theme.palette.primary.contrastText 
    : theme.palette.text.primary,
  alignSelf: sender === 'user' ? 'flex-end' : 'flex-start',
  boxShadow: theme.shadows[1],
  '& pre': {
    backgroundColor: theme.palette.mode === 'dark' ? '#2d2d2d' : '#f5f5f5',
    padding: '12px',
    borderRadius: '8px',
    overflowX: 'auto',
  },
  '& code': {
    fontFamily: 'Roboto Mono, monospace',
    fontSize: '0.9em',
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

const pulse = keyframes`
  0% { opacity: 0.2; }
  50% { opacity: 1; }
  100% { opacity: 0.2; }
`;

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
    background: '#f4f6fb',
    chatBg: '#ffffff',
    sidebarBg: '#1a237e',
    sidebarText: '#fff',
    userBubble: '#e3f2fd',
    botBubble: '#f5f5f5',
    border: '#e0e0e0',
  },
  dark: {
    background: '#181a20',
    chatBg: '#23272f',
    sidebarBg: '#11143a',
    sidebarText: '#fff',
    userBubble: '#223a5f',
    botBubble: '#23272f',
    border: '#23272f',
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
        <AppBar position="static" elevation={0} sx={{ bgcolor: colors.chatBg, color: 'text.primary', borderBottom: `1px solid ${colors.border}` }}>
          <Toolbar>
            <IconButton color="inherit" edge="start" onClick={() => setMobileOpen(true)} sx={{ mr: 2, display: { sm: 'none' } }}>
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>RAG LLM Chat</Typography>
            <Tooltip title="Settings"><IconButton color="inherit" onClick={() => setShowSettings(true)}><SettingsIcon /></IconButton></Tooltip>
            <Tooltip title="Help"><IconButton color="inherit" onClick={() => setShowHelp(true)}><HelpOutlineIcon /></IconButton></Tooltip>
            <Avatar sx={{ ml: 2, bgcolor: 'primary.main' }}>U</Avatar>
          </Toolbar>
        </AppBar>
        {/* Chat area */}
        <ChatContainer sx={{ flex: 1, minHeight: 0, maxHeight: '100%', p: { xs: 1, sm: 3 }, bgcolor: colors.background, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
          <Container maxWidth="md" sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', minHeight: 0, p: 0 }}>
            <List sx={{ width: '100%', bgcolor: 'transparent', flex: 1, minHeight: 0, overflow: 'visible' }}>
              {messages.map((message) => (
                <ListItem key={message.id} alignItems="flex-start" sx={{
                  flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                  textAlign: message.sender === 'user' ? 'right' : 'left',
                  border: 'none',
                  background: 'none',
                  mb: 1
                }}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: message.sender === 'user' ? 'primary.main' : 'secondary.main', width: 40, height: 40 }}>
                      {message.sender === 'user' ? 'U' : 'A'}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Paper elevation={2} sx={{
                        p: 2,
                        borderRadius: message.sender === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                        backgroundColor: message.sender === 'user' ? colors.userBubble : colors.botBubble,
                        color: 'text.primary',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                        fontSize: '1.08rem',
                        position: 'relative',
                        minWidth: 80,
                        maxWidth: { xs: '90vw', sm: '70%' },
                        wordBreak: 'break-word',
                        mb: 0.5
                      }}>
                        {renderMessageContent(message)}
                        {message.isStreaming && (
                          <Box component="span" sx={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: 'text.secondary', ml: 1, animation: 'pulse 1.5s infinite' }} />
                        )}
                        {message.sender === 'bot' && message.sources && message.sources.length > 0 && renderSources(message.sources)}
                      </Paper>
                    }
                    secondary={
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        {new Date(message.id).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
              <div ref={messagesEndRef} />
            </List>
          </Container>
        </ChatContainer>
        {/* Input bar */}
        <Box component="form" onSubmit={handleSendMessage} sx={{
          p: { xs: 1, sm: 2 },
          bgcolor: colors.chatBg,
          borderTop: `1px solid ${colors.border}`,
          display: 'flex',
          alignItems: 'center',
          position: 'sticky',
          bottom: 0,
          zIndex: 10
        }}>
          <Container maxWidth="md" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder={!isConnected ? "Connecting to server..." : "Type your question..."}
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
              maxRows={4}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '28px',
                  backgroundColor: isDark ? 'rgba(40,40,50,0.7)' : 'rgba(240,240,255,0.7)',
                },
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <label htmlFor="upload-document">
                      <IconButton component="span" disabled={isLoading || !isConnected}>
                        <AttachFileIcon />
                      </IconButton>
                    </label>
                    <input
                      accept=".pdf,.docx,.txt"
                      style={{ display: 'none' }}
                      id="upload-document"
                      type="file"
                      onChange={handleFileUpload}
                      disabled={isLoading || !isConnected}
                    />
                  </InputAdornment>
                )
              }}
            />
            {isLoading ? (
              <Button
                variant="contained"
                color="error"
                onClick={handleStopGeneration}
                sx={{ minWidth: 48, width: 48, height: 48, borderRadius: '50%' }}
              >
                <StopIcon />
              </Button>
            ) : (
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={!input.trim() || isLoading || !isConnected}
                sx={{ minWidth: 48, width: 48, height: 48, borderRadius: '50%' }}
              >
                <SendIcon />
              </Button>
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

