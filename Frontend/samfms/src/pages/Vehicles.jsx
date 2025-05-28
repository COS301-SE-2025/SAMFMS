import React, { useState, useEffect } from 'react';
import { PlusCircle } from 'lucide-react';
import VehicleList from '../components/vehicles/VehicleList';
import VehicleSearch from '../components/vehicles/VehicleSearch';
import VehicleActions from '../components/vehicles/VehicleActions';
import VehicleDetailsModal from '../components/vehicles/VehicleDetailsModal';
import DriverAssignmentModal from '../components/vehicles/DriverAssignmentModal';
import DataVisualization from '../components/vehicles/DataVisualization';
import AddVehicleModal from '../components/vehicles/AddVehicleModal';

const Vehicles = () => {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicles, setSelectedVehicles] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const [vehicleDetailsOpen, setVehicleDetailsOpen] = useState(false);
  const [currentVehicle, setCurrentVehicle] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [sortField, setSortField] = useState('id');
  const [sortDirection, setSortDirection] = useState('asc');
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  const [showAddVehicleModal, setShowAddVehicleModal] = useState(false);

  // Make GET requestion to vehicle.py to retrieve the vehicles
  useEffect(() => {
    fetch('http://localhost:8000/vehicles')
      .then(res => res.json())
      .then(data => setVehicles(data))
      .catch(err => console.error('Failed to fetch vehicles:', err));
  }, []);


  // Sorting function
  const handleSort = field => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Sort vehicles based on current sort field and direction
  const sortedVehicles = [...vehicles].sort((a, b) => {
    if (sortField === 'mileage') {
      // Convert to numbers for proper comparison
      const aNum = parseInt(a[sortField].replace(/,/g, ''));
      const bNum = parseInt(b[sortField].replace(/,/g, ''));
      return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
    } else {
      // Standard string comparison
      if (a[sortField] < b[sortField]) return sortDirection === 'asc' ? -1 : 1;
      if (a[sortField] > b[sortField]) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    }
  });

  // Get current vehicles for pagination
  const indexOfLastVehicle = currentPage * itemsPerPage;
  const indexOfFirstVehicle = indexOfLastVehicle - itemsPerPage;
  const currentVehicles = sortedVehicles.slice(indexOfFirstVehicle, indexOfLastVehicle);
  const totalPages = Math.ceil(vehicles.length / itemsPerPage);

  // Sorting is now handled in the VehicleList component

  // Toggle select all (update to use currentVehicles)
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedVehicles([]);
    } else {
      setSelectedVehicles(currentVehicles.map(vehicle => vehicle.id));
    }
    setSelectAll(!selectAll);
  };

  // Toggle select individual vehicle
  const handleSelectVehicle = vehicleId => {
    if (selectedVehicles.includes(vehicleId)) {
      setSelectedVehicles(selectedVehicles.filter(id => id !== vehicleId));
    } else {
      setSelectedVehicles([...selectedVehicles, vehicleId]);
    }
  };

  // Open vehicle details
  const openVehicleDetails = vehicle => {
    setCurrentVehicle(vehicle);
    setVehicleDetailsOpen(true);
  };

  // Close vehicle details
  const closeVehicleDetails = () => {
    setVehicleDetailsOpen(false);
    setCurrentVehicle(null);
  };

  // Open vehicle assignment modal
  const openAssignmentModal = () => {
    setShowAssignmentModal(true);
  };

  // Close vehicle assignment modal
  const closeAssignmentModal = () => {
    setShowAssignmentModal(false);
  };
  // Analytics are always shown now

  // Bulk operations
  const exportSelectedVehicles = () => {
    const selectedData = vehicles.filter(vehicle => selectedVehicles.includes(vehicle.id));
    // In a real app, this would create a CSV or Excel file
    console.log('Exporting data for:', selectedData);
    alert(`Exporting data for ${selectedData.length} vehicles`);
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
      <h1 className="text-3xl font-bold mb-6">Fleet Vehicles</h1>
      <div className="bg-card rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Manage Vehicles</h2>
          <button
            className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition flex items-center gap-2"
            onClick={() => setShowAddVehicleModal(true)}
          >
            <PlusCircle size={18} />
            <span>Add Vehicle</span>
          </button>
        </div>
        {/* Search and filter bar */}
        <VehicleSearch
          filterOpen={filterOpen}
          setFilterOpen={setFilterOpen}
          onSearch={() => { }}
          onApplyFilters={() => setFilterOpen(false)}
          onResetFilters={() => setFilterOpen(false)}
        />{' '}
        {/* Vehicle actions buttons and bulk actions */}
        <VehicleActions
          selectedVehicles={selectedVehicles}
          openAssignmentModal={openAssignmentModal}
          exportSelectedVehicles={exportSelectedVehicles}
        />{' '}
        {/* Vehicle list with pagination */}
        <VehicleList
          vehicles={currentVehicles}
          selectedVehicles={selectedVehicles}
          handleSelectVehicle={handleSelectVehicle}
          selectAll={selectAll}
          handleSelectAll={handleSelectAll}
          sortField={sortField}
          sortDirection={sortDirection}
          handleSort={handleSort}
          openVehicleDetails={openVehicleDetails}
          currentPage={currentPage}
          totalPages={totalPages}
          itemsPerPage={itemsPerPage}
          changeItemsPerPage={changeItemsPerPage}
          goToNextPage={goToNextPage}
          goToPrevPage={goToPrevPage}
        />
      </div>{' '}
      {/* Vehicle Details Modal */}
      {vehicleDetailsOpen && currentVehicle && (
        <VehicleDetailsModal
          vehicle={currentVehicle}
          closeVehicleDetails={closeVehicleDetails}
          openAssignmentModal={openAssignmentModal}
        />
      )}{' '}
      {/* Driver Assignment Modal */}
      {showAssignmentModal && (
        <DriverAssignmentModal
          closeAssignmentModal={closeAssignmentModal}
          selectedVehicles={selectedVehicles}
          handleSelectVehicle={handleSelectVehicle}
          vehicles={vehicles}
          currentVehicle={currentVehicle}
        />
      )}{' '}
      {/* Add Vehicle Modal */}
      {showAddVehicleModal && (
        <AddVehicleModal
          closeModal={() => setShowAddVehicleModal(false)}
          vehicles={vehicles}
          setVehicles={setVehicles}

        />
      )}{' '}
      {/* Data visualization section */}
      <DataVisualization />
    </div>
  );
};

export default Vehicles;
