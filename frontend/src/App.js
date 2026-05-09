import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';

import './App.css';

import { ConfigProvider } from './context/ConfigContext';
import { ConversationStoreProvider } from './context/ConversationStoreContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { ThemeProvider } from './context/ThemeContext';

import AppLayout from './routes/AppLayout';
import ChatRoute from './routes/ChatRoute';
import UploadRoute from './routes/UploadRoute';

const AppProviders = ({ children }) => (
  <ThemeProvider>
    <ConfigProvider>
      <ConversationStoreProvider>
        <WebSocketProvider>
          {children}
        </WebSocketProvider>
      </ConversationStoreProvider>
    </ConfigProvider>
  </ThemeProvider>
);

const App = () => {
  return (
    <AppProviders>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50/20 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <Router>
          <AnimatePresence mode="wait">
            <Routes>
              <Route element={<AppLayout />}>
                <Route path="/" element={<ChatRoute />} />
                <Route path="/chat/:conversationId?" element={<ChatRoute />} />
                <Route path="/upload" element={<UploadRoute />} />
              </Route>
            </Routes>
          </AnimatePresence>
        </Router>
        
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'var(--chat-surface)',
              color: 'var(--chat-text)',
              border: '1px solid var(--chat-border)',
              borderRadius: '12px',
              padding: '16px',
              fontSize: '14px',
              fontWeight: '500',
              boxShadow: 'var(--chat-shadow)',
            },
          }}
        />
      </div>
    </AppProviders>
  );
};

export default App;
