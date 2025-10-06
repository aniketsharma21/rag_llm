import React from 'react';
import { Link, useLocation } from 'react-router-dom';

/**
 * Renders the main sidebar for the application.
 * It includes navigation for starting new chats, browsing documents, viewing conversation history,
 * and accessing settings and theme controls.
 *
 * @param {object} props - The component props.
 * @param {string} props.theme - The current theme ('light' or 'dark').
 * @param {function} props.onThemeToggle - Callback function to toggle the theme.
 * @param {Array<object>} props.conversations - The list of past conversations.
 * @param {function} props.onNewConversation - Callback to start a new conversation.
 * @param {function} props.onSelectConversation - Callback to load a past conversation.
 * @param {string|null} props.currentConversationId - The ID of the currently active conversation.
 * @param {function} props.onSettingsClick - Callback to open the settings modal.
 */
const Sidebar = ({
  onThemeToggle,
  theme,
  conversations,
  onNewConversation,
  onSelectConversation,
  currentConversationId,
  onSettingsClick,
}) => {
  const location = useLocation();

  return (
    <aside className="bg-surface-light dark:bg-surface-dark w-64 p-4 flex flex-col justify-between hidden md:flex transition-all duration-300">
      {/* Top section: Title and main navigation */}
      <div className="flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold">AI Assistant</h1>
        </div>
        <nav>
          <ul>
            {/* New Chat Button */}
            <li className="mb-2">
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); onNewConversation(); }}
                className={`flex items-center p-2 rounded ${location.pathname === '/' ? 'bg-gray-200 dark:bg-gray-700 font-semibold' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
              >
                <span className="material-icons mr-3">add</span> New Chat
              </a>
            </li>
            {/* Browse Documents Link */}
            <li className="mb-2">
              <Link
                to="/upload"
                className={`flex items-center p-2 rounded ${location.pathname === '/upload' ? 'bg-gray-200 dark:bg-gray-700 font-semibold' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
              >
                <span className="material-icons mr-3">folder_open</span> Browse Documents
              </Link>
            </li>
          </ul>
        </nav>
        <hr className="my-4 border-gray-200 dark:border-gray-700" />
        {/* Conversation History Section */}
        <div className="flex-1 overflow-y-auto">
          <h2 className="text-sm font-semibold text-text-secondary-light dark:text-text-secondary-dark mb-2 px-2">History</h2>
          <nav>
            <ul>
              {conversations.map(conv => (
                <li key={conv.id} className="mb-1">
                  <a
                    href="#"
                    onClick={(e) => { e.preventDefault(); onSelectConversation(conv.id); }}
                    className={`flex items-center p-2 rounded text-sm truncate ${currentConversationId === conv.id && location.pathname === '/' ? 'bg-gray-200 dark:bg-gray-700 font-semibold' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
                  >
                    <span className="material-icons mr-3 text-base">chat_bubble_outline</span>
                    {conv.title}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>
      {/* Bottom section: Settings and Theme Toggle */}
      <div>
        <button
          onClick={onSettingsClick}
          className="w-full flex items-center p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <span className="material-icons mr-3">settings</span> Settings
        </button>
        <button
          onClick={onThemeToggle}
          className="w-full flex items-center p-2 mt-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <span className="material-icons mr-3">{theme === 'dark' ? 'light_mode' : 'brightness_4'}</span>
          <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;