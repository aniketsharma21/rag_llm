import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useConfig } from '../context/ConfigContext';

/**
 * A simple modal component for displaying a preview of a file.
 * Currently supports PDF previews in an iframe.
 * @param {object} props - The component props.
 * @param {object} props.file - The file object to preview.
 * @param {function} props.onClose - Callback function to close the modal.
 */
const PreviewModal = ({ file, onClose }) => {
  if (!file) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center" onClick={onClose}>
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg shadow-xl w-11/12 h-5/6 flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold">{file.name}</h3>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700">
            <span className="material-icons">close</span>
          </button>
        </div>
        <div className="flex-1 p-4">
          {file.url && file.name.endsWith('.pdf') ? (
            <iframe src={file.url} title="PDF Preview" width="100%" height="100%" />
          ) : (
            <p>No preview available for this file type.</p>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * A simple notification "toast" component for displaying success or error messages.
 * @param {object} props - The component props.
 * @param {string} props.message - The message to display.
 * @param {string} props.severity - The type of notification ('success' or 'error').
 * @param {function} props.onClose - Callback function to close the notification.
 */
const Notification = ({ message, severity, onClose }) => {
  if (!message) return null;

  const severityClasses = {
    success: 'bg-green-100 border-green-400 text-green-700 dark:bg-green-900 dark:border-green-600 dark:text-green-200',
    error: 'bg-red-100 border-red-400 text-red-700 dark:bg-red-900 dark:border-red-600 dark:text-red-200',
  };

  return (
    <div className={`fixed bottom-5 left-1/2 -translate-x-1/2 p-4 border rounded-md shadow-lg ${severityClasses[severity] || 'bg-gray-100 border-gray-400'}`}>
      <div className="flex items-center">
        <p>{message}</p>
        <button onClick={onClose} className="ml-4 p-1 rounded-full hover:bg-gray-200/50">
          <span className="material-icons text-base">close</span>
        </button>
      </div>
    </div>
  );
};

/**
 * A component that provides a UI for uploading documents to the server.
 * It includes file validation, upload progress, notifications, and a history of uploaded files.
 */
function FileUpload() {
  // Component State
  const [selectedFile, setSelectedFile] = useState(null); // The file currently selected by the user
  const [uploading, setUploading] = useState(false); // Flag to indicate an active upload
  const [uploadProgress, setUploadProgress] = useState(0); // Upload progress percentage
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' }); // For showing success/error messages
  const [uploadHistory, setUploadHistory] = useState([]); // List of previously uploaded files
  const [previewFile, setPreviewFile] = useState(null); // The file to be shown in the preview modal
  const [isDragOver, setIsDragOver] = useState(false); // Track drag over state for visual feedback

  // Constants
  const { apiBaseUrl } = useConfig();
  const MAX_SIZE_MB = 10;
  const ALLOWED_TYPES = ['application/pdf'];

  /**
   * Fetches the history of uploaded files from the backend when the component mounts
   * or when a new file is successfully uploaded.
   */
  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await axios.get(`${apiBaseUrl}/files`);
        setUploadHistory(res.data.files || []);
      } catch (e) {
        console.error("Failed to fetch upload history:", e);
      }
    }
    fetchHistory();
  }, [notification.open]); // Refreshes history after a notification (i.e., after an upload attempt)

  /**
   * Validates the selected file based on type and size.
   * @param {React.ChangeEvent<HTMLInputElement>} event - The file input change event.
   */
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (!ALLOWED_TYPES.includes(file.type)) {
      setNotification({ open: true, message: 'Only PDF files are allowed.', severity: 'error' });
      setSelectedFile(null);
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setNotification({ open: true, message: `File size must be under ${MAX_SIZE_MB}MB.`, severity: 'error' });
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  };

  /**
   * Handles the file upload process, including progress tracking and notifications.
   */
  const handleUpload = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await axios.post(`${apiBaseUrl}/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });
      setNotification({ open: true, message: response.data.message, severity: 'success' });
    } catch (error) {
      setNotification({ open: true, message: error?.response?.data?.message || 'File upload failed!', severity: 'error' });
    } finally {
      setUploading(false);
      setSelectedFile(null);
    }
  };

  /**
   * Effect to automatically hide notifications after a delay.
   */
  useEffect(() => {
      if (notification.open) {
          const timer = setTimeout(() => setNotification({ open: false, message: '', severity: 'info' }), 5000);
          return () => clearTimeout(timer);
      }
  }, [notification.open]);

  return (
    <div className="p-4 md:p-6 h-full overflow-y-auto">
        <h2 className="text-2xl font-bold mb-4">Upload Documents</h2>
        {/* Upload Section */}
        <div className="bg-surface-light dark:bg-surface-dark p-6 rounded-lg shadow-md">
            <div className="flex items-center space-x-4">
                <label className="cursor-pointer bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 flex items-center">
                    <span className="material-icons mr-2">upload_file</span>
                    Choose File
                    <input type="file" className="hidden" onChange={handleFileChange} accept="application/pdf" />
                </label>
                {selectedFile && (
                    <p className="text-text-secondary-light dark:text-text-secondary-dark">{selectedFile.name}</p>
                )}
                <button
                    onClick={handleUpload}
                    disabled={!selectedFile || uploading}
                    className="ml-auto bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                    <span className="material-icons mr-2">cloud_upload</span>
                    Upload
                </button>
            </div>
            {uploading && (
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mt-4">
                    <div className="bg-primary h-2.5 rounded-full" style={{ width: `${uploadProgress}%` }}></div>
                </div>
            )}
        </div>

        {/* Upload History Section */}
        <div className="mt-8">
            <h3 className="text-xl font-semibold mb-4">Uploaded Files</h3>
            <div className="bg-surface-light dark:bg-surface-dark p-4 rounded-lg shadow-md">
                <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                    {uploadHistory.length > 0 ? uploadHistory.map((file, idx) => (
                        <li key={idx} className="py-3 flex items-center justify-between">
                            <p className="text-sm font-medium">{file.name}</p>
                            <button
                                onClick={() => setPreviewFile(file)}
                                className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
                                aria-label="Preview document"
                            >
                                <span className="material-icons text-base">visibility</span>
                            </button>
                        </li>
                    )) : (
                        <p className="text-text-secondary-light dark:text-text-secondary-dark text-center py-4">No files uploaded yet.</p>
                    )}
                </ul>
            </div>
        </div>

        <PreviewModal file={previewFile} onClose={() => setPreviewFile(null)} />
        <Notification
            message={notification.message}
            severity={notification.severity}
            onClose={() => setNotification({ open: false, message: '', severity: 'info' })}
        />
    </div>
  );
}

export default FileUpload;