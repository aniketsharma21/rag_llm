import React, { useState, useEffect } from 'react';

const SettingsPanel = ({ open, onClose, settings, onSave }) => {
  const [localSettings, setLocalSettings] = useState(settings);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings, open]);

  if (!open) {
    return null;
  }

  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setLocalSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSliderChange = (e) => {
    setLocalSettings(prev => ({
        ...prev,
        numDocs: parseInt(e.target.value, 10)
    }));
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center"
      onClick={onClose}
    >
      <div
        className="bg-surface-light dark:bg-surface-dark rounded-lg shadow-xl w-full max-w-md flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold">Settings</h3>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700">
            <span className="material-icons">close</span>
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Model Selection */}
          <div>
            <label htmlFor="model" className="block text-sm font-medium text-text-light dark:text-text-dark mb-1">
              AI Model
            </label>
            <select
              id="model"
              name="model"
              value={localSettings.model}
              onChange={handleInputChange}
              className="w-full bg-surface-light dark:bg-surface-dark border border-gray-300 dark:border-gray-600 rounded-md p-2 focus:ring-primary focus:border-primary"
            >
              <option value="all-MiniLM-L6-v2">MiniLM-L6-v2 (Local)</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4">GPT-4</option>
            </select>
          </div>

          {/* Number of Documents */}
          <div>
            <label htmlFor="numDocs" className="block text-sm font-medium text-text-light dark:text-text-dark">
              Retrieved Documents: {localSettings.numDocs}
            </label>
            <input
              id="numDocs"
              name="numDocs"
              type="range"
              min="1"
              max="10"
              step="1"
              value={localSettings.numDocs}
              onChange={handleSliderChange}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            />
          </div>

          {/* Dark Mode is handled globally, but could be placed here if needed */}

        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;