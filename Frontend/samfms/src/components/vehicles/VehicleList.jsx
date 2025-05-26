import React from 'react';
import { Edit2, Trash2 } from 'lucide-react';
import SortableHeader from './SortableHeader';
import StatusBadge from './StatusBadge';
import Pagination from './Pagination';

const VehicleList = ({
  vehicles,
  selectedVehicles,
  handleSelectVehicle,
  selectAll,
  handleSelectAll,
  sortField,
  sortDirection,
  handleSort,
  openVehicleDetails,
  currentPage,
  totalPages,
  itemsPerPage,
  changeItemsPerPage,
  goToNextPage,
  goToPrevPage,
}) => {
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-3 px-3 w-10">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectAll}
                    onChange={handleSelectAll}
                    className="h-4 w-4 rounded border-border"
                  />
                </div>
              </th>
              <SortableHeader
                field="id"
                label="Vehicle ID"
                sortField={sortField}
                sortDirection={sortDirection}
                handleSort={handleSort}
              />
              <SortableHeader
                field="make"
                label="Make"
                sortField={sortField}
                sortDirection={sortDirection}
                handleSort={handleSort}
              />
              <SortableHeader
                field="model"
                label="Model"
                sortField={sortField}
                sortDirection={sortDirection}
                handleSort={handleSort}
              />
              <SortableHeader
                field="year"
                label="Year"
                sortField={sortField}
                sortDirection={sortDirection}
                handleSort={handleSort}
              />
              <SortableHeader
                field="mileage"
                label="Mileage"
                sortField={sortField}
                sortDirection={sortDirection}
                handleSort={handleSort}
              />
              <th className="text-left py-3 px-4">Driver</th>
              <th className="text-left py-3 px-4">Status</th>
              <th className="text-left py-3 px-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {vehicles.map(vehicle => (
              <tr
                key={vehicle.id}
                className="border-b border-border hover:bg-accent/10 cursor-pointer"
                onClick={() => openVehicleDetails(vehicle)}
              >
                <td className="py-3 px-3" onClick={e => e.stopPropagation()}>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedVehicles.includes(vehicle.id)}
                      onChange={() => handleSelectVehicle(vehicle.id)}
                      className="h-4 w-4 rounded border-border"
                    />
                  </div>
                </td>
                <td className="py-3 px-4">{vehicle.id}</td>
                <td className="py-3 px-4">{vehicle.make}</td>
                <td className="py-3 px-4">{vehicle.model}</td>
                <td className="py-3 px-4">{vehicle.year}</td>
                <td className="py-3 px-4">{vehicle.mileage} km</td>
                <td className="py-3 px-4">
                  <div className="flex items-center">
                    <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium mr-2">
                      {vehicle.driver !== 'Unassigned'
                        ? vehicle.driver
                            .split(' ')
                            .map(n => n[0])
                            .join('')
                        : 'UA'}
                    </div>
                    {vehicle.driver}
                  </div>
                </td>
                <td className="py-3 px-4">
                  <StatusBadge status={vehicle.status} />
                </td>
                <td className="py-3 px-4" onClick={e => e.stopPropagation()}>
                  <div className="flex space-x-2">
                    <button className="text-primary hover:text-primary/80" title="Edit">
                      <Edit2 size={16} />
                    </button>
                    <button className="text-destructive hover:text-destructive/80" title="Delete">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        itemsPerPage={itemsPerPage}
        goToNextPage={goToNextPage}
        goToPrevPage={goToPrevPage}
        changeItemsPerPage={changeItemsPerPage}
      />
    </>
  );
};

export default VehicleList;
