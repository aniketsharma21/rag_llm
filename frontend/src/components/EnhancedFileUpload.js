import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

/**
 * Enhanced toast notification component with better styling and animations
 */
const Toast = ({ message, type, onClose }) => {
  if (!message) return null;

  const typeStyles = {
    success: 'bg-green-500 text-white',
    error: 'bg-red-500 text-white',
    info: 'bg-blue-500 text-white',
    warning: 'bg-yellow-500 text-black'
  };

  return (
    <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg ${typeStyles[type]} animate-slide-in-right`}>
      <div className="flex items-center justify-between">
        <span>{message}</span>
        <button onClick={onClose} className="ml-4 text-lg font-bold opacity-70 hover:opacity-100">
          ×
        </button>
      </div>
    </div>
  );
};

/**
 * Enhanced file preview modal with better UX
 */
const PreviewModal = ({ file, onClose }) => {
  if (!file) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex justify-center items-center animate-fade-in" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-11/12 h-5/6 flex flex-col max-w-4xl" onClick={e => e.stopPropagation()}>
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">{file.name}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {file.size ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Size unknown'}
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="flex-1 p-6">
          {file.url && file.name.endsWith('.pdf') ? (
            <iframe src={file.url} title="PDF Preview" width="100%" height="100%" className="rounded-lg" />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>No preview available for this file type</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Enhanced FileUpload component with drag & drop, better UX, and mobile responsiveness
 */
function EnhancedFileUpload() {
  // Component State
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [toast, setToast] = useState({ message: '', type: '', show: false });
  const [uploadHistory, setUploadHistory] = useState([]);
  const [previewFile, setPreviewFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Constants
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
  const MAX_SIZE_MB = 10;
  const ALLOWED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];

  /**
   * Show toast notification
   */
  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type, show: true });
    setTimeout(() => setToast(prev => ({ ...prev, show: false })), 5000);
  }, []);

  /**
   * Fetch upload history
   */
  const fetchHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/files`);
      setUploadHistory(res.data.files || []);
    } catch (e) {
      console.error("Failed to fetch upload history:", e);
    }
  }, [API_BASE]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  /**
   * Validate file type and size
   */
  const validateFile = useCallback((file) => {
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.includes(fileExtension)) {
      showToast('Only PDF, DOCX, and TXT files are allowed.', 'error');
      return false;
    }
    
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      showToast(`File size must be under ${MAX_SIZE_MB}MB.`, 'error');
      return false;
    }
    
    return true;
  }, [MAX_SIZE_MB, ALLOWED_TYPES, ALLOWED_EXTENSIONS, showToast]);

  /**
   * Handle file selection
   */
  const handleFileSelect = useCallback((file) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      showToast(`Selected: ${file.name}`, 'success');
    }
  }, [validateFile, showToast]);

  /**
   * Handle file input change
   */
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  /**
   * Drag and drop handlers
   */
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  /**
   * Handle file upload
   */
  const handleUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await axios.post(`${API_BASE}/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });
      
      showToast(response.data.message || 'File uploaded successfully!', 'success');
      setSelectedFile(null);
      fetchHistory(); // Refresh the history
    } catch (error) {
      const errorMessage = error?.response?.data?.message || 'File upload failed!';
      showToast(errorMessage, 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  /**
   * Remove selected file
   */
  const removeSelectedFile = () => {
    setSelectedFile(null);
    showToast('File removed', 'info');
  };

  /**
   * Format file size
   */
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-4 md:p-6 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Upload Documents</h2>
        
        {/* Enhanced Upload Section with Drag & Drop */}
        <div className="mb-8">
          <div
            className={`
              relative border-2 border-dashed rounded-xl p-8 transition-all duration-300 cursor-pointer
              ${isDragOver 
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }
              ${selectedFile ? 'bg-green-50 dark:bg-green-900/20 border-green-500' : ''}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt"
              disabled={uploading}
            />
            
            <div className="text-center">
              {selectedFile ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-center">
                    <svg className="w-12 h-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <button
                    onClick={removeSelectedFile}
                    className="text-red-500 hover:text-red-700 text-sm font-medium"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-center">
                    <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      Drop your file here, or <span className="text-blue-500">browse</span>
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                      Supports PDF, DOCX, and TXT files up to {MAX_SIZE_MB}MB
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Upload Button */}
          <div className="mt-6 flex justify-center">
            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className={`
                px-8 py-3 rounded-lg font-semibold text-white transition-all duration-200
                ${selectedFile && !uploading
                  ? 'bg-blue-500 hover:bg-blue-600 shadow-lg hover:shadow-xl transform hover:scale-105'
                  : 'bg-gray-400 cursor-not-allowed'
                }
              `}
            >
              {uploading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading...
                </div>
              ) : (
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload Document
                </div>
              )}
            </button>
          </div>
        </div>

        {/* Upload History */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Uploaded Files</h3>
          {uploadHistory.length > 0 ? (
            <div className="space-y-3">
              {uploadHistory.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{file.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {file.uploadDate ? new Date(file.uploadDate).toLocaleDateString() : 'Date unknown'}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setPreviewFile(file)}
                    className="p-2 text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                    title="Preview file"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-500 dark:text-gray-400">No files uploaded yet</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Upload your first document to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Modals and Notifications */}
      <PreviewModal file={previewFile} onClose={() => setPreviewFile(null)} />
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(prev => ({ ...prev, show: false }))}
        />
      )}
    </div>
  );
}

export default EnhancedFileUpload;
