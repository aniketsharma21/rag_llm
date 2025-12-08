import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useConversationStore } from '../context/ConversationStoreContext';
import EnhancedFileUpload from '../components/EnhancedFileUpload';
import UploadProgress from '../components/UploadProgress';
import FileList from '../components/FileList';

const UploadRoute = () => {
  const [files, setFiles] = useState([]);
  const { activeJobs } = useConversationStore();

  // Fetch uploaded files from backend
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await fetch('/files');
        if (response.ok) {
          const data = await response.json();
          setFiles(data.files || []);
        }
      } catch (error) {
        console.error('Failed to fetch files:', error);
      }
    };

    fetchFiles();
  }, []);

  const handleUploadComplete = () => {
    // Refresh file list after upload
    setTimeout(async () => {
      try {
        const response = await fetch('/files');
        if (response.ok) {
          const data = await response.json();
          setFiles(data.files || []);
        }
      } catch (error) {
        console.error('Failed to refresh files:', error);
      }
    }, 1000);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Document Management
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload and manage your documents for RAG processing
        </p>
      </motion.div>

      {/* Upload Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <EnhancedFileUpload onUploadComplete={handleUploadComplete} />
      </motion.div>

      {/* Upload Progress */}
      {Object.keys(activeJobs).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Processing Status
          </h2>
          <UploadProgress jobs={activeJobs} />
        </motion.div>
      )}

      {/* File List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          Uploaded Documents ({files.length})
        </h2>
        <FileList files={files} />
      </motion.div>
    </div>
  );
};

export default UploadRoute;