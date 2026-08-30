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

  const safeFiles = Array.isArray(files) ? files : [];
  const filteredFiles = safeFiles.filter(file =>
    (file?.name || 'Untitled document').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatFileSize = (bytes) => {
    if (!Number.isFinite(bytes) || bytes < 0) return 'Unknown size';
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

  const getUploadDate = (file) => {
    if (!file?.uploadDate) return 'Unknown date';
    const date = new Date(file.uploadDate);
    return Number.isNaN(date.getTime()) ? 'Unknown date' : date.toLocaleDateString();
  };

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative max-w-md">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search files..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-neutral-700 rounded-xl bg-white dark:bg-[#2f2f2f] text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
        />
      </div>

      {/* Files Grid */}
      {filteredFiles.length === 0 ? (
        <div className="text-center py-12">
          <DocumentTextIcon className="mx-auto w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            {safeFiles.length === 0 ? 'No documents uploaded' : 'No files match your search'}
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {safeFiles.length === 0
              ? 'Upload your first document to get started'
              : 'Try adjusting your search terms'
            }
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-[#2f2f2f]">
          {filteredFiles.map((file, index) => (
            <motion.div
              key={file.id || file.name || index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 border-b last:border-b-0 border-gray-200 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
              onClick={() => handlePreview(file)}
            >
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0">
                  {getFileIcon()}
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {file.name || 'Untitled document'}
                  </h4>

                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1">
                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                      <ScaleIcon className="w-3 h-3 mr-1" />
                      {formatFileSize(Number(file.size))}
                    </div>

                    <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                      <CalendarIcon className="w-3 h-3 mr-1" />
                      {getUploadDate(file)}
                    </div>
                  </div>

                </div>

                <div className="flex-shrink-0">
                    <motion.button
                      whileHover={{ y: -1 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePreview(file);
                      }}
                      disabled={!file.previewUrl}
                      className={`flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                        file.previewUrl
                          ? 'text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/30 hover:bg-emerald-100 dark:hover:bg-emerald-900/40'
                          : 'text-gray-400 bg-gray-100 dark:bg-neutral-800 cursor-not-allowed'
                      }`}
                    >
                      <EyeIcon className="w-3 h-3" />
                      <span>Preview</span>
                    </motion.button>
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
