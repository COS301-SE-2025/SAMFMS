import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const Pagination = ({
  currentPage,
  totalPages,
  itemsPerPage,
  goToNextPage,
  goToPrevPage,
  changeItemsPerPage,
}) => {
  return (
    <div className="bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 
                    rounded-lg p-4 border border-gray-200 dark:border-gray-700 
                    flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Items per page:</span>
        <select
          value={itemsPerPage}
          onChange={changeItemsPerPage}
          className="px-3 py-2 border-2 border-gray-200 dark:border-gray-600 rounded-lg 
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                     dark:bg-gray-700 dark:text-white transition-all duration-200 
                     hover:border-blue-300 dark:hover:border-blue-400 text-sm"
        >
          <option value="5">5 per page</option>
          <option value="10">10 per page</option>
          <option value="20">20 per page</option>
          <option value="50">50 per page</option>
        </select>
      </div>
      <div className="flex items-center space-x-4">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Page <span className="font-bold text-blue-600 dark:text-blue-400">{currentPage}</span> of <span className="font-bold">{totalPages}</span>
        </span>
        <div className="flex items-center space-x-1">
          <button
            onClick={goToPrevPage}
            disabled={currentPage === 1}
            className={`p-2 rounded-lg transition-all duration-200 ${
              currentPage === 1 
                ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed' 
                : 'text-gray-700 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400'
            }`}
            title="Previous page"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            onClick={goToNextPage}
            disabled={currentPage === totalPages}
            className={`p-2 rounded-lg transition-all duration-200 ${
              currentPage === totalPages
                ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
                : 'text-gray-700 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400'
            }`}
            title="Next page"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Pagination;
