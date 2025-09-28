import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import './App.css';

import { ConfigProvider } from './context/ConfigContext';
import { ConversationStoreProvider } from './context/ConversationStoreContext';
import { WebSocketProvider } from './context/WebSocketContext';

import AppLayout from './routes/AppLayout';
import ChatRoute from './routes/ChatRoute';
import UploadRoute from './routes/UploadRoute';

const AppProviders = ({ children }) => (
  <ConfigProvider>
    <ConversationStoreProvider>
      <WebSocketProvider>{children}</WebSocketProvider>
    </ConversationStoreProvider>
  </ConfigProvider>
);

const App = () => (
  <AppProviders>
    <Router>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<ChatRoute />} />
          <Route path="/upload" element={<UploadRoute />} />
        </Route>
      </Routes>
    </Router>
  </AppProviders>
);

export default App;
