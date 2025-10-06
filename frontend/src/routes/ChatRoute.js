import React from 'react';

import ChatWindow from '../components/ChatWindow';
import EnhancedChatInput from '../components/EnhancedChatInput';
import PageContainer from '../components/ui/PageContainer';

const ChatRoute = () => (
  <PageContainer className="flex flex-col overflow-hidden">
    <div className="flex flex-col h-full">
      <ChatWindow />
      <EnhancedChatInput />
    </div>
  </PageContainer>
);

export default ChatRoute;
