import React from 'react';
import { Link, useLocation } from 'react-router-dom';

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
      <div className="flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold">AI Assistant</h1>
        </div>
        <nav>
          <ul>
            <li className="mb-2">
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); onNewConversation(); }}
                className={`flex items-center p-2 rounded ${location.pathname === '/' ? 'bg-gray-200 dark:bg-gray-700 font-semibold' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}`}
              >
                <span className="material-icons mr-3">add</span> New Chat
              </a>
            </li>
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