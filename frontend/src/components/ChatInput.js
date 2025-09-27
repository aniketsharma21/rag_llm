import React, { useState, useRef, useEffect } from 'react';

const ChatInput = ({ onSendMessage }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <footer className="p-4 md:p-6 bg-background-light dark:bg-background-dark border-t border-gray-200 dark:border-gray-700">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center bg-surface-light dark:bg-surface-dark rounded-lg p-2 shadow-sm">
          <textarea
            ref={textareaRef}
            className="flex-1 bg-transparent border-none focus:ring-0 resize-none text-text-light dark:text-text-dark placeholder-text-secondary-light dark:placeholder-text-secondary-dark"
            placeholder="Type your message..."
            rows="1"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          ></textarea>
          <button
            onClick={handleSend}
            className="bg-primary text-white p-2 rounded-full ml-2 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-background-dark disabled:opacity-50"
            disabled={!input.trim()}
          >
            <span className="material-icons">send</span>
          </button>
        </div>
      </div>
    </footer>
  );
};

export default ChatInput;