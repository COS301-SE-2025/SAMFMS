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
    <div className="mt-6 flex items-center justify-between">
      <div>
        <select
          value={itemsPerPage}
          onChange={changeItemsPerPage}
          className="border border-border rounded-md bg-background py-1 pl-2 pr-8"
        >
          <option value="5">5 per page</option>
          <option value="10">10 per page</option>
          <option value="20">20 per page</option>
          <option value="50">50 per page</option>
        </select>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          Page {currentPage} of {totalPages}
        </span>
        <div className="flex gap-1">
          <button
            onClick={goToPrevPage}
            disabled={currentPage === 1}
            className={`p-1 rounded ${
              currentPage === 1 ? 'text-muted-foreground cursor-not-allowed' : 'hover:bg-accent'
            }`}
          >
            <ChevronLeft size={18} />
          </button>
          <button
            onClick={goToNextPage}
            disabled={currentPage === totalPages}
            className={`p-1 rounded ${
              currentPage === totalPages
                ? 'text-muted-foreground cursor-not-allowed'
                : 'hover:bg-accent'
            }`}
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Pagination;
