import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { useConversationStore } from '../context/ConversationStoreContext';
import Button from './ui/Button';
import Card, { CardContent } from './ui/Card';
import Badge from './ui/Badge';

/**
 * Enhanced Sidebar component with search functionality moved above chat history
 * - Search input above conversation history
 * - Improved visual hierarchy
 * - Better responsive design
 */
const EnhancedSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const {
    theme,
    toggleTheme,
    filteredConversations,
    startNewConversation,
    selectConversation,
    currentConversationId,
    openSettings,
    searchQuery,
    setSearchQuery,
  } = useConversationStore();

  const handleNewConversation = () => {
    startNewConversation();
    navigate('/');
  };

  const handleSelectConversation = (conversationId) => {
    selectConversation(conversationId);
    navigate('/');
  };

  return (
    <aside className="bg-surface-light dark:bg-surface-dark w-64 p-4 flex flex-col justify-between hidden md:flex transition-all duration-300 border-r border-gray-200 dark:border-gray-700">
      {/* Top section: Title and main navigation */}
      <div className="flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">AI Assistant</h1>
        </div>
        
        <nav className="mb-4 space-y-2">
          <Button
            variant={location.pathname === '/' ? 'primary' : 'secondary'}
            className="w-full justify-start gap-3"
            onClick={handleNewConversation}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>New Chat</span>
          </Button>

          <Button
            as={Link}
            to="/upload"
            variant={location.pathname === '/upload' ? 'primary' : 'secondary'}
            className="w-full justify-start gap-3"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>Upload Documents</span>
          </Button>
        </nav>

        <hr className="my-4 border-gray-200 dark:border-gray-700" />

        {/* Search Section - moved above chat history */}
        <Card className="mb-4">
          <CardContent className="p-3">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                className={`w-full pl-10 pr-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  isSearchFocused ? 'bg-white dark:bg-gray-700' : ''
                }`}
              />
            </div>
          </CardContent>
        </Card>

        {/* Conversation History Section */}
        <div className="flex-1 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-400">
              Chat History
            </h2>
            {searchQuery && (
              <Badge variant="neutral">{filteredConversations.length} found</Badge>
            )}
          </div>
          
          <nav>
            <ul className="space-y-1">
              {filteredConversations.length > 0 ? (
                filteredConversations.map(conv => (
                  <li key={conv.id}>
                    <Button
                      variant={currentConversationId === conv.id && location.pathname === '/' ? 'subtle' : 'ghost'}
                      className="w-full justify-start gap-3 text-sm"
                      onClick={() => handleSelectConversation(conv.id)}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <span className="truncate flex-1">{conv.title}</span>
                    </Button>
                  </li>
                ))
              ) : searchQuery ? (
                <li className="text-center py-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">No conversations found</p>
                </li>
              ) : (
                <li className="text-center py-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">No conversations yet</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Start a new chat to begin</p>
                </li>
              )}
            </ul>
          </nav>
        </div>
      </div>

      {/* Bottom section: Settings and Theme Toggle */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-2">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3"
          onClick={openSettings}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>Settings</span>
        </Button>

        <Button
          variant="ghost"
          className="w-full justify-start gap-3"
          onClick={toggleTheme}
        >
          {theme === 'dark' ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
          <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </Button>
      </div>
    </aside>
  );
};

export default EnhancedSidebar;
