import React, { Suspense, lazy } from 'react';

import PageContainer from '../components/ui/PageContainer';

const ChatWindow = lazy(() => import('../components/ChatWindow'));
const EnhancedChatInput = lazy(() => import('../components/EnhancedChatInput'));

const LoadingState = () => (
  <div className="flex flex-col items-center justify-center py-12 text-center text-sm text-gray-500 dark:text-gray-400">
    <div className="animate-pulse rounded-full h-12 w-12 bg-gray-200 dark:bg-gray-700 mb-4" />
    Loading conversation workspace…
  </div>
);

const ChatRoute = () => (
  <PageContainer className="flex flex-col overflow-hidden">
    <div className="flex flex-col h-full">
      <Suspense fallback={<LoadingState />}>
        <ChatWindow />
      </Suspense>
      <Suspense fallback={<LoadingState />}>
        <EnhancedChatInput />
      </Suspense>
    </div>
  </PageContainer>
);

export default ChatRoute;
