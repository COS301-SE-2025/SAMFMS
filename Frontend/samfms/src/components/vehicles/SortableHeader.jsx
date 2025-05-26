import React from 'react';

import { ArrowUp, ArrowDown } from 'lucide-react';

const SortableHeader = ({ field, label, sortField, sortDirection, handleSort }) => {
  // Function to render sort arrows
  const renderSortArrow = () => {
    if (sortField === field) {
      return sortDirection === 'asc' ? (
        <ArrowUp className="inline ml-1" size={14} />
      ) : (
        <ArrowDown className="inline ml-1" size={14} />
      );
    }
    return null;
  };

  return (
    <th
      className="text-left py-3 px-4 cursor-pointer hover:bg-accent/10"
      onClick={() => handleSort(field)}
    >
      {label} {renderSortArrow()}
    </th>
  );
};

export default SortableHeader;
