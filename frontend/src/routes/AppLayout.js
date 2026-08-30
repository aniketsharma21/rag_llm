import React from 'react';
import { Outlet } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import EnhancedSidebar from '../components/EnhancedSidebar';
import EnhancedHeader from '../components/EnhancedHeader';
import { useConversationStore } from '../context/ConversationStoreContext';

const AppLayout = () => {
  const { connectionNotice } = useConversationStore();

  return (
    <div className="flex h-screen bg-white dark:bg-[#212121] text-gray-900 dark:text-gray-100 overflow-hidden font-sans">
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
              className="absolute top-0 left-0 right-0 z-50 flex justify-center pt-3 pointer-events-none"
            >
              <div className="bg-white dark:bg-neutral-800 border border-amber-200 dark:border-amber-800 px-4 py-2 rounded-xl shadow-sm pointer-events-auto">
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
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
