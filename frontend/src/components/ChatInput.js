import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Renders the message input form at the bottom of the screen.
 * It includes a textarea that automatically resizes with content
 * and a send button.
 *
 * @param {object} props - The component props.
 * @param {function} props.onSendMessage - Callback function to send a message.
 */
const ChatInput = ({ onSendMessage }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  /**
   * Effect to auto-resize the textarea height based on its content.
   */
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto'; // Reset height to shrink if text is deleted
      textarea.style.height = `${textarea.scrollHeight}px`; // Set to content height
    }
  }, [input]);

  /**
   * Handles the click event for the send button.
   */
  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  /**
   * Handles the 'Enter' key press to send the message,
   * while allowing 'Shift+Enter' for new lines.
   * @param {React.KeyboardEvent<HTMLTextAreaElement>} e - The keyboard event.
   */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent default 'Enter' behavior (new line)
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
          />
          <button
            onClick={handleSend}
            className="bg-primary text-white p-2 rounded-full ml-2 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 dark:focus:ring-offset-background-dark disabled:opacity-50"
            disabled={!input.trim()}
            aria-label="Send message"
          >
            <span className="material-icons">send</span>
          </button>
        </div>
      </div>
    </footer>
  );
};

export default ChatInput;