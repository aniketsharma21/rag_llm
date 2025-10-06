import React from 'react';

import Card, { CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

const SourceList = ({ sources, expandedCards, onToggle, onPreview }) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center mb-3">
        <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span className="font-medium text-sm text-gray-700 dark:text-gray-300">
          Sources ({sources.length})
        </span>
      </div>
      <div className="space-y-3">
        {sources.map((source, index) => {
          const isExpanded = expandedCards.includes(index);

          return (
            <Card key={source.key} className="bg-white dark:bg-gray-900/60">
              <button
                type="button"
                onClick={() => onToggle(index)}
                className="w-full flex items-start justify-between px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800/70 rounded-t-xl"
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center text-xs font-semibold text-blue-600 dark:text-blue-300">
                    {source.citation}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                      {source.displayName}
                    </p>
                    {source.pageLabel && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {source.pageLabel}
                      </p>
                    )}
                    {source.sourceDisplayPath && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                        {source.sourceDisplayPath}
                      </p>
                    )}
                    {!isExpanded && source.snippet && (
                      <p className="mt-1 text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
                        {source.snippet}
                      </p>
                    )}
                  </div>
                </div>
                <svg
                  className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {isExpanded && (
                <CardContent className="border-t border-gray-200 dark:border-gray-700">
                  {source.snippet && (
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      {source.snippet}
                    </p>
                  )}
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    {source.pageLabel && (
                      <Badge variant="blue">{source.pageLabel}</Badge>
                    )}
                    {source.relevance !== null && (
                      <Badge variant="green">Relevance: {(source.relevance * 100).toFixed(0)}%</Badge>
                    )}
                    {source.confidence !== null && (
                      <Badge variant="purple">Confidence: {(source.confidence * 100).toFixed(0)}%</Badge>
                    )}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {source.previewUrl && (
                      <Button variant="subtle" size="sm" onClick={() => onPreview(source)}>
                        Quick preview
                      </Button>
                    )}
                    {source.externalUrl && (
                      <Button
                        as="a"
                        href={source.externalUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="secondary"
                        size="sm"
                      >
                        Open source
                      </Button>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default SourceList;
