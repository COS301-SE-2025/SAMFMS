import React, { useState, useEffect, useCallback } from 'react';
import DriverList from '../components/drivers/DriverList';
import DriverSearch from '../components/drivers/DriverSearch';
import DriverActions from '../components/drivers/DriverActions';
import DriverDetailsModal from '../components/drivers/DriverDetailsModal';
import VehicleAssignmentModal from '../components/drivers/VehicleAssignmentModal';
import AddDriverModal from '../components/drivers/AddDriverModal';
import EditDriverModal from '../components/drivers/EditDriverModal';

import { deleteDriver, searchDrivers, getTripPlanningDrivers } from '../backend/api/drivers';

const Drivers = () => {
  const [drivers, setDrivers] = useState([]);
  const [filteredDrivers, setFilteredDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDrivers, setSelectedDrivers] = useState([]);
  const [driverDetailsOpen, setDriverDetailsOpen] = useState(false);
  const [currentDriver, setCurrentDriver] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [sortField, setSortField] = useState('employeeId');
  const [sortDirection, setSortDirection] = useState('asc');
  const [showVehicleAssignmentModal, setShowVehicleAssignmentModal] = useState(false);
  const [showAddDriverModal, setShowAddDriverModal] = useState(false);
  const [showEditDriverModal, setShowEditDriverModal] = useState(false);
  const [driverToEdit, setDriverToEdit] = useState(null);
  const [filters] = useState({
    status: '',
    department: '',
    licenseType: '',
  });

  // Transform backend driver data to frontend format
  const transformDriverData = useCallback(backendDriver => {
    return {
      id: backendDriver.id,
      name: `${backendDriver.first_name || ''} ${backendDriver.last_name || ''}`.trim() || 'N/A',
      licenseNumber: backendDriver.license_number || 'N/A',
      phone: backendDriver.phone || 'N/A', // Changed from phoneNo to phone
      licenseExpiry: backendDriver.license_expiry || 'N/A',
      email: backendDriver.email || 'N/A',
      status:
        backendDriver.status === 'active'
          ? 'Active'
          : backendDriver.status === 'unavailable'
          ? 'Unavailable'
          : backendDriver.status === 'inactive'
          ? 'Inactive'
          : (backendDriver.status || 'Unknown').charAt(0).toUpperCase() +
            (backendDriver.status || 'unknown').slice(1),
      employeeId: backendDriver.employee_id || 'N/A',
      department: backendDriver.department || 'N/A',
      licenseType: backendDriver.license_class || 'N/A',
      last_login: backendDriver.last_login,
      role: backendDriver.role,
    };
  }, []);

  // Load drivers from API
  useEffect(() => {
    const loadDrivers = async () => {
      try {
        setLoading(true);
        setError(null);
        const params = { limit: 100 };
        if (filters.status) {
          // Map frontend status format to backend format
          params.status = filters.status.toLowerCase() === 'active' ? 'active' : 'inactive';
        }
        if (filters.department) {
          params.department = filters.department;
        }

        // Use the new trip planning service endpoint
        const response = await getTripPlanningDrivers(params);
        console.log('Full response from trip planning service:', response); // Debug log

        // The trip planning service returns { drivers, total, skip, limit, has_more }
        const driversData = response?.drivers || [];
        console.log('Drivers data array:', driversData); // Debug log

        if (!Array.isArray(driversData)) {
          throw new Error('Invalid response format: drivers data is not an array');
        }

        const transformedDrivers = driversData.map((driver, index) => {
          console.log(`Transforming driver ${index}:`, driver); // Debug log
          const transformed = transformDriverData(driver);
          console.log(`Transformed result ${index}:`, transformed); // Debug log
          return transformed;
        });
        console.log('All transformed drivers:', transformedDrivers); // Debug log
        setDrivers(transformedDrivers);
        setFilteredDrivers([]); // Always reset filteredDrivers on load
      } catch (err) {
        console.error('Error loading drivers:', err);
        setError(err.message || 'Failed to load drivers');
        setDrivers([]);
        setFilteredDrivers([]);
      } finally {
        setLoading(false);
      }
    };
    loadDrivers();
  }, [filters, transformDriverData]);

  // Reload when filters change  // Handle search functionality
  const handleSearch = async searchQuery => {
    try {
      setLoading(true);
      setError(null);
      if (!searchQuery.trim()) {
        // Use trip planning service for getting all drivers when search is empty
        const response = await getTripPlanningDrivers({
          limit: 100,
          ...(filters.status && {
            status: filters.status.toLowerCase() === 'active' ? 'active' : 'inactive',
          }),
          ...(filters.department && { department: filters.department }),
        });

        // The trip planning service returns { drivers, total, skip, limit, has_more }
        const driversData = response?.drivers || [];
        const transformedDrivers = driversData.map(transformDriverData);
        setFilteredDrivers(transformedDrivers);
      } else {
        // For search, we still use the existing search function
        // TODO: Consider implementing search in trip planning service as well
        const searchResults = await searchDrivers(searchQuery);
        // Handle search results - adjust based on your search API response format
        const resultsData =
          searchResults?.data?.data?.drivers || searchResults?.drivers || searchResults || [];
        const transformedResults = resultsData.map(transformDriverData);
        setFilteredDrivers(transformedResults);
      }
      setCurrentPage(1);
    } catch (err) {
      console.error('Error searching drivers:', err);
      setError(err.message || 'Failed to search drivers');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDriver = async employeeId => {
    try {
      // Validate that we have a valid employee ID before proceeding
      if (!employeeId) {
        throw new Error('Invalid driver employee ID: Employee ID is undefined');
      }

      setLoading(true);
      await deleteDriver(employeeId);

      // Remove the deleted driver from local state
      const updatedDrivers = drivers.filter(driver => driver.employeeId !== employeeId);
      const updatedFiltered = filteredDrivers.filter(driver => driver.employeeId !== employeeId);

      setDrivers(updatedDrivers);
      setFilteredDrivers(updatedFiltered);

      // Remove from selected drivers if selected
      setSelectedDrivers(selectedDrivers.filter(id => id !== employeeId));

      // Show success message (you might want to add a toast notification here)
      console.log('Driver deleted successfully');
    } catch (err) {
      console.error('Error deleting driver:', err);
      setError(err.message || 'Failed to delete driver');
    } finally {
      setLoading(false);
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

  // Sort drivers based on current sort field and direction
  const sortedDrivers = [...(filteredDrivers.length > 0 ? filteredDrivers : drivers)].sort(
    (a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];
      aValue = aValue?.toString().toLowerCase() || '';
      bValue = bValue?.toString().toLowerCase() || '';
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    }
  );

  // Get current drivers for pagination
  const indexOfLastDriver = currentPage * itemsPerPage;
  const indexOfFirstDriver = indexOfLastDriver - itemsPerPage;
  const currentDrivers = sortedDrivers.slice(indexOfFirstDriver, indexOfLastDriver);
  const totalPages = Math.ceil(sortedDrivers.length / itemsPerPage); // Toggle select all

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
  // Handle driver added callback
  const handleDriverAdded = async newDriver => {
    try {
      // Transform the new driver data and add to the list
      const transformedDriver = transformDriverData(newDriver);
      setDrivers(prevDrivers => [...prevDrivers, transformedDriver]);
      setFilteredDrivers(prevFiltered => [...prevFiltered, transformedDriver]);

      // Show success message (you can replace this with a proper toast notification)
      alert(`Driver "${transformedDriver.name}" has been added successfully!`);
    } catch (error) {
      console.error('Error processing new driver:', error);
      // Refresh the entire list as fallback
      try {
        const response = await getTripPlanningDrivers({ limit: 100 });
        const driversData = response?.drivers || [];
        const transformedDrivers = driversData.map(transformDriverData);
        setDrivers(transformedDrivers);
        setFilteredDrivers([]);
      } catch (refreshError) {
        console.error('Error refreshing drivers list:', refreshError);
        setError('Driver added but failed to refresh list. Please refresh the page.');
      }
    }
  };

  // Handle edit driver
  const handleEditDriver = driver => {
    setDriverToEdit(driver);
    setShowEditDriverModal(true);
  };

  // Close edit driver modal
  const closeEditDriverModal = () => {
    setShowEditDriverModal(false);
    setDriverToEdit(null);
  };
  // Handle driver updated callback
  const handleDriverUpdated = async updatedDriver => {
    try {
      // Transform the updated driver data
      const transformedDriver = transformDriverData(updatedDriver);

      // Update the driver in both arrays using employee ID instead of MongoDB ID
      setDrivers(prevDrivers =>
        prevDrivers.map(driver =>
          driver.employeeId === transformedDriver.employeeId ? transformedDriver : driver
        )
      );
      setFilteredDrivers(prevFiltered =>
        prevFiltered.map(driver =>
          driver.employeeId === transformedDriver.employeeId ? transformedDriver : driver
        )
      );

      // Show success message
      alert(`Driver "${transformedDriver.name}" has been updated successfully!`);
    } catch (error) {
      console.error('Error processing updated driver:', error);
      // Refresh the entire list as fallback
      try {
        const response = await getTripPlanningDrivers({ limit: 100 });
        const driversData = response?.drivers || [];
        const transformedDrivers = driversData.map(transformDriverData);
        setDrivers(transformedDrivers);
        setFilteredDrivers([]);
      } catch (refreshError) {
        console.error('Error refreshing drivers list:', refreshError);
        setError('Driver updated but failed to refresh list. Please refresh the page.');
      }
    }
  };

  // Export selected drivers
  const exportSelectedDrivers = () => {
    const selectedData = sortedDrivers.filter(driver => selectedDrivers.includes(driver.id));
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
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Driver Summary Cards - Top Level */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 animate-in fade-in duration-500 delay-200">
          {/* Total Drivers Card */}
          <div className="group bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 border border-blue-200 dark:border-blue-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-300 mb-2">
                  Total Drivers
                </p>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100 transition-colors duration-300">
                  {drivers.length}
                </p>
                <div className="flex items-center mt-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></div>
                  <p className="text-xs text-blue-600 dark:text-blue-400">Team members</p>
                </div>
              </div>
              <div className="h-14 w-14 bg-blue-500 dark:bg-blue-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
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
                    d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Active Drivers Card */}
          <div className="group bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border border-green-200 dark:border-green-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600 dark:text-green-300 mb-2">
                  Active Drivers
                </p>
                <p className="text-3xl font-bold text-green-900 dark:text-green-100 transition-colors duration-300">
                  {drivers.filter(driver => driver.status?.toLowerCase() === 'available').length}
                </p>
                <div className="flex items-center mt-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  <p className="text-xs text-green-600 dark:text-green-400">Available for duty</p>
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
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Departments Count Card */}
          <div className="group bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 border border-purple-200 dark:border-purple-800 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600 dark:text-purple-300 mb-2">
                  Departments
                </p>
                <p className="text-3xl font-bold text-purple-900 dark:text-purple-100 transition-colors duration-300">
                  {(() => {
                    const uniqueDepartments = new Set(
                      drivers
                        .map(driver => driver.department)
                        .filter(dept => dept && dept !== 'N/A')
                    );
                    return uniqueDepartments.size;
                  })()}
                </p>
                <div className="flex items-center mt-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mr-2 animate-pulse"></div>
                  <p className="text-xs text-purple-600 dark:text-purple-400">unique divisions</p>
                </div>
              </div>
              <div className="h-14 w-14 bg-purple-500 dark:bg-purple-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300">
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
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg p-6">
          <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
            <h2 className="text-xl font-semibold">Manage Drivers</h2>
            <div className="flex-1 flex justify-end">
              <DriverSearch onSearch={handleSearch} />
            </div>
          </div>
          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md mb-6">
              <p>{error}</p>
            </div>
          )}
          {/* Driver actions buttons and bulk actions */}
          <DriverActions
            selectedDrivers={selectedDrivers}
            exportSelectedDrivers={exportSelectedDrivers}
            onDeleteSelected={() => {
              // Filter out any undefined employee IDs
              const validEmployeeIds = selectedDrivers.filter(id => id);

              if (
                validEmployeeIds.length > 0 &&
                window.confirm(
                  `Are you sure you want to delete ${validEmployeeIds.length} driver(s)?`
                )
              ) {
                validEmployeeIds.forEach(employeeId => handleDeleteDriver(employeeId));
              }
            }}
          />
          {/* Loading State */}
          {loading && drivers.length === 0 ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading drivers...</p>
            </div>
          ) : (
            /* Driver list with pagination */ <DriverList
              drivers={currentDrivers}
              sortField={sortField}
              sortDirection={sortDirection}
              handleSort={handleSort}
              openDriverDetails={openDriverDetails}
              onEditDriver={handleEditDriver}
              currentPage={currentPage}
              totalPages={totalPages}
              itemsPerPage={itemsPerPage}
              changeItemsPerPage={changeItemsPerPage}
              goToNextPage={goToNextPage}
              goToPrevPage={goToPrevPage}
            />
          )}
        </div>
        {/* Driver Details Modal */}
        {driverDetailsOpen && currentDriver && (
          <DriverDetailsModal
            driver={currentDriver}
            closeDriverDetails={closeDriverDetails}
            openVehicleAssignmentModal={openVehicleAssignmentModal}
          />
        )}{' '}
        {/* Vehicle Assignment Modal */}
        {showVehicleAssignmentModal && (
          <VehicleAssignmentModal
            closeVehicleAssignmentModal={closeVehicleAssignmentModal}
            selectedDrivers={selectedDrivers}
            currentDriver={currentDriver}
          />
        )}{' '}
        {/* Add Driver Modal */}
        {showAddDriverModal && (
          <AddDriverModal
            closeModal={() => setShowAddDriverModal(false)}
            onDriverAdded={handleDriverAdded}
          />
        )}
        {/* Edit Driver Modal */}
        {showEditDriverModal && driverToEdit && (
          <EditDriverModal
            driver={driverToEdit}
            closeModal={closeEditDriverModal}
            onDriverUpdated={handleDriverUpdated}
          />
        )}
      </div>
    </div>
  );
};

export default Drivers;
