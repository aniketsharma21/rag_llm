import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ChatBubbleLeftIcon, 
  DocumentPlusIcon,
  PlusIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { useConversationStore } from '../context/ConversationStoreContext';

const EnhancedSidebar = () => {
  const { 
    conversations, 
    startNewConversation, 
    selectConversation,
    currentConversationId 
  } = useConversationStore();

  const navItems = [
    { to: '/', icon: ChatBubbleLeftIcon, label: 'Chat' },
    { to: '/upload', icon: DocumentPlusIcon, label: 'Knowledge Base' },
  ];

  return (
    <div className="w-80 h-full flex flex-col bg-gray-50/50 dark:bg-gray-900/50 backdrop-blur-xl border-r border-gray-200 dark:border-gray-800">
      {/* Header */}
      <div className="p-6">
        <div className="flex items-center gap-2 mb-8 px-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center shadow-glow-sm">
            <SparklesIcon className="w-5 h-5 text-white" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight text-gray-900 dark:text-white">
            RAG Assistant
          </span>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={startNewConversation}
          className="w-full group relative flex items-center justify-center gap-2 px-4 py-3.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-primary-500/50 dark:hover:border-primary-500/50 rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-purple-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity" />
          <PlusIcon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <span className="font-medium text-gray-700 dark:text-gray-200 group-hover:text-primary-700 dark:group-hover:text-primary-300">New Chat</span>
        </motion.button>
      </div>

      {/* Navigation */}
      <nav className="px-4 pb-6">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `
                relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                ${isActive 
                  ? 'bg-white dark:bg-gray-800 text-primary-600 dark:text-primary-400 shadow-sm' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-gray-200'
                }
              `}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 custom-scrollbar">
        <div className="mb-3 px-4 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
            Recent Chats
          </h3>
        </div>
        <div className="space-y-1">
          {conversations.map((conversation) => (
            <motion.button
              key={conversation.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              onClick={() => selectConversation(conversation.id)}
              className={`
                group w-full text-left px-4 py-3 rounded-xl text-sm transition-all duration-200 border border-transparent
                ${currentConversationId === conversation.id
                  ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm border-gray-200 dark:border-gray-700'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-gray-200'
                }
              `}
            >
              <div className="truncate font-medium">
                {conversation.title || 'New Conversation'}
              </div>
              <div className="text-xs text-gray-400 mt-1 flex items-center gap-2">
                <span>{new Date(conversation.created_at || Date.now()).toLocaleDateString()}</span>
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* User Profile / Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
            US
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              User Account
            </p>
            <p className="text-xs text-gray-500 truncate">
              Pro Plan
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedSidebar;