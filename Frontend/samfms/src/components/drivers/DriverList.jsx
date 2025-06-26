import React from 'react';
import {Eye, Edit} from 'lucide-react';
import StatusBadge from '../vehicles/StatusBadge';
import Pagination from '../vehicles/Pagination';
import SortableHeader from '../vehicles/SortableHeader';

const DriverList = ({
  drivers,
  sortField,
  sortDirection,
  handleSort,
  openDriverDetails,
  onEditDriver,
  currentPage,
  totalPages,
  itemsPerPage,
  changeItemsPerPage,
  goToNextPage,
  goToPrevPage,
}) => {
  const getStatusColor = status => {
    if (!status || typeof status !== 'string') return 'default';

    const normalizedStatus = status.toLowerCase().replace(/\s+/g, '');

    const statusMap = {
      available: 'success',
      onTrip: 'info',
      onLeave: 'warning',
      inactive: 'destructive',
    };
    return statusMap[normalizedStatus] || 'default';
  };

  return (
    <div>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <SortableHeader
                field="employeeId"
                label="Employee ID"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                field="name"
                label="Full Name"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                field="licenseNumber"
                label="License #"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                field="phone"
                label="Phone"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                field="licenseExpiry"
                label="License Expiry"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                field="email"
                label="Email"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                field="status"
                label="Status"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((driver, index) => (
              <tr
                key={driver.id || driver.employeeId || index}
                className="border-t border-border hover:bg-accent/10 cursor-pointer"
              >
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.employeeId || 'N/A'}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.name || 'N/A'}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.licenseNumber || 'N/A'}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.phone || 'N/A'}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.licenseExpiry || 'N/A'}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.email || 'N/A'}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  <StatusBadge status={driver.status || 'N/A'} type={getStatusColor(driver.status)} />
                </td>
                <td className="px-4 py-3 space-x-2">
                  <button
                    className="text-primary hover:text-primary/80 inline-flex items-center gap-1"
                    onClick={e => {
                      e.stopPropagation();
                      openDriverDetails(driver);
                    }}
                  >
                    <Eye size={16} />
                    View
                  </button>
                  <button
                    className="text-primary hover:text-primary/80 inline-flex items-center gap-1"
                    onClick={e => {
                      e.stopPropagation();
                      onEditDriver?.(driver);
                    }}
                  >
                    <Edit size={16} />
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        itemsPerPage={itemsPerPage}
        changeItemsPerPage={changeItemsPerPage}
        goToNextPage={goToNextPage}
        goToPrevPage={goToPrevPage}
      />
    </div>
  );
};

export default DriverList;
