import React, { createContext, useContext } from 'react';

import { createClientConfig } from '../config/clientConfig';

const ConfigContext = createContext();

export const ConfigProvider = ({ children }) => {
  const config = {
    ...createClientConfig(),
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
