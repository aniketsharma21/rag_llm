import React from 'react';
import { Outlet } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import EnhancedSidebar from '../components/EnhancedSidebar';
import EnhancedHeader from '../components/EnhancedHeader';
import { useConversationStore } from '../context/ConversationStoreContext';

const AppLayout = () => {
  const { connectionNotice } = useConversationStore();

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 overflow-hidden font-sans">
      {/* EnhancedSidebar */}
      <EnhancedSidebar />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col relative min-w-0">
        {/* Connection Notice */}
        <AnimatePresence>
          {connectionNotice && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="absolute top-0 left-0 right-0 z-50 flex justify-center pt-4 pointer-events-none"
            >
              <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 px-4 py-2 rounded-full shadow-lg backdrop-blur-md pointer-events-auto">
                <p className="text-sm text-amber-800 dark:text-amber-200 font-medium flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  {connectionNotice}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* EnhancedHeader */}
        <EnhancedHeader />
        
        {/* Page Content */}
        <main className="flex-1 overflow-hidden relative">
          <div className="absolute inset-0 bg-grid-slate-200/50 dark:bg-grid-slate-800/50 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] pointer-events-none" />
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;