import React, { createContext, useContext, useMemo } from 'react';
import { createClientConfig } from '../config/clientConfig';

const ConfigContext = createContext(null);

export const ConfigProvider = ({ children }) => {
  const value = useMemo(() => createClientConfig(), []);
  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
};

export const useConfig = () => {
  const ctx = useContext(ConfigContext);
  if (!ctx) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return ctx;
};

export default ConfigContext;
