import React from 'react';
import { Outlet } from 'react-router-dom';

import EnhancedSidebar from '../components/EnhancedSidebar';
import EnhancedHeader from '../components/EnhancedHeader';
import SettingsPanel from '../components/SettingsPanel';
import { useConversationStore } from '../context/ConversationStoreContext';

const AppLayout = () => {
  const {
    isSettingsOpen,
    closeSettings,
    settings,
    saveSettings,
    connectionNotice,
  } = useConversationStore();

  return (
    <div className="bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark font-display flex h-screen">
      <EnhancedSidebar />
      <div className="flex-1 flex flex-col max-w-full overflow-hidden">
        {connectionNotice && (
          <div className="bg-amber-100 dark:bg-amber-900/40 text-amber-900 dark:text-amber-200 px-4 py-2 text-sm font-medium shadow-sm">
            {connectionNotice}
          </div>
        )}
        <EnhancedHeader />
        <Outlet />
      </div>
      <SettingsPanel
        open={isSettingsOpen}
        onClose={closeSettings}
        settings={settings}
        onSave={saveSettings}
      />
    </div>
  );
};

export default AppLayout;
