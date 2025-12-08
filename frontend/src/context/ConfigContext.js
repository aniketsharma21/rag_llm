import React, { createContext, useContext } from 'react';

const ConfigContext = createContext();

export const ConfigProvider = ({ children }) => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const webSocketUrl = process.env.REACT_APP_WS_URL || `${wsProtocol}//${window.location.host}/ws/chat`;

  const config = {
    apiBaseUrl: process.env.REACT_APP_API_BASE_URL || '',
    webSocketUrl,
    jobStatusPollInterval: 2000,
    maxFileSize: 50 * 1024 * 1024,
    supportedFileTypes: ['.pdf', '.docx', '.txt', '.md', '.csv', '.json', '.pptx', '.xlsx'],
  };

  return (
    <ConfigContext.Provider value={config}>
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};