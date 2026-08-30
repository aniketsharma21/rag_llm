import React, { useState, useCallback, useMemo } from 'react';
import axios from 'axios';
import { useConfig } from '../context/ConfigContext';
import Button from './ui/Button';
import Card from './ui/Card';
import Toast from './ui/Toast';

function EnhancedFileUpload({ onUploadComplete }) {
  // Component State
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [toast, setToast] = useState({ message: '', type: 'info', show: false });
  const [isDragOver, setIsDragOver] = useState(false);

  // Constants
  const { apiBaseUrl } = useConfig();
  const MAX_SIZE_MB = 10;
  const ALLOWED_TYPES = useMemo(() => [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
    'text/csv',
    'application/json',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ], []);
  const ALLOWED_EXTENSIONS = useMemo(
    () => ['.pdf', '.docx', '.txt', '.md', '.csv', '.json', '.pptx', '.xlsx'],
    [],
  );
  const humanReadableTypes = useMemo(
    () => ['PDF', 'DOCX', 'TXT', 'MD', 'CSV', 'JSON', 'PPTX', 'XLSX'],
    [],
  );

  /**
   * Show toast notification
   */
  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type, show: true });
  }, []);

  const dismissToast = useCallback(() => {
    setToast(prev => ({ ...prev, show: false }));
  }, []);

  /**
   * Validate file type and size
   */
  const validateFile = useCallback((file) => {
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.includes(fileExtension)) {
      showToast(`Only ${humanReadableTypes.join(', ')} files are allowed.`, 'error');
      return false;
    }
    
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      showToast(`File size must be under ${MAX_SIZE_MB}MB.`, 'error');
      return false;
    }
    
    return true;
  }, [MAX_SIZE_MB, ALLOWED_TYPES, ALLOWED_EXTENSIONS, showToast, humanReadableTypes]);

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
    const response = await axios.post(`${apiBaseUrl}/ingest`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      },
    });

    showToast(response.data.message || 'File uploaded successfully!', 'success');
    setSelectedFile(null);

    // Notify parent component that upload is complete
    if (onUploadComplete) {
      onUploadComplete(response.data);
    }
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
    <div>
      {toast.show && (
        <Toast message={toast.message} type={toast.type} onClose={dismissToast} />
      )}

      <div className="space-y-6">
        <div>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
            Document Upload
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Upload {humanReadableTypes.join(', ')} files up to {MAX_SIZE_MB}MB. Files will be processed for intelligent search and retrieval.
          </p>
        </div>

        <Card className="p-5">
          <div
            className={`
              relative border border-dashed rounded-lg p-8 transition-colors duration-150 cursor-pointer
              ${isDragOver
                ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/20'
                : 'border-gray-300 dark:border-neutral-700 hover:border-gray-400 dark:hover:border-neutral-500'}
              ${selectedFile ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-500' : ''}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt,.md,.csv,.json,.pptx,.xlsx"
              disabled={uploading}
            />

            <div className="text-center space-y-4">
              {selectedFile ? (
                <>
                  <div className="flex justify-center">
                    <svg className="w-10 h-10 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-100">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={removeSelectedFile} className="text-red-500 hover:text-red-600">
                    Remove file
                  </Button>
                </>
              ) : (
                <>
                  <div className="flex justify-center">
                    <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-base font-semibold text-gray-900 dark:text-gray-100">
                      Drop your file here, or <span className="text-emerald-600 dark:text-emerald-400">browse</span>
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                      Supports {humanReadableTypes.join(', ')} up to {MAX_SIZE_MB}MB
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {uploading && (
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2">
                <div
                  className="bg-emerald-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <div className="mt-6 flex justify-center">
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className={`${(!selectedFile || uploading) ? 'opacity-60 cursor-not-allowed' : ''} w-full sm:w-auto`}
            >
              {uploading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading...
                </span>
              ) : (
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload Document
                </span>
              )}
            </Button>
          </div>
        </Card>

      </div>
    </div>
  );
}

export default EnhancedFileUpload;
