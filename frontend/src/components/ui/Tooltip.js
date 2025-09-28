import React, { useState } from 'react';

const Tooltip = ({ content, children, className = '' }) => {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className={`relative inline-flex ${className}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && content && (
        <div className="absolute z-50 px-2 py-1 text-xs text-white bg-black/80 rounded-md shadow-md transform -translate-y-full -translate-x-1/2 left-1/2 mb-2 whitespace-nowrap">
          {content}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
