import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChatBubbleLeftIcon, DocumentPlusIcon, MagnifyingGlassIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useConversationStore } from '../context/ConversationStoreContext';

const EnhancedSidebar = () => {
  const { 
    conversations,
    filteredConversations,
    isConversationsLoading,
    searchQuery,
    setSearchQuery,
    startNewConversation, 
    selectConversation,
    currentConversationId,
    deleteConversation,
  } = useConversationStore();

  const navItems = [
    { to: '/', icon: ChatBubbleLeftIcon, label: 'Chat' },
    { to: '/upload', icon: DocumentPlusIcon, label: 'Knowledge Base' },
  ];

  return (
    <aside className="w-[260px] h-full flex flex-col bg-[#f9f9f9] dark:bg-[#171717] border-r border-gray-200 dark:border-neutral-800">
      {/* Header */}
      <div className="p-3">
        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={startNewConversation}
          className="w-full flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-neutral-700 rounded-xl hover:bg-gray-100 dark:hover:bg-neutral-800 transition-colors duration-150"
        >
          <PlusIcon className="w-4 h-4" />
          <span>New chat</span>
        </motion.button>
      </div>

      {/* Navigation */}
      <nav className="px-3 pb-3">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `
                relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150
                ${isActive 
                  ? 'bg-gray-200/70 dark:bg-neutral-800 text-gray-950 dark:text-gray-100' 
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 hover:text-gray-950 dark:hover:text-gray-100'
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
      <div className="flex-1 overflow-y-auto px-3 pb-4 custom-scrollbar">
        <div className="mb-2 px-3 flex items-center justify-between">
          <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400">
            Chats
          </h3>
        </div>
        <div className="relative mb-3">
          <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search chats"
            className="w-full rounded-lg border border-transparent bg-white py-2 pl-9 pr-3 text-sm text-gray-900 outline-none transition-colors placeholder:text-gray-400 focus:border-gray-300 dark:bg-neutral-900 dark:text-gray-100 dark:focus:border-neutral-700"
          />
        </div>
        <div className="space-y-1">
          {isConversationsLoading && conversations.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Loading chats...</div>
          ) : null}
          {!isConversationsLoading && filteredConversations.length === 0 ? (
            <div className="px-3 py-6 text-sm text-gray-500 dark:text-gray-400">
              {searchQuery ? 'No chats match your search.' : 'No saved chats yet.'}
            </div>
          ) : null}
          {filteredConversations.map((conversation) => (
            <motion.div
              key={conversation.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`
                group flex w-full items-center gap-1 rounded-lg text-sm transition-colors duration-150
                ${currentConversationId === conversation.id
                  ? 'bg-gray-200/70 dark:bg-neutral-800 text-gray-950 dark:text-gray-100'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 hover:text-gray-950 dark:hover:text-gray-100'
                }
              `}
            >
              <button onClick={() => selectConversation(conversation.id)} className="min-w-0 flex-1 px-3 py-2.5 text-left">
                <div className="truncate font-medium">{conversation.title || 'New Conversation'}</div>
              </button>
              <button
                type="button"
                aria-label={`Delete ${conversation.title || 'conversation'}`}
                onClick={(event) => {
                  event.stopPropagation();
                  deleteConversation(conversation.id).catch(() => {});
                }}
                className="mr-2 rounded p-1 text-gray-400 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 dark:hover:bg-red-950/30"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* User Profile / Footer */}
      <div className="p-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-gray-100 dark:hover:bg-neutral-800 transition-colors">
          <div className="w-7 h-7 rounded-full bg-emerald-600 flex items-center justify-center text-white text-xs font-semibold">
            U
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              Local workspace
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default EnhancedSidebar;
