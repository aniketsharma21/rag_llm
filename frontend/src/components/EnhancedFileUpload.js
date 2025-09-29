import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { useConfig } from '../context/ConfigContext';
import Button from './ui/Button';
import IconButton from './ui/IconButton';
import Card, { CardContent } from './ui/Card';
import Badge from './ui/Badge';
import Modal from './ui/Modal';
import Toast from './ui/Toast';
import RefreshOutlinedIcon from '@mui/icons-material/RefreshOutlined';

function EnhancedFileUpload() {
  // Component State
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [toast, setToast] = useState({ message: '', type: 'info', show: false });
  const [uploadHistory, setUploadHistory] = useState([]);
  const [previewFile, setPreviewFile] = useState(null);
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
   * Fetch upload history
   */
  const buildPreviewUrl = useCallback((path) => {
    if (!path) return null;
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const normalized = path.startsWith('/') ? path : `/${path}`;
    return `${apiBaseUrl}${normalized}`;
  }, [apiBaseUrl]);

  const normalizeFileRecord = useCallback((record) => {
    if (!record || typeof record !== 'object') {
      return record;
    }

    const previewUrl = buildPreviewUrl(record.previewUrl || record.url);

    return {
      ...record,
      previewUrl,
      url: previewUrl,
    };
  }, [buildPreviewUrl]);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/files`);
      const files = Array.isArray(res.data?.files) ? res.data.files : [];
      setUploadHistory(files.map(normalizeFileRecord));
    } catch (e) {
      console.error("Failed to fetch upload history:", e);
      showToast('Unable to fetch uploaded files. Please try again later.', 'error');
    }
  }, [apiBaseUrl, normalizeFileRecord]);

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
      const response = await axios.post(`${apiBaseUrl}/ingest`, formData, {
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
      {toast.show && (
        <Toast message={toast.message} type={toast.type} onClose={dismissToast} />
      )}

      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h2 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">Upload Documents</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Drag and drop {humanReadableTypes.join(', ')} files up to {MAX_SIZE_MB}MB or browse your computer.
          </p>
        </div>

        <Card className="p-8">
          <div
            className={`
              relative border-2 border-dashed rounded-xl p-8 transition-all duration-300 cursor-pointer
              ${isDragOver
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'}
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
              accept=".pdf,.docx,.txt,.md,.csv,.json,.pptx,.xlsx"
              disabled={uploading}
            />

            <div className="text-center space-y-4">
              {selectedFile ? (
                <>
                  <div className="flex justify-center">
                    <svg className="w-12 h-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={removeSelectedFile} className="text-red-500 hover:text-red-600">
                    Remove file
                  </Button>
                </>
              ) : (
                <>
                  <div className="flex justify-center">
                    <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      Drop your file here, or <span className="text-blue-500">browse</span>
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
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
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

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Uploaded Files</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Recently uploaded documents appear here.</p>
            </div>
            <IconButton onClick={fetchHistory} tooltip="Refresh list">
              <RefreshOutlinedIcon fontSize="small" />
            </IconButton>
          </div>

          {uploadHistory.length > 0 ? (
            <div className="space-y-3">
              {uploadHistory.map((file, idx) => (
                <Card key={idx} className="p-4 bg-gray-50 dark:bg-gray-800/60">
                  <CardContent className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-0">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900 dark:text-white">{file.name}</p>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-gray-300">
                          {file.uploadDate && (
                            <Badge variant="neutral">{new Date(file.uploadDate).toLocaleString()}</Badge>
                          )}
                          {file.size && (
                            <Badge variant="blue">{formatFileSize(file.size)}</Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {file.previewUrl ? (
                        <Button variant="subtle" size="sm" onClick={() => setPreviewFile(file)}>
                          Preview
                        </Button>
                      ) : null}
                      {file.previewUrl ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          as="a"
                          href={file.previewUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Open
                        </Button>
                      ) : null}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p>No files uploaded yet. Upload a document to see it here.</p>
            </div>
          )}
        </Card>
      </div>

      <Modal
        isOpen={!!previewFile}
        title={previewFile?.name}
        subtitle={previewFile?.size ? formatFileSize(previewFile.size) : undefined}
        onClose={() => setPreviewFile(null)}
      >
        {previewFile ? (
          previewFile.previewUrl && previewFile.name?.toLowerCase().endsWith('.pdf') ? (
            <iframe
              src={previewFile.previewUrl}
              title={`${previewFile.name} preview`}
              className="w-full h-full border-0"
            />
          ) : previewFile.previewUrl ? (
            <div className="flex items-center justify-center h-full">
              <a
                href={previewFile.previewUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-600"
              >
                Open file in a new tab
              </a>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <p>No preview available for this file type.</p>
            </div>
          )
        ) : null}
      </Modal>
    </div>
  );
}

export default EnhancedFileUpload;
