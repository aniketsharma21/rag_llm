import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useConversationStore } from '../context/ConversationStoreContext';
import { useConfig } from '../context/ConfigContext';
import EnhancedFileUpload from '../components/EnhancedFileUpload';
import UploadProgress from '../components/UploadProgress';
import FileList from '../components/FileList';

const UploadRoute = () => {
  const [files, setFiles] = useState([]);
  const { activeJobs, handleJobSubmission } = useConversationStore();
  const { apiBaseUrl } = useConfig();

  const refreshFiles = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/files`);
      if (!response.ok) {
        throw new Error(`Unable to load documents (${response.status})`);
      }
      const data = await response.json();
      setFiles(Array.isArray(data.files) ? data.files : []);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    }
  }, [apiBaseUrl]);

  // Fetch uploaded files from backend
  useEffect(() => {
    refreshFiles();
  }, [refreshFiles]);

  const handleUploadComplete = (result) => {
    if (result?.job_id) {
      handleJobSubmission(
        result.job_id,
        result.file_name || 'Uploaded document',
        result.message || 'Processing uploaded document...',
        result.status || 'queued',
      );
    }
    // The file is immediately available for the inventory while ingestion
    // continues in the background.
    refreshFiles();
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar bg-white dark:bg-[#212121]">
      <div className="p-6 max-w-5xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.16 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-1">
          Knowledge Base
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Upload source material, monitor ingestion, and review indexed files.
        </p>
      </motion.div>

      {/* Upload Area */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.16 }}
        className="mb-6"
      >
        <EnhancedFileUpload onUploadComplete={handleUploadComplete} />
      </motion.div>

      {/* Upload Progress */}
      {Object.keys(activeJobs).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.16 }}
          className="mb-6"
        >
          <h2 className="text-base font-semibold mb-3 text-gray-900 dark:text-white">
            Processing Status
          </h2>
          <UploadProgress jobs={activeJobs} />
        </motion.div>
      )}

      {/* File List */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.16 }}
      >
        <h2 className="text-base font-semibold mb-3 text-gray-900 dark:text-white">
          Uploaded Documents ({files.length})
        </h2>
        <FileList files={files} />
      </motion.div>
      </div>
    </div>
  );
};

export default UploadRoute;
