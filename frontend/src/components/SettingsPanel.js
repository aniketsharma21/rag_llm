import React, { useState, useEffect } from 'react';

/**
 * A modal dialog for viewing and editing application settings.
 * It allows users to change the AI model and the number of retrieved documents.
 *
 * @param {object} props - The component props.
 * @param {boolean} props.open - Controls the visibility of the modal.
 * @param {function} props.onClose - Callback function to close the modal.
 * @param {object} props.settings - The current application settings object.
 * @param {function} props.onSave - Callback function to save the updated settings.
 */
const SettingsPanel = ({ open, onClose, settings, onSave }) => {
  // Use local state to manage form changes without affecting the global state until "Save" is clicked.
  const [localSettings, setLocalSettings] = useState(settings);

  // Sync local state with global settings when the modal is opened.
  useEffect(() => {
    setLocalSettings(settings);
  }, [settings, open]);

  // If the modal is not open, render nothing.
  if (!open) {
    return null;
  }

  /**
   * Calls the onSave callback with the modified local settings and then closes the modal.
   */
  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  /**
   * Handles changes for standard input elements like select dropdowns.
   * @param {React.ChangeEvent<HTMLSelectElement>} e - The event object.
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLocalSettings(prev => ({ ...prev, [name]: value }));
  };

  /**
   * Handles changes for the slider input.
   * @param {React.ChangeEvent<HTMLInputElement>} e - The event object.
   */
  const handleSliderChange = (e) => {
    setLocalSettings(prev => ({ ...prev, numDocs: parseInt(e.target.value, 10) }));
  };

  return (
    // Modal backdrop
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center"
      onClick={onClose}
    >
      {/* Modal content */}
      <div
        className="bg-surface-light dark:bg-surface-dark rounded-lg shadow-xl w-full max-w-md flex flex-col"
        onClick={e => e.stopPropagation()} // Prevents closing the modal when clicking inside the content
      >
        {/* Modal Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold">Settings</h3>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700">
            <span className="material-icons">close</span>
          </button>
        </div>

        {/* Modal Body */}
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
              <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2</option>
            </select>
          </div>

          {/* Number of Documents Slider */}
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
        </div>

        {/* Modal Footer */}
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