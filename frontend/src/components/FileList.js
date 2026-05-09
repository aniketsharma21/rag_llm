import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  DocumentTextIcon,
  EyeIcon,
  CalendarIcon,
  ScaleIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const FileList = ({ files }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = () => {
    return <DocumentTextIcon className="w-8 h-8 text-gray-400" />;
  };

  const handlePreview = (file) => {
    if (file.previewUrl) {
      window.open(file.previewUrl, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search files..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Files Grid */}
      {filteredFiles.length === 0 ? (
        <div className="text-center py-12">
          <DocumentTextIcon className="mx-auto w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            {files.length === 0 ? 'No documents uploaded' : 'No files match your search'}
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {files.length === 0
              ? 'Upload your first document to get started'
              : 'Try adjusting your search terms'
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredFiles.map((file, index) => (
            <motion.div
              key={file.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 hover:shadow-lg transition-shadow cursor-pointer hover-lift"
              onClick={() => handlePreview(file)}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  {getFileIcon()}
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {file.name}
                  </h4>

                  <div className="mt-2 space-y-1">
                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                      <ScaleIcon className="w-3 h-3 mr-1" />
                      {formatFileSize(file.size)}
                    </div>

                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                      <CalendarIcon className="w-3 h-3 mr-1" />
                      {new Date(file.uploadDate).toLocaleDateString()}
                    </div>
                  </div>

                  <div className="mt-3 flex space-x-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePreview(file);
                      }}
                      className="flex items-center space-x-1 px-2 py-1 text-xs font-medium text-primary-700 dark:text-primary-300 bg-primary-50 dark:bg-primary-900/20 rounded-md hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-colors"
                    >
                      <EyeIcon className="w-3 h-3" />
                      <span>Preview</span>
                    </motion.button>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileList;
