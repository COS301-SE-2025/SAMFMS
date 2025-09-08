import React, {useState, useEffect, useCallback} from 'react';
import {Plus} from 'lucide-react';
import VehicleList from '../components/vehicles/VehicleList';
import VehicleSearch from '../components/vehicles/VehicleSearch';
import VehicleActions from '../components/vehicles/VehicleActions';
import VehicleDetailsModal from '../components/vehicles/VehicleDetailsModal';
import DriverAssignmentModal from '../components/vehicles/DriverAssignmentModal';
import AddVehicleModal from '../components/vehicles/AddVehicleModal';
import EditVehicleModal from '../components/vehicles/EditVehicleModal';
import Notification from '../components/common/Notification';
import { Car } from 'lucide-react';
import {getVehicles, deleteVehicle, searchVehicles} from '../backend/API';
const Vehicles = () => {
  const [vehicles, setVehicles] = useState([]);
  // Removed unused state variable for filteredVehicles
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVehicles, setSelectedVehicles] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [vehicleDetailsOpen, setVehicleDetailsOpen] = useState(false);
  const [currentVehicle, setCurrentVehicle] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
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

  // Notification state
  const [notification, setNotification] = useState({
    isVisible: false,
    message: '',
    type: 'info',
  });

  // Function to show notifications
  const showNotification = (message, type = 'info') => {
    setNotification({
      isVisible: true,
      message,
      type,
    });
  };

  // Function to close notifications
  const closeNotification = () => {
    setNotification(prev => ({
      ...prev,
      isVisible: false,
    }));
  };

  // Enhanced error handling with retry logic
  const handleAPIError = async (error, retryFn, maxRetries = 3) => {
    if ((error.status === 503 || error.status === 504) && retryFn && maxRetries > 0) {
      console.log(
        `Service unavailable (${error.status}), retrying... (${maxRetries} attempts left)`
      );
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
      return retryFn(maxRetries - 1);
    }
    throw error;
  };

  // Transform backend vehicle data to frontend format
  const transformVehicleData = useCallback(backendVehicle => {
    // Add null safety check
    if (!backendVehicle) return null;

    return {
      id: backendVehicle.id || backendVehicle._id || '',
      make: backendVehicle.make || 'Unknown',
      model: backendVehicle.model || 'Unknown',
      year: backendVehicle.year || 'N/A',
      vin: backendVehicle.vin || 'N/A',
      licensePlate: backendVehicle.license_plate || backendVehicle.licensePlate || 'N/A',
      color: backendVehicle.color || 'N/A',
      fuelType: backendVehicle.fuel_type || backendVehicle.fuelType || 'N/A',
      mileage:
        backendVehicle.mileage?.toString() || backendVehicle.current_mileage?.toString() || '0',
      // Fix status mapping - handle both is_active boolean and status string
      status: backendVehicle.status
        ? backendVehicle.status.charAt(0).toUpperCase() + backendVehicle.status.slice(1)
        : backendVehicle.is_active !== undefined
          ? backendVehicle.is_active
            ? 'Active'
            : 'Inactive'
          : 'Active',
      driver: backendVehicle.driver_name || backendVehicle.driver || 'Unassigned',
      driverId: backendVehicle.driver_id || backendVehicle.driverId || null,
      department: backendVehicle.department || 'N/A',
      lastService: backendVehicle.last_service || backendVehicle.lastService || 'N/A',
      nextService: backendVehicle.next_service || backendVehicle.nextService || 'N/A',
      insuranceExpiry: backendVehicle.insurance_expiry || backendVehicle.insuranceExpiry || 'N/A',
      acquisitionDate: backendVehicle.acquisition_date || backendVehicle.acquisitionDate || 'N/A',
      fuelEfficiency: backendVehicle.fuel_efficiency || backendVehicle.fuelEfficiency || 'N/A',
      tags: backendVehicle.tags || [],
      lastDriver: backendVehicle.last_driver || backendVehicle.lastDriver || 'None',
      maintenanceCosts: backendVehicle.maintenance_costs || backendVehicle.maintenanceCosts || [],
    };
  }, []);

  // Load vehicles from API
  useEffect(() => {
    const loadVehicles = async (retryCount = 3) => {
      try {
        setLoading(true);
        setError(null);
        const params = {
          limit: 100, // Load more vehicles for better testing
        };
        if (filters.status) {
          params.status_filter = filters.status.toLowerCase();
        }
        if (filters.make) {
          params.make_filter = filters.make;
        }
        const response = await getVehicles(params);
        const vehiclesData =
          response.data?.data?.vehicles || response.vehicles || response.data?.vehicles || [];
        const transformedVehicles = vehiclesData
          .map(transformVehicleData)
          .filter(vehicle => vehicle !== null);
        setVehicles(transformedVehicles);
      } catch (err) {
        console.error('Error loading vehicles:', err);

        // Try to retry on service unavailable errors
        try {
          await handleAPIError(err, () => loadVehicles(retryCount - 1), retryCount);
        } catch (finalError) {
          // Enhanced error handling with different error types
          let errorMessage = 'Failed to load vehicles';

          if (finalError.status === 401) {
            errorMessage = 'Session expired. Please log in again.';
          } else if (finalError.status === 403) {
            errorMessage = 'You do not have permission to view vehicles.';
          } else if (finalError.status === 500) {
            errorMessage = 'Server error. Please try again later.';
          } else if (finalError.status === 503) {
            errorMessage = 'Service temporarily unavailable. Please try again in a moment.';
          } else if (finalError.message.includes('fetch')) {
            errorMessage = 'Network error. Please check your connection.';
          } else {
            errorMessage = finalError.message || 'Failed to load vehicles';
          }

          setError(errorMessage);
          setVehicles([]);
        }
      } finally {
        setLoading(false);
      }
    };
    loadVehicles();
  }, [filters, transformVehicleData]);
  // Handle search functionality
  const handleSearch = async (searchQuery, retryCount = 3) => {
    try {
      setLoading(true);
      setError(null);

      if (!searchQuery.trim()) {
        // If empty search, reload all vehicles
        const response = await getVehicles({
          limit: 100,
          ...(filters.status && {status_filter: filters.status.toLowerCase()}),
          ...(filters.make && {make_filter: filters.make}),
        });
        // Handle both array and object response formats with proper nesting
        const vehiclesArray =
          response.data?.data?.vehicles ||
          response.vehicles ||
          response.data?.vehicles ||
          response ||
          [];
        const transformedVehicles = Array.isArray(vehiclesArray)
          ? vehiclesArray.map(transformVehicleData).filter(v => v !== null)
          : [];
        setVehicles(transformedVehicles);
      } else {
        // Search vehicles
        const results = await searchVehicles(searchQuery);
        // Handle both array and object response formats with proper nesting
        const vehiclesArray =
          results.data?.data?.vehicles ||
          results.vehicles ||
          results.data?.vehicles ||
          results ||
          [];
        if (Array.isArray(vehiclesArray) && vehiclesArray.length > 0) {
          const transformedResults = vehiclesArray
            .map(transformVehicleData)
            .filter(v => v !== null);
          setVehicles(transformedResults);
        } else {
          setVehicles([]); // Clear vehicles if no results found
          setError('No vehicles found matching your search criteria.');
          return; // Exit early if no results
        }
      }

      setCurrentPage(1); // Reset to first page
    } catch (err) {
      console.error('Error searching vehicles:', err);

      // Try to retry on service unavailable errors
      try {
        await handleAPIError(err, () => handleSearch(searchQuery, retryCount - 1), retryCount);
      } catch (finalError) {
        // Enhanced error handling for search
        let errorMessage = 'Failed to search vehicles';

        if (finalError.status === 401) {
          errorMessage = 'Session expired. Please log in again.';
        } else if (finalError.status === 403) {
          errorMessage = 'You do not have permission to search vehicles.';
        } else if (finalError.status === 503) {
          errorMessage = 'Search service temporarily unavailable. Please try again.';
        } else if (finalError.message.includes('Network')) {
          errorMessage = 'Network error during search. Please try again.';
        } else {
          errorMessage = finalError.message || 'Failed to search vehicles';
        }

        setError(errorMessage);
      }
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

      // Find the vehicle to check if it has unavailable status
      const vehicle = vehicles.find(v => v.id === vehicleId);
      if (!vehicle) {
        throw new Error('Vehicle not found');
      }

      // Check if vehicle status is unavailable
      if (vehicle.status === 'unavailable') {
        showNotification(
          `Cannot delete ${vehicle.make} ${vehicle.model} because its status is unavailable.`,
          'warning'
        );
        return;
      }

      setLoading(true);
      await deleteVehicle(vehicleId);

      // Remove the deleted vehicle from local state
      const updatedVehicles = vehicles.filter(vehicle => vehicle.id !== vehicleId);
      setVehicles(updatedVehicles);

      // Remove from selected vehicles if selected
      setSelectedVehicles(selectedVehicles.filter(id => id !== vehicleId));

      // Show success message
      showNotification(`Vehicle ${vehicle.make} ${vehicle.model} deleted successfully`, 'success');
    } catch (err) {
      console.error('Error deleting vehicle:', err);
      showNotification(err.message || 'Failed to delete vehicle', 'error');
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
      showNotification(
        `Vehicle "${transformedVehicle.make} ${transformedVehicle.model}" has been updated successfully!`,
        'success'
      );
    } catch (error) {
      console.error('Error processing updated vehicle:', error);
      // Refresh the entire list as fallback
      try {
        const response = await getVehicles({limit: 100});
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

  // Callback to refresh vehicles after assignment
  const handleAssignmentComplete = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        limit: 100,
        ...(filters.status && {status_filter: filters.status.toLowerCase()}),
        ...(filters.make && {make_filter: filters.make}),
      };
      const response = await getVehicles(params);
      const vehiclesArray = response.vehicles || response || [];
      const transformedVehicles = vehiclesArray
        .map(transformVehicleData)
        .filter(vehicle => vehicle !== null);
      setVehicles(transformedVehicles);
    } catch (error) {
      console.error('Error refreshing vehicles after assignment:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, transformVehicleData]);
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
    <div className="min-h-screen bg-background relative">
      {/* SVG pattern background like Landing page */}
      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: 'url("/logo/logo_icon_dark.svg")',
          backgroundSize: '200px',
          backgroundRepeat: 'repeat',
          filter: 'blur(1px)',
        }}
      />
      <div className="relative z-10 container mx-auto px-4 py-8 animate-in fade-in duration-700">
        {/* Vehicle Summary Cards - Top Level */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 animate-in fade-in duration-500 delay-200">
          {/* Total Vehicles Card */}
          <div className="group bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border border-blue-200 dark:border-blue-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-300 mb-2">
                  Total Vehicles
                </p>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100 transition-colors duration-300">
                  {vehicles.length}
                </p>
                <div className="flex items-center mt-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></div>
                  <p className="text-xs text-blue-600 dark:text-blue-400">Fleet size</p>
                </div>
              </div>
              <div className="h-14 w-14 bg-blue-500 dark:bg-blue-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
                <svg
                  className="h-7 w-7 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <Car />
                </svg>
              </div>
            </div>
          </div>

          {/* Available Vehicles Card */}
          <div className="group bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600 dark:text-green-300 mb-2">
                  Available Vehicles
                </p>
                <p className="text-3xl font-bold text-green-900 dark:text-green-100 transition-colors duration-300">
                  {
                    vehicles.filter(
                      vehicle =>
                        vehicle.status?.toLowerCase() === 'active' ||
                        vehicle.status?.toLowerCase() === 'available'
                    ).length
                  }
                </p>
                <div className="flex items-center mt-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  <p className="text-xs text-green-600 dark:text-green-400">Ready to use</p>
                </div>
              </div>
              <div className="h-14 w-14 bg-green-500 dark:bg-green-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
                <svg
                  className="h-7 w-7 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Average Mileage Card */}
          <div className="group bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900 border border-orange-200 dark:border-orange-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600 dark:text-orange-300 mb-2">
                  Average Mileage
                </p>
                <p className="text-3xl font-bold text-orange-900 dark:text-orange-100 transition-colors duration-300">
                  {(() => {
                    const validMileages = vehicles
                      .map(vehicle => parseFloat(vehicle.mileage) || 0)
                      .filter(mileage => mileage > 0);
                    const average =
                      validMileages.length > 0
                        ? validMileages.reduce((sum, mileage) => sum + mileage, 0) /
                        validMileages.length
                        : 0;
                    return Math.round(average).toLocaleString();
                  })()}
                </p>
                <div className="flex items-center mt-2">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mr-2 animate-pulse"></div>
                  <p className="text-xs text-orange-600 dark:text-orange-400">kilometers traveled</p>
                </div>
              </div>
              <div className="h-14 w-14 bg-orange-500 dark:bg-orange-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
                <svg
                  className="h-7 w-7 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6 animate-in slide-in-from-bottom-4 duration-700 delay-150">
          <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4 animate-in fade-in duration-500 delay-300">
            <h2 className="text-xl font-semibold">Manage Vehicles</h2>
            <div className="flex-1 mx-4">
              <VehicleSearch
                onSearch={handleSearch}
                onApplyFilters={handleApplyFilters}
                onResetFilters={handleResetFilters}
              />
            </div>
            <button
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-all duration-200 flex items-center gap-2 shadow-md hover:shadow-lg"
              onClick={() => setShowAddVehicleModal(true)}
              title="Add Vehicle"
            >
              <Plus size={18} />
            </button>
          </div>
          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md mb-6">
              <p>{error}</p>
            </div>
          )}
          {/* Vehicle actions buttons and bulk actions */}
          <div className="animate-in fade-in duration-500 delay-500">
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
          </div>

          {/* Loading State */}
          {loading && vehicles.length === 0 ? (
            <div className="text-center py-8 animate-in fade-in duration-500">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading vehicles...</p>
            </div>
          ) : (
            /* Vehicle list with pagination */
            <div className="animate-in slide-in-from-bottom-6 duration-700 delay-700">
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
            </div>
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
            onAssignmentComplete={handleAssignmentComplete}
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
            showNotification={showNotification}
          />
        )}
        {/* Notification Component */}
        <Notification
          message={notification.message}
          type={notification.type}
          isVisible={notification.isVisible}
          onClose={closeNotification}
        />
      </div>
    </div>
  );
};

export default Vehicles;
