import React, { useState, useEffect, useRef } from 'react';

/**
 * Renders the header for the main content area.
 * It includes the application title, a "Clear Chat" button, and an expandable search bar.
 *
 * @param {object} props - The component props.
 * @param {function} props.onClearChat - Callback function to clear the current chat messages.
 * @param {string} props.searchQuery - The current value of the search input.
 * @param {function} props.onSearchChange - Callback function to update the search query state in the parent.
 */
const Header = ({ onClearChat, searchQuery, onSearchChange }) => {
  // State to manage the visibility and animation of the search bar
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const searchInputRef = useRef(null);

  /**
   * Expands the search bar when the search icon is clicked.
   * @param {React.MouseEvent<HTMLButtonElement>} e - The click event.
   */
  const handleSearchIconClick = (e) => {
    e.stopPropagation(); // Prevent the click from being caught by the document listener immediately
    setIsSearchExpanded(true);
  };

  /**
   * Effect to focus the search input field automatically when it expands.
   */
  useEffect(() => {
    if (isSearchExpanded) {
      searchInputRef.current?.focus();
    }
  }, [isSearchExpanded]);

  /**
   * Effect to handle clicks outside of the search input, which collapses the bar
   * if it's empty.
   */
  useEffect(() => {
    const handleClickOutside = (e) => {
      // Check if the click is outside the search input and its button
      if (
        searchInputRef.current &&
        !searchInputRef.current.contains(e.target) &&
        e.target.id !== 'search-button' &&
        !e.target.closest('#search-button')
      ) {
        // Only collapse if the search input is empty
        if (!searchQuery) {
          setIsSearchExpanded(false);
        }
      }
    };
    document.addEventListener('click', handleClickOutside);
    // Cleanup the event listener on component unmount
    return () => document.removeEventListener('click', handleClickOutside);
  }, [searchQuery]); // Re-run effect if searchQuery changes, to keep it open while typing

  return (
    <header className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center">
        <h1 className="text-xl font-semibold">AI Assistant</h1>
      </div>
      <div className="flex items-center gap-2">
        {/* Clear Chat Button */}
        <button
          onClick={onClearChat}
          className="flex items-center p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <span className="material-icons mr-1 text-base">delete_outline</span>
          <span className="text-sm">Clear Chat</span>
        </button>
        {/* Search Bar */}
        <div className="relative flex items-center">
          <button
            id="search-button"
            onClick={handleSearchIconClick}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
            aria-label="Search history"
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