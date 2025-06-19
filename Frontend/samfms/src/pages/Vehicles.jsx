import React, { useState, useEffect, useCallback } from 'react';
import { PlusCircle } from 'lucide-react';
import VehicleList from '../components/vehicles/VehicleList';
import VehicleSearch from '../components/vehicles/VehicleSearch';
import VehicleActions from '../components/vehicles/VehicleActions';
import VehicleDetailsModal from '../components/vehicles/VehicleDetailsModal';
import DriverAssignmentModal from '../components/vehicles/DriverAssignmentModal';
import DataVisualization from '../components/vehicles/DataVisualization';
import AddVehicleModal from '../components/vehicles/AddVehicleModal';
import EditVehicleModal from '../components/vehicles/EditVehicleModal';
import { getVehicles, deleteVehicle, searchVehicles } from '../backend/API';

const Vehicles = () => {
  const [vehicles, setVehicles] = useState([]);
  // Removed unused state variable for filteredVehicles
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
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
  const [showEditVehicleModal, setShowEditVehicleModal] = useState(false);
  const [vehicleToEdit, setVehicleToEdit] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    make: '',
  });

  // Transform backend vehicle data to frontend format
  const transformVehicleData = useCallback(backendVehicle => {
    return {
      id: backendVehicle.id || backendVehicle._id,
      make: backendVehicle.make || 'Unknown',
      model: backendVehicle.model || 'Unknown',
      year: backendVehicle.year || 'N/A',
      vin: backendVehicle.vin || 'N/A',
      licensePlate: backendVehicle.license_plate || 'N/A',
      color: backendVehicle.color || 'N/A',
      fuelType: backendVehicle.fuel_type || 'N/A',
      mileage: backendVehicle.mileage?.toString() || '0',
      status:
        backendVehicle.status?.charAt(0).toUpperCase() + backendVehicle.status?.slice(1) ||
        'Active',
      driver: backendVehicle.driver_name || 'Unassigned',
      driverId: backendVehicle.driver_id || null,
      department: backendVehicle.department || 'N/A',
      lastService: backendVehicle.last_service || 'N/A',
      nextService: backendVehicle.next_service || 'N/A',
      insuranceExpiry: backendVehicle.insurance_expiry || 'N/A',
      acquisitionDate: backendVehicle.acquisition_date || 'N/A',
      fuelEfficiency: backendVehicle.fuel_efficiency || 'N/A',
      tags: backendVehicle.tags || [],
      lastDriver: backendVehicle.last_driver || 'None',
      maintenanceCosts: backendVehicle.maintenance_costs || [],
    };
  }, []);

  // Load vehicles from API
  useEffect(() => {
    const loadVehicles = async () => {
      try {
        setLoading(true);
        setError(null);

        const params = {
          limit: 100, // Load more vehicles for better testing
        };

        // Apply filters if any
        if (filters.status) {
          params.status_filter = filters.status.toLowerCase();
        }
        if (filters.make) {
          params.make_filter = filters.make;
        }

        const response = await getVehicles(params);
        const transformedVehicles = response.map(transformVehicleData);
        setVehicles(transformedVehicles);
      } catch (err) {
        console.error('Error loading vehicles:', err);

        // Enhanced error handling with different error types
        let errorMessage = 'Failed to load vehicles';

        if (err.status === 401) {
          errorMessage = 'Session expired. Please log in again.';
        } else if (err.status === 403) {
          errorMessage = 'You do not have permission to view vehicles.';
        } else if (err.status === 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (err.message.includes('fetch')) {
          errorMessage = 'Network error. Please check your connection.';
        } else {
          errorMessage = err.message || 'Failed to load vehicles';
        }

        setError(errorMessage);
        setVehicles([]);
      } finally {
        setLoading(false);
      }
    };
    loadVehicles();
  }, [filters, transformVehicleData]);
  // Handle search functionality
  const handleSearch = async searchQuery => {
    try {
      setLoading(true);
      setError(null);

      if (!searchQuery.trim()) {
        // If empty search, reload all vehicles
        const response = await getVehicles({
          limit: 100,
          ...(filters.status && { status_filter: filters.status.toLowerCase() }),
          ...(filters.make && { make_filter: filters.make }),
        });
        const transformedVehicles = response.map(transformVehicleData);
        setVehicles(transformedVehicles);
      } else {
        // Search vehicles
        const results = await searchVehicles(searchQuery);
        const transformedResults = results.map(transformVehicleData);
        setVehicles(transformedResults);
      }

      setCurrentPage(1); // Reset to first page
    } catch (err) {
      console.error('Error searching vehicles:', err);

      // Enhanced error handling for search
      let errorMessage = 'Failed to search vehicles';

      if (err.status === 401) {
        errorMessage = 'Session expired. Please log in again.';
      } else if (err.status === 403) {
        errorMessage = 'You do not have permission to search vehicles.';
      } else if (err.message.includes('Network')) {
        errorMessage = 'Network error during search. Please try again.';
      } else {
        errorMessage = err.message || 'Failed to search vehicles';
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle filter changes
  const handleApplyFilters = async newFilters => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page
  };

  // Handle filter reset
  const handleResetFilters = () => {
    setFilters({
      status: '',
      make: '',
    });
    setCurrentPage(1); // Reset to first page
  };

  // Handle vehicle deletion
  const handleDeleteVehicle = async vehicleId => {
    try {
      // Validate that we have a valid vehicle ID before proceeding
      if (!vehicleId) {
        throw new Error('Invalid vehicle ID: ID is undefined');
      }

      setLoading(true);
      await deleteVehicle(vehicleId);

      // Remove the deleted vehicle from local state
      const updatedVehicles = vehicles.filter(vehicle => vehicle.id !== vehicleId);
      setVehicles(updatedVehicles);

      // Remove from selected vehicles if selected
      setSelectedVehicles(selectedVehicles.filter(id => id !== vehicleId));

      // Show success message
      console.log('Vehicle deleted successfully');
    } catch (err) {
      console.error('Error deleting vehicle:', err);
      setError(err.message || 'Failed to delete vehicle');
    } finally {
      setLoading(false);
    }
  };

  // Handle edit vehicle
  const handleEditVehicle = vehicle => {
    setVehicleToEdit(vehicle);
    setShowEditVehicleModal(true);
  };

  // Close edit vehicle modal
  const closeEditVehicleModal = () => {
    setShowEditVehicleModal(false);
    setVehicleToEdit(null);
  };

  // Handle vehicle updated callback
  const handleVehicleUpdated = async updatedVehicle => {
    try {
      // Transform the updated vehicle data
      const transformedVehicle = transformVehicleData(updatedVehicle);

      // Update the vehicle in the array
      setVehicles(prevVehicles =>
        prevVehicles.map(vehicle =>
          vehicle.id === transformedVehicle.id ? transformedVehicle : vehicle
        )
      );

      // Show success message
      alert(
        `Vehicle "${transformedVehicle.make} ${transformedVehicle.model}" has been updated successfully!`
      );
    } catch (error) {
      console.error('Error processing updated vehicle:', error);
      // Refresh the entire list as fallback
      try {
        const response = await getVehicles({ limit: 100 });
        const transformedVehicles = response.map(transformVehicleData);
        setVehicles(transformedVehicles);
      } catch (refreshError) {
        console.error('Error refreshing vehicles list:', refreshError);
        setError('Vehicle updated but failed to refresh list. Please refresh the page.');
      }
    }
  };

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
    if (sortField === 'mileage' || sortField === 'year') {
      // Convert to numbers for proper comparison
      const aNum = parseInt(a[sortField].toString().replace(/,/g, '')) || 0;
      const bNum = parseInt(b[sortField].toString().replace(/,/g, '')) || 0;
      return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
    } else {
      // Standard string comparison
      const aValue = a[sortField]?.toString()?.toLowerCase() || '';
      const bValue = b[sortField]?.toString()?.toLowerCase() || '';
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
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
      setSelectAll(false);
    } else {
      setSelectedVehicles(currentVehicles.map(vehicle => vehicle.id));
      setSelectAll(true);
    }
  };

  // Toggle select individual vehicle
  const handleSelectVehicle = vehicleId => {
    setSelectedVehicles(prev => {
      if (prev.includes(vehicleId)) {
        const newSelected = prev.filter(id => id !== vehicleId);
        // Update selectAll state based on whether all current vehicles are selected
        setSelectAll(
          newSelected.length > 0 &&
            currentVehicles.every(vehicle => newSelected.includes(vehicle.id))
        );
        return newSelected;
      } else {
        const newSelected = [...prev, vehicleId];
        // Update selectAll state based on whether all current vehicles are selected
        setSelectAll(currentVehicles.every(vehicle => newSelected.includes(vehicle.id)));
        return newSelected;
      }
    });
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
        </div>{' '}
        {/* Error Message */}
        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md mb-6">
            <p>{error}</p>
          </div>
        )}
        {/* Search and filter bar */}{' '}
        <VehicleSearch
          filterOpen={filterOpen}
          setFilterOpen={setFilterOpen}
          onSearch={handleSearch}
          onApplyFilters={handleApplyFilters}
          onResetFilters={handleResetFilters}
        />
        {/* Vehicle actions buttons and bulk actions */}{' '}
        <VehicleActions
          selectedVehicles={selectedVehicles}
          openAssignmentModal={openAssignmentModal}
          exportSelectedVehicles={exportSelectedVehicles}
          onDeleteSelected={() => {
            if (
              selectedVehicles.length > 0 &&
              window.confirm(
                `Are you sure you want to delete ${selectedVehicles.length} vehicle(s)?`
              )
            ) {
              selectedVehicles.forEach(vehicleId => handleDeleteVehicle(vehicleId));
            }
          }}
        />
        {/* Loading State */}
        {loading && vehicles.length === 0 ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading vehicles...</p>
          </div>
        ) : (
          /* Vehicle list with pagination */
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
            onEditVehicle={handleEditVehicle}
            onDeleteVehicle={handleDeleteVehicle}
            currentPage={currentPage}
            totalPages={totalPages}
            itemsPerPage={itemsPerPage}
            changeItemsPerPage={changeItemsPerPage}
            goToNextPage={goToNextPage}
            goToPrevPage={goToPrevPage}
            totalVehicles={sortedVehicles.length}
          />
        )}
      </div>
      {/* Vehicle Details Modal */}
      {vehicleDetailsOpen && currentVehicle && (
        <VehicleDetailsModal
          vehicle={currentVehicle}
          closeVehicleDetails={closeVehicleDetails}
          openAssignmentModal={openAssignmentModal}
          onEditVehicle={handleEditVehicle}
          onDeleteVehicle={handleDeleteVehicle}
        />
      )}
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
      )}
      {/* Edit Vehicle Modal */}
      {showEditVehicleModal && vehicleToEdit && (
        <EditVehicleModal
          vehicle={vehicleToEdit}
          closeModal={closeEditVehicleModal}
          onVehicleUpdated={handleVehicleUpdated}
        />
      )}
      {/* Data visualization section */}
      <DataVisualization />
    </div>
  );
};

export default Vehicles;
