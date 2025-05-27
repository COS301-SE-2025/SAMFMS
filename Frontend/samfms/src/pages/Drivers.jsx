import React, { useState, useEffect } from 'react';
import { PlusCircle } from 'lucide-react';
import DriverList from '../components/drivers/DriverList';
import DriverSearch from '../components/drivers/DriverSearch';
import DriverActions from '../components/drivers/DriverActions';
import DriverDetailsModal from '../components/drivers/DriverDetailsModal';
import VehicleAssignmentModal from '../components/drivers/VehicleAssignmentModal';
import DataVisualization from '../components/drivers/DataVisualization';

const Drivers = () => {
  const [drivers, setDrivers] = useState([]);
  const [selectedDrivers, setSelectedDrivers] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [driverDetailsOpen, setDriverDetailsOpen] = useState(false);
  const [currentDriver, setCurrentDriver] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [sortField, setSortField] = useState('id');
  const [sortDirection, setSortDirection] = useState('asc');
  const [showVehicleAssignmentModal, setShowVehicleAssignmentModal] = useState(false);
  const [showAddDriverModal, setShowAddDriverModal] = useState(false);
  

  // Sorting function
  const handleSort = field => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Sort drivers based on current sort field and direction
  const sortedDrivers = [...drivers].sort((a, b) => {
    // Standard string comparison
    if (a[sortField] < b[sortField]) return sortDirection === 'asc' ? -1 : 1;
    if (a[sortField] > b[sortField]) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Get current drivers for pagination
  const indexOfLastDriver = currentPage * itemsPerPage;
  const indexOfFirstDriver = indexOfLastDriver - itemsPerPage;
  const currentDrivers = sortedDrivers.slice(indexOfFirstDriver, indexOfLastDriver);
  const totalPages = Math.ceil(drivers.length / itemsPerPage);

  // Toggle select all
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedDrivers([]);
    } else {
      setSelectedDrivers(currentDrivers.map(driver => driver.id));
    }
    setSelectAll(!selectAll);
  };

  // Toggle select individual driver
  const handleSelectDriver = driverId => {
    if (selectedDrivers.includes(driverId)) {
      setSelectedDrivers(selectedDrivers.filter(id => id !== driverId));
    } else {
      setSelectedDrivers([...selectedDrivers, driverId]);
    }
  };

  // Open driver details
  const openDriverDetails = driver => {
    setCurrentDriver(driver);
    setDriverDetailsOpen(true);
  };

  // Close driver details
  const closeDriverDetails = () => {
    setDriverDetailsOpen(false);
    setCurrentDriver(null);
  };

  // Open vehicle assignment modal
  const openVehicleAssignmentModal = () => {
    setShowVehicleAssignmentModal(true);
  };

  // Close vehicle assignment modal
  const closeVehicleAssignmentModal = () => {
    setShowVehicleAssignmentModal(false);
  };

  // Export selected drivers
  const exportSelectedDrivers = () => {
    const selectedData = drivers.filter(driver => selectedDrivers.includes(driver.id));
    // In a real app, this would create a CSV or Excel file
    console.log('Exporting data for:', selectedData);
    alert(`Exporting data for ${selectedData.length} drivers`);
  };

  // Pagination handlers
  const goToNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const goToPrevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const changeItemsPerPage = e => {
    setItemsPerPage(parseInt(e.target.value));
    setCurrentPage(1); // Reset to first page
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Fleet Drivers</h1>
      <div className="bg-card rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Manage Drivers</h2>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition flex items-center gap-2">
            <PlusCircle size={18} />
            <span>Add Driver</span>
          </button>
        </div>

        {/* Search and filter bar */}
        <DriverSearch
          filterOpen={filterOpen}
          setFilterOpen={setFilterOpen}
          onSearch={() => {}}
          onApplyFilters={() => setFilterOpen(false)}
          onResetFilters={() => setFilterOpen(false)}
        />

        {/* Driver actions */}
        <DriverActions
          selectedDrivers={selectedDrivers}
          exportSelectedDrivers={exportSelectedDrivers}
        />

        {/* Driver list with pagination */}
        <DriverList
          drivers={currentDrivers}
          selectedDrivers={selectedDrivers}
          handleSelectDriver={handleSelectDriver}
          selectAll={selectAll}
          handleSelectAll={handleSelectAll}
          sortField={sortField}
          sortDirection={sortDirection}
          handleSort={handleSort}
          openDriverDetails={openDriverDetails}
          currentPage={currentPage}
          totalPages={totalPages}
          itemsPerPage={itemsPerPage}
          changeItemsPerPage={changeItemsPerPage}
          goToNextPage={goToNextPage}
          goToPrevPage={goToPrevPage}
        />
      </div>

      {/* Driver Details Modal */}
      {driverDetailsOpen && currentDriver && (
        <DriverDetailsModal
          driver={currentDriver}
          closeDriverDetails={closeDriverDetails}
          openVehicleAssignmentModal={openVehicleAssignmentModal}
        />
      )}

      {/* Vehicle Assignment Modal */}
      {showVehicleAssignmentModal && (
        <VehicleAssignmentModal
          closeVehicleAssignmentModal={closeVehicleAssignmentModal}
          selectedDrivers={selectedDrivers}
          currentDriver={currentDriver}
        />
      )}

      {/* Data visualization section */}
      <DataVisualization />
    </div>
  );
};

export default Drivers;
