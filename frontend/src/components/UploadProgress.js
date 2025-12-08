import React from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/solid';

const UploadProgress = ({ jobs }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <Cog6ToothIcon className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20';
      case 'failed':
        return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20';
      case 'processing':
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20';
      default:
        return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20';
    }
  };

  return (
    <div className="space-y-3">
      {Object.entries(jobs).map(([jobId, job]) => (
        <motion.div
          key={jobId}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className={`
            flex items-center space-x-4 p-4 rounded-xl border
            ${getStatusColor(job.status)}
          `}
        >
          {getStatusIcon(job.status)}

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                {job.fileName}
              </h4>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                {job.status}
              </span>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {job.message}
            </p>

            {job.status === 'processing' && (
              <div className="mt-2">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                  <div className="bg-blue-500 h-1.5 rounded-full animate-pulse w-1/3"></div>
                </div>
              </div>
            )}

            {job.details && Object.keys(job.details).length > 0 && (
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {Object.entries(job.details).map(([key, value]) => (
                  <span key={key} className="mr-4">
                    {key}: {String(value)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default UploadProgress;
