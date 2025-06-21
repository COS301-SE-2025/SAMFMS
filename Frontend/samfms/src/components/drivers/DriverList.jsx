import React from 'react';
import { Eye, Edit, Trash2 } from 'lucide-react';
import StatusBadge from '../vehicles/StatusBadge';
import Pagination from '../vehicles/Pagination';
import SortableHeader from '../vehicles/SortableHeader';

const DriverList = ({
  drivers,
  selectedDrivers,
  handleSelectDriver,
  selectAll,
  handleSelectAll,
  sortField,
  sortDirection,
  handleSort,
  openDriverDetails,
  onEditDriver,
  onDeleteDriver,
  currentPage,
  totalPages,
  itemsPerPage,
  changeItemsPerPage,
  goToNextPage,
  goToPrevPage,
}) => {
  const getStatusColor = status => {
    const statusMap = {
      available: 'success',
      onTrip: 'info',
      onLeave: 'warning',
      inactive: 'destructive',
    };
    return statusMap[status.toLowerCase().replace(/\s+/g, '')] || 'default';
  };

  return (
    <div>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              {' '}
              <th className="w-[36px] px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300"
                />
              </th>
              <SortableHeader
                field="employeeId"
                label="Employee ID"
                currentSortField={sortField}
                currentSortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                field="name"
                label="Name"
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
            {' '}
            {drivers.map(driver => (
              <tr
                key={driver.id}
                className="border-t border-border hover:bg-accent/10 cursor-pointer"
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedDrivers.includes(driver.employeeId)}
                    onChange={() => handleSelectDriver(driver.employeeId)}
                    className="rounded border-gray-300"
                  />
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.employeeId}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.name}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.licenseNumber}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.phone}
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.licenseExpiry}
                </td>{' '}
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  <StatusBadge status={driver.status} type={getStatusColor(driver.status)} />
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
                  <button
                    className="text-destructive hover:text-destructive/80 inline-flex items-center gap-1"
                    onClick={e => {
                      e.stopPropagation();
                      console.log('Delete clicked for driver:', driver);

                      if (
                        window.confirm(
                          `Are you sure you want to delete ${driver.name} (${driver.employeeId})?`
                        )
                      ) {
                        // Make sure we have a valid employee ID to pass to the delete function
                        if (!driver.employeeId) {
                          console.error(
                            'Error: Cannot delete driver - Employee ID is missing or undefined',
                            driver
                          );
                          alert(
                            `Error: Cannot delete driver "${driver.name}" - missing Employee ID`
                          );
                          return;
                        }

                        console.log('Calling onDeleteDriver with Employee ID:', driver.employeeId);
                        // Pass the employee ID for backend operations
                        onDeleteDriver?.(driver.employeeId);
                      }
                    }}
                  >
                    <Trash2 size={16} />
                    Delete
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
