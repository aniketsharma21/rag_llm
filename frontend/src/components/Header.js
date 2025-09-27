import React, { useState, useEffect, useRef } from 'react';

const Header = ({ onClearChat, searchQuery, onSearchChange }) => {
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const searchInputRef = useRef(null);

  const handleSearchIconClick = (e) => {
    e.stopPropagation();
    setIsSearchExpanded(true);
  };

  useEffect(() => {
    if (isSearchExpanded) {
      searchInputRef.current?.focus();
    }
  }, [isSearchExpanded]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        searchInputRef.current &&
        !searchInputRef.current.contains(e.target) &&
        e.target.id !== 'search-button' &&
        !e.target.closest('#search-button')
      ) {
        if (!searchQuery) {
          setIsSearchExpanded(false);
        }
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [searchQuery]);

  return (
    <header className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center">
        <h1 className="text-xl font-semibold">AI Assistant</h1>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onClearChat}
          className="flex items-center p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <span className="material-icons mr-1 text-base">delete_outline</span>
          <span className="text-sm">Clear Chat</span>
        </button>
        <div className="relative flex items-center">
          <button
            id="search-button"
            onClick={handleSearchIconClick}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            <span className="material-icons text-text-secondary-light dark:text-text-secondary-dark">search</span>
          </button>
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search History..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            onFocus={() => setIsSearchExpanded(true)}
            className={`absolute right-full top-1/2 -translate-y-1/2 p-0 border-0 rounded-full bg-surface-light dark:bg-surface-dark transition-all duration-300 ease-in-out focus:ring-primary ${
              isSearchExpanded || searchQuery ? 'w-48 p-2 border' : 'w-0'
            }`}
          />
        </div>
      </div>
    </header>
  );
};

export default Header;