import React from 'react';
import { Outlet } from 'react-router-dom';

import EnhancedSidebar from '../components/EnhancedSidebar';
import EnhancedHeader from '../components/EnhancedHeader';
import SettingsPanel from '../components/SettingsPanel';
import { useConversationStore } from '../context/ConversationStoreContext';

const AppLayout = () => {
  const { isSettingsOpen, closeSettings, settings, saveSettings } = useConversationStore();

  return (
    <div className="bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark font-display flex h-screen">
      <EnhancedSidebar />
      <div className="flex-1 flex flex-col max-w-full overflow-hidden">
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
