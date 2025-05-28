import React, { useState, useEffect, useCallback } from 'react';
import { PlusCircle } from 'lucide-react';
import DriverList from '../components/drivers/DriverList';
import DriverSearch from '../components/drivers/DriverSearch';
import DriverActions from '../components/drivers/DriverActions';
import DriverDetailsModal from '../components/drivers/DriverDetailsModal';
import VehicleAssignmentModal from '../components/drivers/VehicleAssignmentModal';
import DataVisualization from '../components/drivers/DataVisualization';
import { getDrivers, deleteDriver, searchDrivers } from '../backend/API';

const Drivers = () => {
  const [drivers, setDrivers] = useState([]);
  const [filteredDrivers, setFilteredDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
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
  const [filters, setFilters] = useState({
    status: '',
    department: '',
    licenseType: '',
  }); // Helper function to capitalize status
  const capitalizeStatus = useCallback(status => {
    if (!status) return 'Unknown';
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }, []);

  // Transform backend driver data to frontend format
  const transformDriverData = useCallback(
    backendDriver => {
      return {
        id: backendDriver.id,
        name: backendDriver.user_info?.full_name || 'Unknown',
        licenseNumber: backendDriver.license_number,
        phone: backendDriver.user_info?.phoneNo || 'N/A',
        licenseExpiry: backendDriver.license_expiry,
        licenseType: backendDriver.license_type,
        status: capitalizeStatus(backendDriver.status),
        email: backendDriver.user_info?.email || 'N/A',
        emergencyContact: backendDriver.emergency_contact || 'N/A',
        department: backendDriver.department || 'N/A',
        joiningDate: backendDriver.joining_date || 'N/A',
        employeeId: backendDriver.employee_id || 'N/A',
        rating: backendDriver.rating?.toString() || '0.0',
        currentVehicle: null, // TODO: Implement vehicle relationship
        trips: [], // TODO: Implement trip history
        documents: [], // TODO: Implement document management
      };
    },
    [capitalizeStatus]
  );

  // Load drivers from API
  useEffect(() => {
    const loadDrivers = async () => {
      try {
        setLoading(true);
        setError(null);

        const params = {
          limit: 100, // Load more drivers for better testing
        };

        // Apply filters if any
        if (filters.status) {
          params.status_filter = filters.status.toLowerCase().replace(/\s+/g, '_');
        }
        if (filters.department) {
          params.department_filter = filters.department;
        }

        const response = await getDrivers(params);
        const transformedDrivers = response.map(transformDriverData);

        setDrivers(transformedDrivers);
        setFilteredDrivers(transformedDrivers);
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
  }, [filters, transformDriverData]); // Reload when filters change  // Handle search functionality
  const handleSearch = async searchQuery => {
    try {
      setLoading(true);
      setError(null);

      if (!searchQuery.trim()) {
        // If empty search, reload all drivers
        const response = await getDrivers({
          limit: 100,
          ...(filters.status && {
            status_filter: filters.status.toLowerCase().replace(/\s+/g, '_'),
          }),
          ...(filters.department && { department_filter: filters.department }),
        });
        const transformedDrivers = response.map(transformDriverData);
        setFilteredDrivers(transformedDrivers);
      } else {
        // Search drivers
        const searchResults = await searchDrivers(searchQuery);
        const transformedResults = searchResults.map(transformDriverData);
        setFilteredDrivers(transformedResults);
      }

      setCurrentPage(1); // Reset to first page
    } catch (err) {
      console.error('Error searching drivers:', err);
      setError(err.message || 'Failed to search drivers');
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
      department: '',
      licenseType: '',
    });
    setCurrentPage(1); // Reset to first page
  };

  // Handle driver deletion
  const handleDeleteDriver = async driverId => {
    try {
      setLoading(true);
      await deleteDriver(driverId);

      // Remove the deleted driver from local state
      const updatedDrivers = drivers.filter(driver => driver.id !== driverId);
      const updatedFiltered = filteredDrivers.filter(driver => driver.id !== driverId);

      setDrivers(updatedDrivers);
      setFilteredDrivers(updatedFiltered);

      // Remove from selected drivers if selected
      setSelectedDrivers(selectedDrivers.filter(id => id !== driverId));

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

      // Handle different data types
      if (sortField === 'rating') {
        aValue = parseFloat(aValue) || 0;
        bValue = parseFloat(bValue) || 0;
      } else if (sortField === 'licenseExpiry' || sortField === 'joiningDate') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      } else {
        aValue = aValue?.toString().toLowerCase() || '';
        bValue = bValue?.toString().toLowerCase() || '';
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    }
  );

  // Get current drivers for pagination
  const indexOfLastDriver = currentPage * itemsPerPage;
  const indexOfFirstDriver = indexOfLastDriver - itemsPerPage;
  const currentDrivers = sortedDrivers.slice(indexOfFirstDriver, indexOfLastDriver);
  const totalPages = Math.ceil(sortedDrivers.length / itemsPerPage);

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
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Fleet Drivers</h1>

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md mb-6">
          <p>{error}</p>
        </div>
      )}

      <div className="bg-card rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">
            Manage Drivers
            {loading && <span className="text-sm text-muted-foreground ml-2">(Loading...)</span>}
          </h2>
          <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition flex items-center gap-2">
            <PlusCircle size={18} />
            <span>Add Driver</span>
          </button>
        </div>

        {/* Search and filter bar */}
        <DriverSearch
          filterOpen={filterOpen}
          setFilterOpen={setFilterOpen}
          onSearch={handleSearch}
          onApplyFilters={handleApplyFilters}
          onResetFilters={handleResetFilters}
        />

        {/* Driver actions */}
        <DriverActions
          selectedDrivers={selectedDrivers}
          exportSelectedDrivers={exportSelectedDrivers}
          onDeleteSelected={() => {
            if (
              selectedDrivers.length > 0 &&
              window.confirm(`Are you sure you want to delete ${selectedDrivers.length} driver(s)?`)
            ) {
              selectedDrivers.forEach(driverId => handleDeleteDriver(driverId));
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
          /* Driver list with pagination */
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
            totalDrivers={sortedDrivers.length}
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
