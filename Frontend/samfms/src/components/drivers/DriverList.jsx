import React from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
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
              <th className="w-[36px] px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300"
                />
              </th>
              <SortableHeader
                field="id"
                label="Driver ID"
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
            {drivers.map(driver => (
              <tr
                key={driver.id}
                className="border-t border-border hover:bg-accent/10 cursor-pointer"
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedDrivers.includes(driver.id)}
                    onChange={() => handleSelectDriver(driver.id)}
                    className="rounded border-gray-300"
                  />
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  {driver.id}
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
                </td>
                <td className="px-4 py-3" onClick={() => openDriverDetails(driver)}>
                  <StatusBadge status={driver.status} type={getStatusColor(driver.status)} />
                </td>
                <td className="px-4 py-3 space-x-2">
                  <button
                    className="text-primary hover:text-primary/80"
                    onClick={() => openDriverDetails(driver)}
                  >
                    View
                  </button>
                  <button className="text-primary hover:text-primary/80">Edit</button>
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
