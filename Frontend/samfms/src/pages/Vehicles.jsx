import React, { useState, useEffect, useCallback, use } from 'react';
import { Plus } from 'lucide-react';
import VehicleList from '../components/vehicles/VehicleList';
import VehicleSearch from '../components/vehicles/VehicleSearch';
import VehicleActions from '../components/vehicles/VehicleActions';
import VehicleDetailsModal from '../components/vehicles/VehicleDetailsModal';
import DriverAssignmentModal from '../components/vehicles/DriverAssignmentModal';
import DataVisualization from '../components/vehicles/DataVisualization';
import AddVehicleModal from '../components/vehicles/AddVehicleModal';
import EditVehicleModal from '../components/vehicles/EditVehicleModal';
import { getVehicles, deleteVehicle, searchVehicles, getVehicleUsage, getAssignmentMetrics } from '../backend/API';
import FleetUtilizationCard from '../components/analytics/FleetUtilizationCard';
import VehicleUsageStats from '../components/analytics/VehicleUsageStats';
import AssignmentMetricsCard from '../components/analytics/AssignmentMetricsCard';
import MaintenanceAnalyticsCard from '../components/analytics/MaintenanceAnalyticsCard';
import DriverPerformanceCard from '../components/analytics/DriverPerformanceCard';
import CostAnalyticsCard from '../components/analytics/CostAnalyticsCard';
import StatusBreakdownCard from '../components/analytics/StatusBreakdownCard';

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
  const [analytics, setAnalytics] = useState({});
  const [stats, setStats] = useState({});
  const [vehicleAnalytics, setVehicleAnalytics] = useState({});

  const [loadingVehicles, setLoadingVehicles] = useState(true);
  const [loadingVehicleAnalytics, setLoadingVehicleAnalytics] = useState(true);
  const [totalVehicles, setTotalVehicles] = useState({});
  const [totalVehiclesMaint, setTotalVehiclesMaint] = useState({});
  const [fleetUtil, setFleetUtil] = useState({});



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

    const fetchVehicleAnalytics = async () => {
      try {
        setLoadingVehicleAnalytics(true);
        const response = await getVehicleUsage();
        const response2 = await getAssignmentMetrics();
        
        setVehicleAnalytics(
          {
            assignment_metrics: response.data.data.dashboard.fleet_utilization || 0,
          }
         || {});
         console.log(vehicleAnalytics.assignment_metrics);
        
      } catch (error) {
        console.log(`Error fetching data: ${error}`);
      } finally {
        setLoadingVehicleAnalytics(false);
      }
    };
    fetchVehicleAnalytics();

    const fetchTotalVehicles = async () => {
      try {
        setLoadingVehicles(true);
        const response = await getVehicles();
        setTotalVehicles(response.data.data.vehicles.length || 0);

        const maintenanceVehicles = response.data.data.vehicles.filter(vehicle => vehicle.status === 'maintenance');
        setTotalVehiclesMaint(maintenanceVehicles.length);
        console.log(maintenanceVehicles.length);

        const vehicleUtil = (1 - (maintenanceVehicles.length / response.data.data.vehicles.length));
        setFleetUtil(vehicleUtil);

        setStats(
          {
            totalVehicles: response.data.data.vehicles.length || 0,
            totalVehiclesMaint: maintenanceVehicles.length || 0,
            fleetUtil: vehicleUtil || 0,
            statusBreakdown: response.data.data.vehicles.reduce((breakdown, vehicle) => {
              breakdown[vehicle.status] = (breakdown[vehicle.status] || 0) + 1;
              return breakdown;
          })
          }
         || {});
        console.log(stats);
        
      } catch (error) {
        console.log(`Error fetching data: ${error}`);
        setTotalVehicles('N/A');
      } finally {
        setLoadingVehicles(false);
      }
    };
    fetchTotalVehicles();
    fetchVehicleAnalytics();

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
        setAnalytics(response.analytics || {}); // <-- set analytics here
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
          ...(filters.status && { status_filter: filters.status.toLowerCase() }),
          ...(filters.make && { make_filter: filters.make }),
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

  // Callback to refresh vehicles after assignment
  const handleAssignmentComplete = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        limit: 100,
        ...(filters.status && { status_filter: filters.status.toLowerCase() }),
        ...(filters.make && { make_filter: filters.make }),
      };
      const response = await getVehicles(params);
      const vehiclesArray = response.vehicles || response || [];
      const transformedVehicles = vehiclesArray
        .map(transformVehicleData)
        .filter(vehicle => vehicle !== null);
      setVehicles(transformedVehicles);
      setAnalytics(response.analytics || {});
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
        <h1 className="text-3xl font-bold mb-6 animate-in slide-in-from-top-4 duration-500">
          Fleet Vehicles
        </h1>
        <div className="bg-card rounded-lg shadow-md p-6 animate-in slide-in-from-bottom-4 duration-700 delay-150">
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
          />
        )}
        {/* Data visualization section */}
        <div className="animate-in slide-in-from-bottom-8 duration-700 delay-1000">
          <DataVisualization analytics={stats} />
        </div>
        <div className="animate-in fade-in duration-500 delay-1200">
          <VehicleUsageStats stats={analytics.vehicle_usage} />
        </div>
        <div className="animate-in fade-in duration-500 delay-1300">
          <DriverPerformanceCard stats={analytics.driver_performance} />
        </div>
        <div className="animate-in fade-in duration-500 delay-1400">
          <CostAnalyticsCard stats={analytics.cost_analytics} />
        </div>
        {/* Analytics Cards Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 animate-in slide-in-from-bottom-6 duration-700 delay-1500">
          <StatusBreakdownCard stats={analytics.status_breakdown} />
          <FleetUtilizationCard data={analytics.fleet_utilization} />
          <AssignmentMetricsCard data={analytics.assignment_metrics} />
          <MaintenanceAnalyticsCard data={analytics.maintenance_analytics} />
        </div>
      </div>
    </div>
  );
};

export default Vehicles;s
//<FleetUtilizationCard data={analytics.fleet_utilization} />
//<StatusBreakdownCard stats={analytics.status_breakdown} />
//<MaintenanceAnalyticsCard data={analytics.maintenance_analytics} />
//<VehicleUsageStats stats={vehicleAnalytics} />
//<DriverPerformanceCard data={analytics.driver_performance} />
//<CostAnalyticsCard stats={vehicleAnalytics} />
