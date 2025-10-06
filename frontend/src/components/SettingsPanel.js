import React, { useState, useEffect } from 'react';

import Modal from './ui/Modal';
import Button from './ui/Button';

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
  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setLocalSettings(prev => ({ ...prev, [name]: value }));
  };

  /**
   * Handles changes for the slider input.
   * @param {React.ChangeEvent<HTMLInputElement>} e - The event object.
   */
  const handleSliderChange = (event) => {
    setLocalSettings(prev => ({ ...prev, numDocs: parseInt(event.target.value, 10) }));
  };

  const footer = (
    <div className="flex justify-end gap-3">
      <Button variant="ghost" size="sm" onClick={onClose}>
        Cancel
      </Button>
      <Button size="sm" onClick={handleSave}>
        Save Changes
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Settings"
      size="sm"
      bodyClassName="p-6 space-y-6 bg-surface-light dark:bg-surface-dark"
      footer={footer}
    >
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
    </Modal>
  );
};

export default SettingsPanel;